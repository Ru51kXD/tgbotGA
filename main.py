import asyncio
import logging
import os
import random
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.callback_data import CallbackData
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from aiogram.fsm.state import State, StatesGroup
from typing import Dict, Any
# Загружаем переменные из .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
OPERATOR_CHAT_ID = int(os.getenv("SUPPORT_CHAT_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Активные чаты {user_id: True}
active_chats = {}

class RecommendationState(StatesGroup):
    waiting_for_category = State()
    waiting_for_criteria = State()
# Создаем состояние для ожидания ответа пользователя
class ProductSelectionState(StatesGroup):
    waiting_for_product_details = State()

# Состояние для ввода номера карты
class BalanceCheckState(StatesGroup):
    waiting_for_card_number = State()

class SupportState(StatesGroup):
    in_chat = State()
    waiting_for_question = State()

# Клавиатура для запроса номера телефона
phone_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📱 Поделиться номером", request_contact=True)]],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Главное меню с кнопкой "Вернуться в главное меню"
main_menu_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📦 Каталог товаров", url="https://goldapple.ru/catalog")],
    [InlineKeyboardButton(text="📍 Ближайшие магазины", url="https://goldapple.ru/stores")],
    [InlineKeyboardButton(text="💡 FAQ (Часто задаваемые вопросы)", url="https://goldapple.ru/faq")],
    [InlineKeyboardButton(text="🔥 Акции", callback_data="sales")],
    [InlineKeyboardButton(text="📭 Не пришла карта", callback_data="missing_card")],
    #[InlineKeyboardButton(text="🎁 Подарочные карты", url="https://goldapple.ru/giftcard")],
    [InlineKeyboardButton(text="📦 Статус заказа", callback_data="order_status")],
    [InlineKeyboardButton(text="🆘 Техподдержка", callback_data="support_request")],
    [InlineKeyboardButton(text="🎁 Подарочные карты", callback_data="gift_cards")],
    [InlineKeyboardButton(text="🛒 Как оформить заказ", callback_data="how_to_order")],
    
    [InlineKeyboardButton(text="❌ Отменить заказ", callback_data="cancel_order")],
    [InlineKeyboardButton(text="🛍️ Консультация по товару", callback_data="product_consultation")],
    [InlineKeyboardButton(text="🎯 Рекомендации", callback_data="product_recommendations")],
    [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main")]
])
gift_cards_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🛒 Как купить?", callback_data="gift_how_to_buy")],
    [InlineKeyboardButton(text="📖 Как использовать?", callback_data="gift_how_to_use")],
    [InlineKeyboardButton(text="👥 Карты для коллег", callback_data="gift_for_colleagues")],
    [InlineKeyboardButton(text="💳 Узнать баланс карты", callback_data="gift_check_balance")],
    [InlineKeyboardButton(text="🔙 Вернуться назад", callback_data="back_to_main")]
])
#

# Клавиатура "Не пришла карта"
missing_card_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📭 Карта не дошла", callback_data="card_not_arrived")],
    [InlineKeyboardButton(text="📩 Продублировать SMS", callback_data="resend_sms")],
    [InlineKeyboardButton(text="⏳ Узнать время отправки", callback_data="shipping_time")],
    [InlineKeyboardButton(text="✏ Изменить данные", callback_data="update_card_info")],
    [InlineKeyboardButton(text="🎁 Как купить", callback_data="how_to_buy_card")],
    [InlineKeyboardButton(text="🛍 Как использовать", callback_data="how_to_use_card")],
    [InlineKeyboardButton(text="🔙 Вернуться назад", callback_data="back_to_main")],
    [InlineKeyboardButton(text="❓ Другой вопрос", callback_data="support_request")]
])

order_faq_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="💳 Вопрос по оплате", callback_data="payment_issue")],
    [InlineKeyboardButton(text="📍 Не могу выбрать адрес", callback_data="address_issue")],
    [InlineKeyboardButton(text="🛒 Не добавляется в корзину", callback_data="cart_issue")],
    [InlineKeyboardButton(text="🚚 Почему недоступен самовывоз?", callback_data="pickup_issue")],
    [InlineKeyboardButton(text="🔙 Вернуться назад", callback_data="back_to_main")]
])

