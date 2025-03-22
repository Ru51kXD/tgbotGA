from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging

# Клавиатура для меню "Не пришла карта"
missing_card_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📭 Карта не пришла", callback_data="card_not_arrived")],
    [InlineKeyboardButton(text="📱 Повторно отправить SMS", callback_data="resend_sms")],
    [InlineKeyboardButton(text="⏱ Сроки доставки", callback_data="shipping_time")],
    [InlineKeyboardButton(text="📝 Обновить данные", callback_data="update_card_info")],
    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
])

# Обработчик кнопки "Не пришла карта"
async def missing_card_menu(callback: types.CallbackQuery):
    try:
        await callback.answer()
        
        await callback.message.answer(
            "📭 Проблемы с доставкой карты\n\n"
            "Выберите интересующий вас раздел:",
            reply_markup=missing_card_kb
        )
    except Exception as e:
        logging.error(f"Error in missing_card_menu: {e}")
        try:
            await callback.message.answer(
                "Произошла ошибка. Пожалуйста, попробуйте снова или обратитесь в поддержку.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
                ])
            )
        except Exception as ex:
            logging.error(f"Failed to send error message in missing_card_menu: {ex}")

# Обработчик кнопки "Карта не пришла"
async def card_not_arrived(callback: types.CallbackQuery):
    try:
        await callback.answer()
        
        await callback.message.answer(
            "📭 Карта не пришла\n\n"
            "Если вы не получили карту в указанные сроки, это могло произойти по нескольким причинам:\n\n"
            "1. Срок доставки еще не истек (стандартный срок - до 14 рабочих дней)\n"
            "2. Указан неверный адрес доставки\n"
            "3. Проблемы с почтовым отправлением\n\n"
            "Что можно сделать:\n"
            "- Проверить статус отправления в личном кабинете\n"
            "- Убедиться, что адрес указан корректно\n"
            "- Связаться с курьерской службой\n\n"
            "Если карта не доставлена более 14 рабочих дней, обратитесь в службу поддержки.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="missing_card")],
                [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
            ])
        )
    except Exception as e:
        logging.error(f"Error in card_not_arrived: {e}")
        try:
            await callback.message.answer(
                "Произошла ошибка. Пожалуйста, попробуйте снова или обратитесь в поддержку.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
                ])
            )
        except Exception as ex:
            logging.error(f"Failed to send error message in card_not_arrived: {ex}")

# Обработчик кнопки "Повторно отправить SMS"
async def resend_sms(callback: types.CallbackQuery):
    try:
        await callback.answer()
        
        await callback.message.answer(
            "📱 Повторная отправка SMS\n\n"
            "Для повторной отправки SMS с кодом активации карты:\n\n"
            "1. Войдите в личный кабинет на сайте goldapple.ru\n"
            "2. Перейдите в раздел 'Мои карты'\n"
            "3. Выберите карту, по которой нужно повторно отправить SMS\n"
            "4. Нажмите кнопку 'Отправить SMS повторно'\n\n"
            "Или обратитесь в службу поддержки по телефону 8-800-555-33-22.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="missing_card")],
                [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
            ])
        )
    except Exception as e:
        logging.error(f"Error in resend_sms: {e}")
        try:
            await callback.message.answer(
                "Произошла ошибка. Пожалуйста, попробуйте снова или обратитесь в поддержку.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
                ])
            )
        except Exception as ex:
            logging.error(f"Failed to send error message in resend_sms: {ex}")

# Обработчик кнопки "Сроки доставки"
async def shipping_time(callback: types.CallbackQuery):
    try:
        await callback.answer()
        
        await callback.message.answer(
            "⏱ Сроки доставки карт\n\n"
            "Стандартные сроки доставки карт Gold Apple:\n\n"
            "🏙 Москва и Санкт-Петербург: 2-5 рабочих дней\n"
            "🏙 Другие крупные города: 5-7 рабочих дней\n"
            "🏙 Остальные регионы: 7-14 рабочих дней\n\n"
            "Электронные подарочные карты отправляются на email моментально после оплаты.\n\n"
            "Примечание: в периоды высокой загрузки (праздники, распродажи) сроки могут увеличиваться.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="missing_card")],
                [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
            ])
        )
    except Exception as e:
        logging.error(f"Error in shipping_time: {e}")
        try:
            await callback.message.answer(
                "Произошла ошибка. Пожалуйста, попробуйте снова или обратитесь в поддержку.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
                ])
            )
        except Exception as ex:
            logging.error(f"Failed to send error message in shipping_time: {ex}")

# Обработчик кнопки "Обновить данные"
async def update_card_info(callback: types.CallbackQuery):
    try:
        await callback.answer()
        
        await callback.message.answer(
            "📝 Обновление данных для доставки карты\n\n"
            "Если вам нужно изменить адрес или другие данные для доставки карты:\n\n"
            "1. Войдите в личный кабинет на сайте goldapple.ru\n"
            "2. Перейдите в раздел 'Профиль'\n"
            "3. Выберите 'Адреса доставки'\n"
            "4. Измените или добавьте новый адрес\n\n"
            "Если карта уже отправлена, изменить адрес доставки нельзя.\n"
            "В этом случае обратитесь в службу поддержки по телефону 8-800-555-33-22.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="missing_card")],
                [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
            ])
        )
    except Exception as e:
        logging.error(f"Error in update_card_info: {e}")
        try:
            await callback.message.answer(
                "Произошла ошибка. Пожалуйста, попробуйте снова или обратитесь в поддержку.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
                ])
            )
        except Exception as ex:
            logging.error(f"Failed to send error message in update_card_info: {ex}")

# Функция для регистрации обработчиков в диспетчере
def register_handlers(dp):
    dp.callback_query(lambda c: c.data == "missing_card")(missing_card_menu)
    dp.callback_query(lambda c: c.data == "card_not_arrived")(card_not_arrived)
    dp.callback_query(lambda c: c.data == "resend_sms")(resend_sms)
    dp.callback_query(lambda c: c.data == "shipping_time")(shipping_time)
    dp.callback_query(lambda c: c.data == "update_card_info")(update_card_info) 