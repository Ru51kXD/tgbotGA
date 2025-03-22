import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Загружаем токен из .env
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
OPERATOR_CHAT_ID = int(os.getenv('SUPPORT_CHAT_ID'))

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Состояние для чата поддержки
class SupportState(StatesGroup):
    in_chat = State()

# Активные чаты {user_id: True}
active_chats = {}

# Клавиатура стартового меню
start_kb = types.InlineKeyboardMarkup(inline_keyboard=[
    [types.InlineKeyboardButton(text="🆘 Техподдержка", callback_data="support_test")],
    [types.InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main")]
])

# Обработчик команды /start
@dp.message(lambda message: message.text == "/start")
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Это тестовый бот для проверки функции техподдержки\n\n"
        "Нажмите на кнопку 'Техподдержка' для проверки:",
        reply_markup=start_kb
    )

# Обработчик для запуска чата поддержки
@dp.callback_query(lambda c: c.data == "support_test")
async def start_support_chat(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    
    try:
        print(f"DEBUG: Получен запрос поддержки от пользователя {user_id}")
        
        # Отвечаем на callback
        await callback.answer("Подключаем вас к чату поддержки...")
        
        # Устанавливаем состояние в чате
        active_chats[user_id] = True
        await state.set_state(SupportState.in_chat)
        
        # Отправляем сообщение пользователю
        await callback.message.answer(
            "👨‍💼 Вы подключены к тестовому чату поддержки.\n\n"
            "Это тестовое сообщение, подтверждающее что функция работает!",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="❌ Завершить чат", callback_data=f"end_chat_{user_id}")],
                [types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
            ])
        )
        
        # Уведомляем оператора
        await bot.send_message(
            OPERATOR_CHAT_ID,
            f"👤 Пользователь {user_id} подключился к тестовому чату поддержки."
        )
        
    except Exception as e:
        logging.error(f"Error in start_support_chat: {e}")
        await callback.message.answer(
            "⚠️ Произошла ошибка при подключении к чату поддержки. Пожалуйста, попробуйте позже.",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
            ])
        )

# Обработчик кнопки "Вернуться в главное меню"
@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main_menu(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.answer("Возвращаемся в главное меню...")
        
        # Сбрасываем состояние
        await state.clear()
        
        # Отправляем стартовое меню
        await callback.message.edit_text(
            "👋 Главное меню тестового бота\n\n"
            "Нажмите на кнопку 'Техподдержка' для проверки:",
            reply_markup=start_kb
        )
    except Exception as e:
        logging.error(f"Error in back_to_main_menu: {e}")
        await callback.message.answer(
            "Произошла ошибка. Возвращаемся в главное меню...",
            reply_markup=start_kb
        )

# Обработчик для завершения чата с оператором
@dp.callback_query(lambda c: c.data.startswith("end_chat_"))
async def end_chat_callback(callback: types.CallbackQuery, state: FSMContext):
    try:
        user_id = int(callback.data.split("_")[2])
        
        if user_id in active_chats:
            active_chats.pop(user_id)
            
            # Уведомляем пользователя
            await callback.message.edit_text(
                "✅ Тестовый чат с оператором завершен.\n\n"
                "Тест успешно завершен!",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_main")]
                ])
            )
            
            # Сбрасываем состояние
            await state.clear()
    except Exception as e:
        logging.error(f"Error in end_chat_callback: {e}")
        await callback.answer("Произошла ошибка при завершении чата. Попробуйте еще раз.")

# Запуск бота
async def main():
    print("Запуск тестового бота для проверки техподдержки...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен!") 