# Клавиатура с подтверждением отмены заказа
cancel_order_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ Отменяем", callback_data="confirm_cancel")],
    [InlineKeyboardButton(text="❌ Не буду отменять", callback_data="decline_cancel")]
])
confirm_cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main")]
])

# Клавиатура для консультации по товару
product_consult_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="💰 Узнать цену и наличие", callback_data="product_price_availability")],
    [InlineKeyboardButton(text="📜 Сертификат качества", callback_data="product_quality_certificate")],
    [InlineKeyboardButton(text="🔍 Подобрать товар", callback_data="product_selection")],
    [InlineKeyboardButton(text="❓ Другой вопрос", callback_data="support_request")],
    [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main")]
])
recommendation_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🌸 Духи", callback_data="recommend_perfume")],
    [InlineKeyboardButton(text="💄 Тушь", callback_data="recommend_mascara")],
    [InlineKeyboardButton(text="💋 Помада", callback_data="recommend_lipstick")],
    [InlineKeyboardButton(text="🧴 Уход за кожей", callback_data="recommend_skincare")],
    [InlineKeyboardButton(text="🧼 Средства для ванны", callback_data="recommend_bath")],
    [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main")]
])

criteria_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="💰 Бюджетные", callback_data="criteria_budget")],
    [InlineKeyboardButton(text="💎 Премиум", callback_data="criteria_premium")],
    [InlineKeyboardButton(text="🏆 Популярные", callback_data="criteria_popular")],
    [InlineKeyboardButton(text="🎯 Все варианты", callback_data="criteria_all")]
])

# Добавляем обработчики
@dp.callback_query(lambda c: c.data == "product_recommendations")
async def product_recommendations(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🎯 *Рекомендации товаров*\n\n"
        "Выберите категорию товаров:",
        parse_mode="Markdown",
        reply_markup=recommendation_kb
    )

@dp.callback_query(lambda c: c.data.startswith("recommend_"))
async def handle_recommendation_category(callback: types.CallbackQuery, state: FSMContext):
    category = callback.data.split("_")[1]
    await state.update_data(category=category)
    
    await callback.message.edit_text(
        "📌 Выберите критерии подбора:",
        reply_markup=criteria_kb
    )
    await state.set_state(RecommendationState.waiting_for_criteria)

@dp.callback_query(lambda c: c.data.startswith("criteria_"), RecommendationState.waiting_for_criteria)
async def handle_criteria_selection(callback: types.CallbackQuery, state: FSMContext):
    criteria = callback.data.split("_")[1]
    user_data = await state.get_data()
    category = user_data.get('category')
    
    user_id = callback.from_user.id
    username = callback.from_user.username or "Без username"
    phone_number = user_contacts.get(user_id, "Не указан")

    await bot.send_message(
        OPERATOR_CHAT_ID,
        f"🔔 Запрос на подбор товаров!\n"
        f"👤 Пользователь: @{username} (ID: {user_id})\n"
        f"📞 Телефон: {phone_number}\n"
        f"Категория: {category}\n"
        f"Критерии: {criteria}\n\n"
        f"Отправьте ссылку в формате:\n/send_recommendation {user_id} ваша_ссылка"
    )
    
    await callback.message.answer("✅ Запрос передан оператору!")
    await state.clear()

# Добавляем обработчик для оператора
@dp.message(lambda message: message.chat.id == OPERATOR_CHAT_ID and message.text.startswith("/send_recommendation"))
async def send_recommendation(message: Message):
    try:
        _, user_id, *link_parts = message.text.split()
        target_user_id = int(user_id)
        link = ' '.join(link_parts)
        
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Перейти к товарам", url=link)],
            [InlineKeyboardButton(text="🎯 Новые рекомендации", callback_data="product_recommendations")]
        ])
        
        await bot.send_message(
            target_user_id,
            f"🎁 Персональные рекомендации:\n{link}",
            reply_markup=markup
        )
        await message.answer("✅ Рекомендации отправлены!")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


