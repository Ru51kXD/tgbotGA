from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging
import re

# Определение состояний для отмены заказа
class OrderState(StatesGroup):
    waiting_for_order_number = State()
    waiting_for_cancel_confirm = State()

# Основной обработчик кнопки "Отменить заказ"
async def order_cancellation_handler(callback: types.CallbackQuery):
    print(f"DEBUG: Received order_cancellation callback from user {callback.from_user.id}")
    
    try:
        # Обязательно отвечаем на callback
        await callback.answer("Открываю меню отмены заказа")
        
        # Создаем клавиатуру для отмены заказа
        cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Всё-таки отменить", callback_data="proceed_with_cancel")],
            [InlineKeyboardButton(text="❤️ Я передумал(а)", callback_data="changed_mind_cancel")],
            [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
        ])
        
        # Отправляем сообщение с вопросом
        await callback.message.answer(
            "❌ Отмена заказа\n\nВы действительно хотите отменить заказ?",
            reply_markup=cancel_kb
        )
        
    except Exception as e:
        logging.error(f"Error in order_cancellation_handler: {e}")
        try:
            await callback.message.answer(
                "Произошла ошибка при открытии меню отмены заказа. Пожалуйста, попробуйте снова или обратитесь в поддержку.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
                ])
            )
        except Exception as ex:
            logging.error(f"Failed to send error message in order_cancellation_handler: {ex}")

# Обработчик кнопки "Всё-таки отменить"
async def proceed_with_cancel(callback: types.CallbackQuery, state: FSMContext):
    try:
        # Отвечаем на callback
        await callback.answer()
        
        # Устанавливаем состояние ожидания номера заказа
        await state.set_state(OrderState.waiting_for_order_number)
        
        # Отправляем сообщение с инструкцией
        await callback.message.answer(
            "Для отмены заказа, пожалуйста, введите номер заказа в формате GA-XXXXXX:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Вернуться назад", callback_data="back_to_main")]
            ])
        )
    except Exception as e:
        logging.error(f"Error in proceed_with_cancel: {e}")
        try:
            await callback.message.answer(
                "Произошла ошибка. Пожалуйста, попробуйте снова или обратитесь в поддержку.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
                ])
            )
        except Exception as ex:
            logging.error(f"Failed to send error message in proceed_with_cancel: {ex}")

# Обработчик ввода номера заказа
async def handle_order_cancel(message: types.Message, state: FSMContext):
    # Шаблон для проверки формата номера заказа
    order_pattern = r"^GA-\d{6}$"
    
    try:
        if re.match(order_pattern, message.text.strip()):
            # Сохраняем номер заказа в состоянии
            await state.update_data(order_number=message.text.strip())
            
            # Переходим к состоянию подтверждения отмены
            await state.set_state(OrderState.waiting_for_cancel_confirm)
            
            # Отправляем сообщение с запросом подтверждения
            await message.answer(
                f"Вы собираетесь отменить заказ {message.text.strip()}.\n\nПодтвердите отмену:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Да, отменить заказ", callback_data="confirm_cancel")],
                    [InlineKeyboardButton(text="❌ Нет, не отменять", callback_data="decline_cancel")],
                    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
                ])
            )
        else:
            # Сообщаем о неверном формате
            await message.answer(
                "❌ Неверный формат номера заказа.\n\nПожалуйста, введите номер заказа в формате GA-XXXXXX "
                "(GA- в верхнем регистре, затем 6 цифр).",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="proceed_with_cancel")],
                    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
                ])
            )
    except Exception as e:
        logging.error(f"Error in handle_order_cancel: {e}")
        try:
            await message.answer(
                "Произошла ошибка при обработке номера заказа. Пожалуйста, попробуйте снова или обратитесь в поддержку.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
                ])
            )
        except Exception as ex:
            logging.error(f"Failed to send error message in handle_order_cancel: {ex}")

# Обработчик подтверждения отмены
async def confirm_cancel_order(callback: types.CallbackQuery, state: FSMContext):
    try:
        # Отвечаем на callback
        await callback.answer()
        
        # Получаем номер заказа из состояния
        user_data = await state.get_data()
        order_number = user_data.get('order_number')
        
        # Сбрасываем состояние
        await state.clear()
        
        # Отправляем сообщение об успешной отмене
        await callback.message.answer(
            f"✅ Заказ {order_number} успешно отменен.\n\n"
            "Подтверждение об отмене будет отправлено на вашу электронную почту в течение 30 минут.\n\n"
            "Если у вас есть вопросы, обратитесь в службу поддержки.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
            ])
        )
    except Exception as e:
        logging.error(f"Error in confirm_cancel_order: {e}")
        try:
            await callback.message.answer(
                "Произошла ошибка при отмене заказа. Пожалуйста, обратитесь в службу поддержки для отмены заказа.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
                ])
            )
        except Exception as ex:
            logging.error(f"Failed to send error message in confirm_cancel_order: {ex}")

# Обработчик отклонения отмены
async def decline_cancel(callback: types.CallbackQuery, state: FSMContext):
    try:
        # Отвечаем на callback
        await callback.answer()
        
        # Сбрасываем состояние
        await state.clear()
        
        # Отправляем сообщение о сохранении заказа
        await callback.message.answer(
            "❤️ Спасибо, что решили сохранить заказ! Мы ценим ваш выбор.\n\n"
            "Если у вас есть вопросы по заказу, обратитесь в нашу службу поддержки.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
            ])
        )
    except Exception as e:
        logging.error(f"Error in decline_cancel: {e}")
        handle_error(callback)

# Обработчик кнопки "Я передумал(а)"
async def changed_mind_cancel(callback: types.CallbackQuery):
    try:
        # Отвечаем на callback
        await callback.answer()
        
        # Отправляем сообщение с благодарностью
        await callback.message.answer(
            "❤️ Спасибо, что остаетесь с нами!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
            ])
        )
    except Exception as e:
        logging.error(f"Error in changed_mind_cancel: {e}")
        try:
            await callback.message.answer(
                "Произошла ошибка. Пожалуйста, попробуйте снова или обратитесь в поддержку.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
                ])
            )
        except Exception as ex:
            logging.error(f"Failed to send error message in changed_mind_cancel: {ex}")

# Вспомогательная функция для обработки ошибок
async def handle_error(callback):
    try:
        await callback.message.answer(
            "Произошла ошибка. Пожалуйста, попробуйте снова или обратитесь в поддержку.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
            ])
        )
    except Exception as ex:
        logging.error(f"Failed to send error message: {ex}")

# Функция для регистрации обработчиков в диспетчере
def register_handlers(dp):
    dp.callback_query(lambda c: c.data == "order_cancellation")(order_cancellation_handler)
    dp.callback_query(lambda c: c.data == "proceed_with_cancel")(proceed_with_cancel)
    dp.message(OrderState.waiting_for_order_number)(handle_order_cancel)
    dp.callback_query(lambda c: c.data == "confirm_cancel")(confirm_cancel_order)
    dp.callback_query(lambda c: c.data == "decline_cancel")(decline_cancel)
    dp.callback_query(lambda c: c.data == "changed_mind_cancel")(changed_mind_cancel) 