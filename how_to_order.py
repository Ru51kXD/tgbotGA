from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging

# Обработчик кнопки "Как оформить заказ"
async def how_to_order(callback: types.CallbackQuery):
    try:
        await callback.answer()
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❓ Проблемы с оплатой", callback_data="payment_issue")],
            [InlineKeyboardButton(text="❓ Проблемы с адресом доставки", callback_data="address_issue")],
            [InlineKeyboardButton(text="❓ Проблемы с корзиной", callback_data="cart_issue")],
            [InlineKeyboardButton(text="❓ Самовывоз", callback_data="pickup_issue")],
            [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
        ])
        
        await callback.message.answer(
            "🛒 Как оформить заказ:\n\n"
            "1. Зайдите на сайт goldapple.ru\n"
            "2. Добавьте нужные товары в корзину\n"
            "3. Нажмите 'Оформить заказ'\n"
            "4. Заполните данные для доставки\n"
            "5. Выберите способ оплаты\n"
            "6. Нажмите 'Подтвердить заказ'\n\n"
            "Если у вас возникли проблемы, выберите тип проблемы ниже:",
            reply_markup=kb
        )
    except Exception as e:
        logging.error(f"Error in how_to_order: {e}")
        try:
            await callback.message.answer(
                "Произошла ошибка. Пожалуйста, попробуйте снова или обратитесь в поддержку.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
                ])
            )
        except Exception as ex:
            logging.error(f"Failed to send error message in how_to_order: {ex}")

# Обработчик кнопки "Проблемы с оплатой"
async def payment_issue(callback: types.CallbackQuery):
    try:
        await callback.answer()
        
        await callback.message.answer(
            "💳 Проблемы с оплатой:\n\n"
            "Возможные причины:\n"
            "- Недостаточно средств на карте\n"
            "- Банк заблокировал транзакцию\n"
            "- Превышен лимит по карте\n\n"
            "Решения:\n"
            "- Проверьте баланс карты\n"
            "- Свяжитесь с банком для разблокировки\n"
            "- Попробуйте другую карту\n"
            "- Выберите другой способ оплаты\n\n"
            "Если проблема остается, обратитесь в службу поддержки.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="how_to_order")],
                [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
            ])
        )
    except Exception as e:
        logging.error(f"Error in payment_issue: {e}")
        try:
            await callback.message.answer(
                "Произошла ошибка. Пожалуйста, попробуйте снова или обратитесь в поддержку.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
                ])
            )
        except Exception as ex:
            logging.error(f"Failed to send error message in payment_issue: {ex}")

# Обработчик кнопки "Проблемы с адресом доставки"
async def address_issue(callback: types.CallbackQuery):
    try:
        await callback.answer()
        
        await callback.message.answer(
            "📍 Проблемы с адресом доставки:\n\n"
            "Возможные причины:\n"
            "- Адрес введен некорректно\n"
            "- Нет доставки в ваш регион\n"
            "- Ошибка в форме заполнения\n\n"
            "Решения:\n"
            "- Проверьте правильность адреса\n"
            "- Убедитесь, что ваш регион входит в зону доставки\n"
            "- Заполните все обязательные поля\n\n"
            "Если проблема остается, обратитесь в службу поддержки.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="how_to_order")],
                [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
            ])
        )
    except Exception as e:
        logging.error(f"Error in address_issue: {e}")
        try:
            await callback.message.answer(
                "Произошла ошибка. Пожалуйста, попробуйте снова или обратитесь в поддержку.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
                ])
            )
        except Exception as ex:
            logging.error(f"Failed to send error message in address_issue: {ex}")

# Обработчик кнопки "Проблемы с корзиной"
async def cart_issue(callback: types.CallbackQuery):
    try:
        await callback.answer()
        
        await callback.message.answer(
            "🛒 Проблемы с корзиной:\n\n"
            "Возможные причины:\n"
            "- Товар закончился на складе\n"
            "- Ошибка в системе\n"
            "- Товар недоступен в вашем регионе\n\n"
            "Решения:\n"
            "- Обновите страницу\n"
            "- Очистите кеш браузера\n"
            "- Попробуйте войти с другого устройства\n"
            "- Проверьте наличие товара\n\n"
            "Если проблема остается, обратитесь в службу поддержки.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="how_to_order")],
                [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
            ])
        )
    except Exception as e:
        logging.error(f"Error in cart_issue: {e}")
        try:
            await callback.message.answer(
                "Произошла ошибка. Пожалуйста, попробуйте снова или обратитесь в поддержку.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
                ])
            )
        except Exception as ex:
            logging.error(f"Failed to send error message in cart_issue: {ex}")

# Обработчик кнопки "Самовывоз"
async def pickup_issue(callback: types.CallbackQuery):
    try:
        await callback.answer()
        
        await callback.message.answer(
            "🚚 Самовывоз:\n\n"
            "Как оформить самовывоз:\n"
            "1. Добавьте товары в корзину\n"
            "2. При оформлении выберите 'Самовывоз'\n"
            "3. Выберите удобный пункт выдачи\n"
            "4. Завершите оформление заказа\n\n"
            "Что нужно для получения:\n"
            "- Номер заказа\n"
            "- Паспорт или другой документ\n\n"
            "Срок хранения заказа в пункте выдачи - 5 дней.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="how_to_order")],
                [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
            ])
        )
    except Exception as e:
        logging.error(f"Error in pickup_issue: {e}")
        try:
            await callback.message.answer(
                "Произошла ошибка. Пожалуйста, попробуйте снова или обратитесь в поддержку.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
                ])
            )
        except Exception as ex:
            logging.error(f"Failed to send error message in pickup_issue: {ex}")

# Функция для регистрации обработчиков в диспетчере
def register_handlers(dp):
    dp.callback_query(lambda c: c.data == "how_to_order")(how_to_order)
    dp.callback_query(lambda c: c.data == "payment_issue")(payment_issue)
    dp.callback_query(lambda c: c.data == "address_issue")(address_issue)
    dp.callback_query(lambda c: c.data == "cart_issue")(cart_issue)
    dp.callback_query(lambda c: c.data == "pickup_issue")(pickup_issue) 