# Обработчик нажатия "Консультация по товару"
@dp.callback_query(lambda c: c.data == "product_consultation")
async def product_consultation(callback: types.CallbackQuery):
    await callback.message.edit_text("Выберите интересующий вас вопрос:", reply_markup=product_consult_kb)

# Обработчик "Узнать цену и наличие"
@dp.callback_query(lambda c: c.data == "product_price_availability")
async def product_price_availability(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "💰 *Как узнать цену и наличие товара?*\n\n"
        "✅ Актуальная цена и наличие указаны на сайте. \n"
        "🔗 Проверьте информацию здесь: [Перейти в каталог](https://goldapple.ru/catalog).",
        parse_mode="Markdown",
        reply_markup=product_consult_kb
    )

# Обработчик "Сертификат качества"
@dp.callback_query(lambda c: c.data == "product_quality_certificate")
async def product_quality_certificate(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📜 *Сертификаты качества товаров* \n\n"
        "Все товары сертифицированы. Если вам нужен сертификат, отправьте запрос в техподдержку.",
        parse_mode="Markdown",
        reply_markup=product_consult_kb
    )
###############################################################
# Обработчик "Подобрать товар"
# Обработчик "Подобрать товар"
@dp.callback_query(lambda c: c.data == "product_selection")
async def product_selection(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🔍 *Поможем выбрать товар!* \n\n"
        "Напишите, какой товар вам нужен.",
        parse_mode="Markdown"
    )

    # Ждем ответа пользователя
    @dp.message()
    async def forward_to_operator(message: types.Message):
        user_id = message.from_user.id
        username = message.from_user.username or "Нет юзернейма"
        phone_number = "Не указан"

        # Проверяем, передавал ли пользователь контакт ранее
        if message.contact:
            phone_number = message.contact.phone_number

        # Отправляем сообщение оператору
        await bot.send_message(
            OPERATOR_CHAT_ID,
            f"🔔 Запрос на подбор товара!\n"
            f"👤 Пользователь: @{username} (ID: {user_id})\n"
            f"📞 Номер: {phone_number}\n"
            f"💬 Сообщение: {message.text}"
        )
###################################################################################################################
@dp.callback_query(lambda c: c.data == "cancel_order")
async def cancel_order(callback: types.CallbackQuery):
    message_text = """❌ *Хотите отменить заказ? 🤔*

Эх, рассказываю условия отмены:
▫️ Восстановить отменённый заказ нельзя  
▫️ Возврат в течение *10 дней* тем же способом, которым оплачивали  
▫️ Промокод *не восстанавливается*  
▫️ В личном кабинете статус изменится после возврата средств  

Вы уверены?  
"""
    await callback.message.edit_text(message_text, parse_mode="Markdown", reply_markup=cancel_order_kb)

@dp.callback_query(lambda c: c.data == "confirm_cancel")
async def confirm_cancel(callback: types.CallbackQuery):
    message_text = """🛑 *Как отменить заказ?*  

1️⃣ Если заказ ещё не передан в доставку, отмените его в [личном кабинете](https://goldapple.ru/account/orders).  
2️⃣ Если заказ уже отправлен, откажитесь от него при получении.  
3️⃣ Если заказ был оплачен заранее, возврат средств займет до *10 дней*.  

Для дополнительной помощи обращайтесь в техподдержку. 📞  
"""
    await callback.message.edit_text(message_text, parse_mode="Markdown", reply_markup=confirm_cancel_kb)

@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    await callback.message.edit_text("Добро пожаловать! Выберите нужный раздел:", reply_markup=main_menu_kb)

@dp.callback_query(lambda c: c.data == "decline_cancel")
async def decline_cancel(callback: types.CallbackQuery):
    await callback.message.edit_text("Спасибо, что остаетесь с нами! 😊", reply_markup=main_menu_kb)

