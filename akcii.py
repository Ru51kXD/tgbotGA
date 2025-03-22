from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging

# Обработчик кнопки "Акции"
async def show_sales(callback: types.CallbackQuery):
    try:
        await callback.answer()
        await callback.message.answer(
            "🔥 Текущие акции:\n\n"
            "1. Скидка 20% на первый заказ\n"
            "2. Скидка 5% при оплате картой Gold\n"
            "3. Бесплатная доставка при заказе от 5000₽\n\n"
            "Подробности на сайте: https://goldapple.ru/sales",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Скидка на первый заказ", callback_data="first_order_discount")],
                [InlineKeyboardButton(text="Скидка при оплате картой", callback_data="card_discount")],
                [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main")]
            ])
        )
    except Exception as e:
        logging.error(f"Error in show_sales: {e}")
        try:
            await callback.message.answer(
                "Произошла ошибка при загрузке акций. Пожалуйста, попробуйте позже или обратитесь в поддержку.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main")]
                ])
            )
        except Exception as ex:
            logging.error(f"Failed to send error message in show_sales: {ex}")

# Обработчик кнопки "Скидка на первый заказ"
async def first_order_discount(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "🎁 Скидка 20% на первый заказ\n\n"
        "Как получить:\n"
        "- Зарегистрируйтесь на сайте goldapple.ru\n"
        "- Добавьте товары в корзину\n"
        "- Введите промокод FIRST20 при оформлении\n\n"
        "Условия:\n"
        "- Действует только для новых клиентов\n"
        "- Не суммируется с другими акциями\n"
        "- Не распространяется на товары со скидкой",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад к акциям", callback_data="sales")],
            [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main")]
        ])
    )

# Обработчик кнопки "Скидка при оплате картой"
async def card_discount(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "💳 Скидка 5% при оплате картой Gold\n\n"
        "Как получить:\n"
        "- Оформите заказ на сайте goldapple.ru\n"
        "- Выберите способ оплаты 'Картой Gold'\n\n"
        "Условия:\n"
        "- Скидка применяется автоматически\n"
        "- Суммируется с бонусными баллами\n"
        "- Не распространяется на товары со скидкой более 40%",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад к акциям", callback_data="sales")],
            [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main")]
        ])
    )

# Функция для регистрации обработчиков в диспетчере
def register_handlers(dp):
    dp.callback_query(lambda c: c.data == "sales")(show_sales)
    dp.callback_query(lambda c: c.data == "first_order_discount")(first_order_discount)
    dp.callback_query(lambda c: c.data == "card_discount")(card_discount) 