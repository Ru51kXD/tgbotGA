from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
import logging
# from aiogram.dispatcher import Dispatcher

# Клавиатура главного меню
main_menu_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📦 Каталог товаров", url="https://goldapple.ru/catalog")],
    [InlineKeyboardButton(text="📍 Ближайшие магазины", url="https://goldapple.ru/stores")],
    [InlineKeyboardButton(text="💡 FAQ (Часто задаваемые вопросы)", url="https://goldapple.ru/faq")],
    [InlineKeyboardButton(text="🔥 Акции", callback_data="sales")],
    [InlineKeyboardButton(text="📭 Не пришла карта", callback_data="missing_card")],
    [InlineKeyboardButton(text="📦 Статус заказа", callback_data="order_status")],
    [InlineKeyboardButton(text="🆘 Техподдержка", callback_data="support_request")],
    [InlineKeyboardButton(text="🎁 Подарочные карты", callback_data="gift_cards")],
    [InlineKeyboardButton(text="🛒 Как оформить заказ", callback_data="how_to_order")],
    [InlineKeyboardButton(text="❌ Отменить заказ", callback_data="order_cancellation")],
    [InlineKeyboardButton(text="🛍️ Консультация по товару", callback_data="product_recommendations")],
    [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main")]
])

# Функция для отображения главного меню
async def show_main_menu(message):
    """Отображает главное меню.
    
    Эта функция пытается двумя способами отобразить главное меню:
    1. Если передан объект message с методом edit_text, пытается редактировать существующее сообщение
    2. Если редактирование не удалось или не применимо, отправляет новое сообщение
    """
    print(f"DEBUG: Отображение главного меню вызвано для {getattr(message, 'chat', {}).get('id', 'неизвестно')}")
    
    # Функция отправки нового сообщения
    async def send_new_menu():
        try:
            if hasattr(message, 'answer'):
                await message.answer(
                    "👋 Добро пожаловать в главное меню!\n\n"
                    "Выберите нужный раздел:",
                    reply_markup=main_menu_kb
                )
            elif hasattr(message, 'send_message'):
                # Если передан объект типа bot
                chat_id = message.chat.id
                await message.send_message(
                    chat_id=chat_id,
                    text="👋 Добро пожаловать в главное меню!\n\n"
                         "Выберите нужный раздел:",
                    reply_markup=main_menu_kb
                )
        except Exception as e:
            logging.error(f"Не удалось отправить новое сообщение с меню: {e}")
    
    # Сначала пробуем отредактировать
    try:
        if hasattr(message, 'edit_text'):
            await message.edit_text(
                "👋 Добро пожаловать в главное меню!\n\n"
                "Выберите нужный раздел:",
                reply_markup=main_menu_kb
            )
            return
    except Exception as e:
        logging.error(f"Не удалось отредактировать сообщение для меню: {e}")
        await send_new_menu()
        return
    
    # Если сюда дошли, значит редактирование не применимо
    await send_new_menu()

# Обработчик кнопки "Вернуться в главное меню"
async def back_to_main_menu(callback: types.CallbackQuery, state: FSMContext = None):
    print(f"DEBUG: back_to_main_menu callback received from user {callback.from_user.id}")
    
    try:
        # Если передано состояние, сбрасываем его
        if state:
            await state.clear()
            print(f"DEBUG: State cleared for user {callback.from_user.id}")
            
        # Отвечаем на callback
        await callback.answer("Возвращаемся в главное меню")
        
        # Показываем главное меню
        await callback.message.answer(
            "👋 Добро пожаловать в главное меню!\n\n"
            "Выберите нужный раздел:",
            reply_markup=main_menu_kb
        )
    except Exception as e:
        logging.error(f"Error in back_to_main_menu: {e}")
        try:
            await callback.message.answer(
                "👋 Добро пожаловать в главное меню!\n\n"
                "Выберите нужный раздел:",
                reply_markup=main_menu_kb
            )
        except Exception as ex:
            logging.error(f"Failed to send main menu message in back_to_main_menu: {ex}")

# Обработчик команды /start
async def start_cmd(message: types.Message):
    try:
        await message.answer(
            f"👋 Привет, {message.from_user.first_name}!\n\n"
            "Я бот-помощник Gold Apple. Чем могу помочь?",
            reply_markup=main_menu_kb
        )
    except Exception as e:
        logging.error(f"Error in start_cmd: {e}")

# Функция для регистрации обработчиков в диспетчере
def register_handlers(dp: Dispatcher):
    # Регистрация обработчика команды /start
    @dp.message(lambda message: message.text == "/start")
    async def start_handler(message: types.Message):
        await start_cmd(message)
    
    # Добавим обработчик для команды /menu
    @dp.message(lambda message: message.text == "/menu")
    async def menu_handler(message: types.Message):
        print(f"DEBUG: Получена команда /menu от пользователя {message.from_user.id}")
        await message.answer(
            "👋 Главное меню\n\n"
            "Выберите нужный раздел:",
            reply_markup=main_menu_kb
        )
    
    # Регистрация обработчика для кнопки "Вернуться в главное меню"
    @dp.callback_query(lambda c: c.data == "back_to_main")
    async def back_to_main_handler(callback: types.CallbackQuery, state: FSMContext):
        await back_to_main_menu(callback, state) 