@dp.callback_query(lambda c: c.data == "how_to_order")
async def how_to_order(callback: types.CallbackQuery):
    message_text = """📦 *Как оформить заказ?*

1️⃣ Выберите товары в каталоге и добавьте их в корзину.  
2️⃣ Перейдите в корзину и проверьте список товаров.  
3️⃣ Укажите адрес доставки или выберите пункт самовывоза.  
4️⃣ Выберите удобный способ оплаты и подтвердите заказ.  
5️⃣ Дождитесь подтверждения заказа и получения трек-номера.  

Если у вас возникли вопросы, выберите их ниже:  
"""
    await callback.message.edit_text(message_text, parse_mode="Markdown", reply_markup=order_faq_kb)

@dp.callback_query(lambda c: c.data == "payment_issue")
async def payment_issue(callback: types.CallbackQuery):
    message_text = """💳 *Вопрос по оплате*  

Возможные причины проблем с оплатой:  
✅ Недостаточно средств на карте.  
✅ Банк отклонил платеж – попробуйте другой способ оплаты.  
✅ Ошибка при вводе данных карты.  
✅ Платеж временно заблокирован – попробуйте позже.  

Если проблема не решилась, обратитесь в поддержку банка или выберите другой способ оплаты.  
"""
    await callback.message.edit_text(message_text, parse_mode="Markdown", reply_markup=order_faq_kb)

@dp.callback_query(lambda c: c.data == "address_issue")
async def address_issue(callback: types.CallbackQuery):
    message_text = """📍 *Не могу выбрать адрес*  

1️⃣ Убедитесь, что ваш адрес указан правильно.  
2️⃣ Проверьте, доступна ли доставка в ваш регион.  
3️⃣ Попробуйте выбрать другой адрес или изменить настройки доставки.  
4️⃣ Если проблема сохраняется, попробуйте оформить заказ через другой браузер или устройство.  

Если ничего не помогает, обратитесь в нашу поддержку.  
"""
    await callback.message.edit_text(message_text, parse_mode="Markdown", reply_markup=order_faq_kb)

@dp.callback_query(lambda c: c.data == "cart_issue")
async def cart_issue(callback: types.CallbackQuery):
    message_text = """🛒 *Не добавляется в корзину*  

Возможные причины:  
❌ Товар временно отсутствует на складе.  
❌ Ошибка соединения – попробуйте перезагрузить страницу.  
❌ Ограничение на количество товара в одном заказе.  

Попробуйте обновить страницу и повторить попытку. Если проблема сохраняется, напишите в поддержку.  
"""
    await callback.message.edit_text(message_text, parse_mode="Markdown", reply_markup=order_faq_kb)

@dp.callback_query(lambda c: c.data == "pickup_issue")
async def pickup_issue(callback: types.CallbackQuery):
    message_text = """🚚 *Почему недоступен самовывоз?*  

🔸 Самовывоз может быть недоступен из-за временных ограничений в выбранном магазине.  
🔸 Товар может быть доступен только для доставки.  
🔸 Выбранный пункт самовывоза может быть закрыт.  

Попробуйте выбрать другой пункт самовывоза или свяжитесь с нашей поддержкой для уточнения.  
"""
    await callback.message.edit_text(message_text, parse_mode="Markdown", reply_markup=order_faq_kb)
@dp.callback_query(lambda c: c.data == "missing_card")
async def missing_card_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("Выберите, что вас беспокоит:", reply_markup=missing_card_kb)

@dp.callback_query(lambda c: c.data == "card_not_arrived")
async def card_not_arrived(callback: types.CallbackQuery):
    await callback.message.answer("📦 Если карта не дошла, проверьте статус заказа в личном кабинете или обратитесь в поддержку.", reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Проверить статус заказа", url="https://goldapple.ru/lk/orders")],
            [InlineKeyboardButton(text="🆘 Связаться с поддержкой", callback_data="support_request")]
        ]
    ))

@dp.callback_query(lambda c: c.data == "resend_sms")
async def resend_sms(callback: types.CallbackQuery):
    await callback.message.answer("📩 Если вы не получили SMS с данными карты, попробуйте проверить спам или запросить повторную отправку через поддержку.", reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Запросить повторно", callback_data="support_request")]
        ]
    ))

