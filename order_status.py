from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging
import re

# Определение состояний для проверки статуса заказа
class OrderStatusState(StatesGroup):
    waiting_for_order_number = State()

# Обработчик кнопки "Статус заказа"
async def check_order_status(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        
        # Отправляем сообщение с инструкцией
        await callback.message.answer(
            "📦 Проверка статуса заказа\n\n"
            "Выберите действие:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📝 Ввести номер заказа", callback_data="enter_order_number")],
                [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
            ])
        )
    except Exception as e:
        logging.error(f"Error in check_order_status: {e}")
        try:
            await callback.message.answer(
                "Произошла ошибка. Пожалуйста, попробуйте снова или обратитесь в поддержку.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
                ])
            )
        except Exception as ex:
            logging.error(f"Failed to send error message in check_order_status: {ex}")

# Обработчик кнопки "Ввести номер заказа"
async def enter_order_number(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        
        # Устанавливаем состояние ожидания номера заказа
        await state.set_state(OrderStatusState.waiting_for_order_number)
        
        # Отправляем сообщение с инструкцией
        await callback.message.answer(
            "Пожалуйста, введите номер вашего заказа в формате GA-XXXXXX:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Отмена", callback_data="back_to_main")]
            ])
        )
    except Exception as e:
        logging.error(f"Error in enter_order_number: {e}")
        try:
            await callback.message.answer(
                "Произошла ошибка. Пожалуйста, попробуйте снова или обратитесь в поддержку.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
                ])
            )
        except Exception as ex:
            logging.error(f"Failed to send error message in enter_order_number: {ex}")

# Обработчик ввода номера заказа
async def handle_order_number(message: types.Message, state: FSMContext):
    # Шаблон для проверки формата номера заказа
    order_pattern = r"^GA-\d{6}$"
    
    try:
        if re.match(order_pattern, message.text.strip()):
            # Получаем номер заказа
            order_number = message.text.strip()
            
            # Сбрасываем состояние
            await state.clear()
            
            # Отправляем информацию о статусе заказа
            # В реальном приложении здесь бы был запрос к API для получения статуса
            await message.answer(
                f"📦 Информация о заказе {order_number}:\n\n"
                f"Статус: ✅ Заказ оформлен\n"
                f"Дата оформления: 25.12.2023\n"
                f"Ожидаемая дата доставки: 05.01.2024\n"
                f"Способ доставки: Курьер\n\n"
                f"Для более подробной информации посетите сайт: https://goldapple.ru/profile/orders",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
                ])
            )
        else:
            # Сообщаем о неверном формате
            await message.answer(
                "❌ Неверный формат номера заказа.\n\nПожалуйста, введите номер заказа в формате GA-XXXXXX "
                "(GA- в верхнем регистре, затем 6 цифр).",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="enter_order_number")],
                    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
                ])
            )
    except Exception as e:
        logging.error(f"Error in handle_order_number: {e}")
        try:
            await message.answer(
                "Произошла ошибка при обработке номера заказа. Пожалуйста, попробуйте снова или обратитесь в поддержку.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
                ])
            )
        except Exception as ex:
            logging.error(f"Failed to send error message in handle_order_number: {ex}")

# Функция для регистрации обработчиков в диспетчере
def register_handlers(dp):
    dp.callback_query(lambda c: c.data == "order_status")(check_order_status)
    dp.callback_query(lambda c: c.data == "enter_order_number")(enter_order_number)
    dp.message(OrderStatusState.waiting_for_order_number)(handle_order_number) 