import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Загружаем переменные из .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
OPERATOR_CHAT_ID = int(os.getenv("SUPPORT_CHAT_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Активные чаты {user_id: True}
active_chats = {}


class SupportState(StatesGroup):
    in_chat = State()
    waiting_for_question = State()


# Клавиатура "Техподдержка" + "FAQ"
support_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📩 Техподдержка", callback_data="support_request")],
    [InlineKeyboardButton(text="💡 FAQ (Часто задаваемые вопросы)", url="https://goldapple.ru/faq")]
])

main_menu_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📦 Каталог товаров", url="https://goldapple.ru/catalog")],
    [InlineKeyboardButton(text="🔥 Акции", callback_data="sales")],  # БЫЛ URL, СТАЛА callback_data
    [InlineKeyboardButton(text="🎁 Подарочные карты", url="https://goldapple.ru/giftcard")],
    [InlineKeyboardButton(text="📍 Ближайшие магазины", url="https://goldapple.ru/stores")],
    [InlineKeyboardButton(text="📦 Статус заказа", callback_data="order_status")],
    [InlineKeyboardButton(text="💡 FAQ (Часто задаваемые вопросы)", url="https://goldapple.ru/faq")],
    [InlineKeyboardButton(text="🆘 Техподдержка", callback_data="support_request")]
])
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

@dp.callback_query(lambda c: c.data == "order_status")
async def order_status(callback: types.CallbackQuery):
    await callback.message.answer("Введите номер вашего заказа для проверки статуса:")
@dp.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer("Привет! Если нужна помощь, выберите одну из опций:", reply_markup=support_kb)


@dp.callback_query(lambda c: c.data == "support_request")
async def support_request(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    if user_id in active_chats:
        await callback.message.answer("❗ Вы уже на связи с оператором.")
        return
    
    active_chats[user_id] = True
    await state.set_state(SupportState.in_chat)

    # Уведомляем оператора
    await bot.send_message(OPERATOR_CHAT_ID, f"🔔 Новый запрос в поддержку!\n"
                                             f"👤 Пользователь: @{callback.from_user.username} (ID: {user_id})\n"
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