@dp.callback_query(lambda c: c.data == "shipping_time")
async def shipping_time(callback: types.CallbackQuery):
    await callback.message.answer("⏳ Карта обычно доставляется в течение 5-7 рабочих дней. Проверьте статус отправки в личном кабинете.")

@dp.callback_query(lambda c: c.data == "update_card_info")
async def update_card_info(callback: types.CallbackQuery):
    await callback.message.answer("✏ Если необходимо изменить данные для получения карты, обратитесь в поддержку.", reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✍ Изменить данные", callback_data="support_request")]
        ]
    ))

@dp.callback_query(lambda c: c.data == "how_to_buy_card")
async def how_to_buy_card(callback: types.CallbackQuery):
    await callback.message.answer("🎁 Купить подарочную карту можно на нашем сайте по ссылке: [Перейти к покупке](https://goldapple.ru/giftcard)", parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "how_to_use_card")
async def how_to_use_card(callback: types.CallbackQuery):
    await callback.message.answer("🛍 Использовать карту просто:\n\n- Введите код карты при оформлении заказа на сайте.\n- Или покажите карту на кассе в розничном магазине.")      
@dp.callback_query(lambda c: c.data == "gift_cards")
async def gift_cards_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("🎁 *Раздел подарочных карт*\nВыберите нужный пункт:", 
                                     parse_mode="Markdown", reply_markup=gift_cards_kb)

@dp.callback_query(lambda c: c.data == "gift_how_to_buy")
async def gift_how_to_buy(callback: types.CallbackQuery):
    await callback.message.answer("🛒 Вы можете купить подарочную карту на сайте [здесь](https://goldapple.ru/giftcard).", parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "gift_how_to_use")
async def gift_how_to_use(callback: types.CallbackQuery):
    await callback.message.answer("📖 Подарочную карту можно использовать в магазинах и на сайте. Просто укажите код при оплате.")

@dp.callback_query(lambda c: c.data == "gift_for_colleagues")
async def gift_for_colleagues(callback: types.CallbackQuery):
    await callback.message.answer("👥 Вы можете приобрести корпоративные подарочные карты для коллег. Подробности [здесь](https://goldapple.ru/giftcard-corporate).", parse_mode="Markdown")

# Разветвление для проверки баланса
balance_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="💳 Пластиковая карта", callback_data="gift_balance_physical")],
    [InlineKeyboardButton(text="📧 Электронная карта", callback_data="gift_balance_digital")],
    [InlineKeyboardButton(text="🔙 Вернуться назад", callback_data="gift_cards")]
])

@dp.callback_query(lambda c: c.data == "gift_check_balance")
async def gift_check_balance(callback: types.CallbackQuery):
    await callback.message.edit_text("💳 Выберите тип карты:", reply_markup=balance_kb)

# Проверка баланса пластиковой карты
@dp.callback_query(lambda c: c.data == "gift_balance_physical")
async def gift_balance_physical(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("🔢 Введите номер вашей пластиковой карты:")
    await state.set_state(BalanceCheckState.waiting_for_card_number)

@dp.message(lambda message: message.chat.id == OPERATOR_CHAT_ID and message.text.startswith("/end"))
async def operator_end_chat(message: Message):
    try:
        target_user_id = int(message.text.split()[1])  # ID пользователя из команды
        if target_user_id in active_chats:
            active_chats.pop(target_user_id)
            await bot.send_message(target_user_id, "📴 Чат с оператором завершен.")
            await message.answer(f"✅ Чат с пользователем {target_user_id} завершён.")
        else:
            await message.answer("❗ Этот пользователь не активен в чате поддержки.")
    except (IndexError, ValueError):
        await message.answer("⚠ Ошибка! Используйте команду /end [ID пользователя].")

@dp.message(BalanceCheckState.waiting_for_card_number)
async def process_card_number(message: types.Message, state: FSMContext):
    card_number = message.text.strip()
    if not card_number.isdigit() or len(card_number) not in [16, 19]:  
        await message.answer("❌ Неверный формат номера карты. Попробуйте снова.")
        return

    await state.clear()
    await message.answer(
        "✅ Ваш баланс доступен в личном кабинете.\n\n"
        "1️⃣ Перейдите в [личный кабинет](https://goldapple.ru/login)\n"
        "2️⃣ Войдите в аккаунт, связанный с картой\n"
        "3️⃣ В разделе *'Мои карты'* найдите нужную карту и проверьте баланс",
        parse_mode="Markdown"
    )
# Разветвление для электронной карты
digital_card_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔎 Проверить баланс", url="https://goldapple.ru/check-balance")],
    [InlineKeyboardButton(text="⚠ Проблемы с картой", callback_data="gift_balance_problem")],
    [InlineKeyboardButton(text="❓ Другой вопрос", callback_data="gift_balance_other")],
    [InlineKeyboardButton(text="🔙 Вернуться назад", callback_data="gift_check_balance")]
])

@dp.callback_query(lambda c: c.data == "gift_balance_digital")
async def gift_balance_digital(callback: types.CallbackQuery):
    await callback.message.edit_text("📧 Что вас интересует?", reply_markup=digital_card_kb)

@dp.callback_query(lambda c: c.data == "gift_balance_problem")
@dp.callback_query(lambda c: c.data == "gift_balance_other")
async def gift_balance_support(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    username = callback.from_user.username or "Без username"
    phone_number = user_contacts.get(user_id, "Не указан")

    active_chats[user_id] = True
    await state.set_state(SupportState.in_chat)

    await bot.send_message(OPERATOR_CHAT_ID, f"🔔 Новый запрос по подарочным картам!\n"
                                             f"👤 Пользователь: @{username} (ID: {user_id})\n"
                                             f"📞 Телефон: {phone_number}\n"
                                             f"Проблема с электронной картой или другой вопрос.")
    await callback.message.answer("✅ Оператор подключился! Опишите вашу проблему.")
#

@dp.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer("Привет! Поделитесь номером телефона, чтобы мы могли помочь вам!", reply_markup=phone_kb)

user_contacts = {}  # Хранение номеров пользователей {user_id: phone_number}

@dp.message(lambda message: message.contact)
async def handle_contact(message: Message):
    user_id = message.from_user.id
    if user_id in user_contacts:
        await message.answer("📌 Мы уже получили ваш номер. Выберите нужный раздел:", reply_markup=main_menu_kb)
    else:
        user_contacts[user_id] = message.contact.phone_number
        await message.answer("Спасибо! Теперь напишите свой вопрос одним сообщением так будет легче помочь вам!", reply_markup=types.ReplyKeyboardRemove())
        await message.answer("Добро пожаловать! Выберите нужный раздел:", reply_markup=main_menu_kb)

@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    await callback.message.edit_text("Добро пожаловать! Выберите нужный раздел:", reply_markup=main_menu_kb)

sales_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="10% на ПЕРВЫЙ заказ", callback_data="first_order_discount")],
    [InlineKeyboardButton(text="Скидка по карте", callback_data="card_discount")],
    [InlineKeyboardButton(text="🔙 Вернуться назад", callback_data="back_to_main")]
])
@dp.callback_query(lambda c: c.data == "first_order_discount")
async def first_order_discount(callback: types.CallbackQuery):
    await callback.message.answer("🎉 Чтобы получить 10% скидку на первый заказ, введите промокод *WELCOME10* при оформлении!", parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "card_discount")
async def card_discount(callback: types.CallbackQuery):
    await callback.message.answer("💳 Воспользуйтесь картой лояльности, чтобы получать кешбэк и дополнительные скидки!")

@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    await callback.message.edit_text("Добро пожаловать! Выберите нужный раздел:", reply_markup=main_menu_kb)

@dp.callback_query(lambda c: c.data == "sales")
async def show_sales(callback: types.CallbackQuery):
    message_text = """🔥 *АКЦИИ И СКИДКИ* 🔥

🎁 *10% на первый заказ!*  
Получите скидку на ваш первый заказ.  

💳 *Скидка по карте*  
Оплачивайте картой лояльности и получайте бонусы!  

📅 Актуальные скидки и акции можно найти [здесь](https://goldapple.ru/sale).
"""

    await callback.message.edit_text(message_text, parse_mode="Markdown", reply_markup=sales_kb)

@dp.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer("Добро пожаловать! Выберите нужный раздел:", reply_markup=main_menu_kb)


@dp.callback_query(lambda c: c.data == "support_request")
async def support_request(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    username = callback.from_user.username or "Без username"
    phone_number = user_contacts.get(user_id, "Не указан")

    if user_id in active_chats:
        await callback.message.answer("❗ Вы уже на связи с оператором.")
        return
    
    active_chats[user_id] = True
    await state.set_state(SupportState.in_chat)

    # Уведомляем оператора с номером телефона
    await bot.send_message(OPERATOR_CHAT_ID, f"🔔 Новый запрос в поддержку!\n"
                                             f"👤 Пользователь: @{username} (ID: {user_id})\n"
                                             f"📞 Телефон: {phone_number}\n"
                                             f"Напишите сообщение, оно будет переслано пользователю.")
    await callback.message.answer("✅ Оператор подключился! Вы можете задавать вопросы.")

@dp.message()
async def handle_messages(message: Message, state: FSMContext):
    user_id = message.from_user.id

    # Если пользователь в чате с оператором
    if user_id in active_chats:
        await bot.send_message(OPERATOR_CHAT_ID, f"👤 Пользователь: {message.text}")
        return

    # Если оператор отвечает в чате операторов
    if message.chat.id == OPERATOR_CHAT_ID:
        try:
            split_msg = message.text.split(" ", 1)
            target_user_id = int(split_msg[0])  # ID пользователя
            reply_text = split_msg[1]  # Текст ответа

            if target_user_id in active_chats:
                # Клавиатура с кнопками "Остались вопросы?" и "Завершить диалог"
                buttons = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="❓ Остались вопросы?", callback_data=f"more_questions_{target_user_id}")],
                    [InlineKeyboardButton(text="🚫 Завершить диалог", callback_data=f"end_chat_{target_user_id}")]
                ])
                
                await bot.send_message(target_user_id, f"👨‍💼 Оператор: {reply_text}", reply_markup=buttons)
            else:
                await message.answer("❗ Этот пользователь не активен в чате поддержки.")
        except (IndexError, ValueError):
            await message.answer("⚠ Ошибка! Введите ID пользователя и текст через пробел.")


@dp.callback_query(lambda c: c.data.startswith("more_questions_"))
async def more_questions(callback: types.CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split("_")[2])

    if user_id in active_chats:
        # Клавиатура: "Ввести вопрос" и "Завершить чат"
        question_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Завершить чат", callback_data=f"end_chat_{user_id}")]
        ])
        await bot.send_message(user_id, "🤔 Какие вопросы у вас остались? Или хотите завершить чат?", reply_markup=question_kb)
        await state.set_state(SupportState.waiting_for_question)
    else:
        await callback.answer("Чат уже завершен.")


@dp.message(SupportState.waiting_for_question)
async def handle_more_questions(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if user_id in active_chats:
        await bot.send_message(OPERATOR_CHAT_ID, f"🔄 Дополнительный вопрос от {user_id}: {message.text}")
        # Повторно отправляем клавиатуру оператору
        buttons = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❓ Остались вопросы?", callback_data=f"more_questions_{user_id}")],
            [InlineKeyboardButton(text="🚫 Завершить диалог", callback_data=f"end_chat_{user_id}")]
        ])
        await bot.send_message(user_id, "Оператор получил ваш вопрос и ответит скоро.", reply_markup=buttons)
        await state.set_state(SupportState.in_chat)


@dp.callback_query(lambda c: c.data.startswith("end_chat_"))
async def end_chat_callback(callback: types.CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split("_")[2])

    if user_id in active_chats:
        active_chats.pop(user_id)
        await bot.send_message(user_id, "📴 Чат с оператором завершен.")
        await bot.send_message(OPERATOR_CHAT_ID, f"🚫 Пользователь {user_id} завершил чат.")
        await state.clear()
    await callback.answer("Чат завершен.")


async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
