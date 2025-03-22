import logging
from aiogram import types, Bot, Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Состояние для чата поддержки
class SupportState(StatesGroup):
    waiting_for_name = State()  # Ожидание ввода имени
    in_chat = State()
    waiting_for_question = State()

# Активные чаты {user_id: True}
active_chats = {}
user_contacts = {}  # Хранение номеров пользователей {user_id: phone_number}

# Обработчик сообщений с контактами (номерами телефонов)
async def handle_contact(message: types.Message, bot, main_menu_kb):
    user_id = message.from_user.id
    if user_id in user_contacts:
        await message.answer("📌 Мы уже получили ваш номер. Выберите нужный раздел:", reply_markup=main_menu_kb)
    else:
        user_contacts[user_id] = message.contact.phone_number
        await message.answer("Спасибо! Теперь напишите свой вопрос одним сообщением так будет легче помочь вам!", 
                           reply_markup=types.ReplyKeyboardRemove())
        await message.answer("Добро пожаловать! Выберите нужный раздел:", reply_markup=main_menu_kb)

# Обработчик для оператора, чтобы завершить чат с пользователем
async def operator_end_chat(message: types.Message, bot):
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

# Обработчик для завершения чата с оператором
async def end_chat_callback(callback: types.CallbackQuery, state: FSMContext, bot, OPERATOR_CHAT_ID):
    try:
        # Отвечаем на callback
        await callback.answer("Завершаем чат...")
        
        # Получаем ID пользователя из callback data
        user_id = callback.from_user.id
        
        if user_id in active_chats:
            active_chats.pop(user_id)
            
            # Уведомляем пользователя
            await callback.message.edit_text(
                "✅ Чат с оператором завершен.\n\n"
                "Если у вас появятся новые вопросы, вы всегда можете обратиться к нам снова.",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_main")]
                ])
            )
            
            # Уведомляем оператора
            await bot.send_message(
                OPERATOR_CHAT_ID,
                f"❌ Пользователь {user_id} завершил чат."
            )
            
            await state.clear()
        else:
            await callback.message.edit_text(
                "⚠️ Чат уже был завершен или вы не находитесь в активном чате.",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_main")]
                ])
            )
    except Exception as e:
        logging.error(f"Error in end_chat_callback: {e}")
        await callback.answer("Произошла ошибка при завершении чата. Попробуйте еще раз.")

# Обработчик для обычных сообщений (поддержка чата)
async def handle_messages(message: types.Message, state: FSMContext, bot, OPERATOR_CHAT_ID):
    # Пропускаем сообщения без текста
    if not message.text:
        return
        
    user_id = message.from_user.id
    current_state = await state.get_state()
    
    print(f"DEBUG: Обработка сообщения от пользователя {user_id}, состояние: {current_state}")

    # Если пользователь ожидает ввода имени
    if current_state == "SupportState:waiting_for_name":
        await handle_support_name(message, state, bot, OPERATOR_CHAT_ID)
        return

    # Если сообщение от оператора
    if message.chat.id == OPERATOR_CHAT_ID:
        # Пропускаем все команды оператора, кроме отправки обычных сообщений
        if message.text.startswith("/") and not message.text.startswith("/end"):
            return

        try:
            # Проверяем формат сообщения оператора: ID_пользователя текст_сообщения
            parts = message.text.strip().split(maxsplit=1)
            
            # Если сообщение не содержит 2 части (ID и текст)
            if len(parts) != 2:
                await message.answer(
                    "⚠️ <b>Ошибка формата!</b>\n\n"
                    "Введите ID пользователя и текст сообщения через пробел.\n"
                    "Пример: <code>123456789 Здравствуйте! Чем могу помочь?</code>"
                )
                return

            # Пытаемся преобразовать первую часть в ID пользователя
            try:
                target_user_id = int(parts[0])
            except ValueError:
                await message.answer(
                    "⚠️ <b>Неверный формат ID пользователя!</b>\n\n"
                    "ID должен быть числом.\n"
                    "Пример: <code>123456789 Здравствуйте!</code>"
                )
                return

            text = parts[1]  # Текст сообщения

            print(f"DEBUG: Оператор отправляет сообщение пользователю {target_user_id}: {text[:20]}...")

            # Проверяем, активен ли чат с пользователем
            if target_user_id not in active_chats:
                # Предлагаем оператору отправить сообщение даже если чат не активен
                await message.answer(
                    f"⚠️ Пользователь {target_user_id} не находится в активном чате.\n"
                    f"Хотите отправить сообщение всё равно?",
                    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                        [types.InlineKeyboardButton(text="✅ Да", callback_data=f"force_send_{target_user_id}")],
                        [types.InlineKeyboardButton(text="❌ Нет", callback_data="cancel_send")]
                    ])
                )
                return

            # Отправляем сообщение пользователю
            try:
                sent_msg = await bot.send_message(
                    chat_id=target_user_id,
                    text=f"👨‍💼 <b>Оператор:</b> {text}",
                    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                        [types.InlineKeyboardButton(text="❌ Завершить чат", callback_data="end_chat")]
                    ])
                )
                
                if sent_msg:
                    await message.answer(f"✅ Сообщение успешно отправлено пользователю {target_user_id}")
                else:
                    await message.answer(f"⚠️ Не удалось отправить сообщение пользователю {target_user_id}. Попробуйте еще раз.")
            except Exception as e:
                logging.error(f"Ошибка при отправке сообщения пользователю {target_user_id}: {e}")
                await message.answer(f"⚠️ Ошибка при отправке сообщения пользователю {target_user_id}: {e}")

        except Exception as e:
            logging.error(f"Ошибка при обработке сообщения оператора: {e}")
            await message.answer(
                "⚠️ Произошла ошибка при обработке вашего сообщения.\n"
                "Проверьте формат и попробуйте снова:\n"
                "<code>ID_ПОЛЬЗОВАТЕЛЯ ТЕКСТ_СООБЩЕНИЯ</code>"
            )
    
    # Если сообщение от пользователя (не оператора)
    else:
        # Проверка активного чата или состояния поддержки
        is_in_support = (user_id in active_chats) or (current_state and "SupportState" in str(current_state))
        
        # Если пользователь в состоянии чата поддержки
        if is_in_support:
            print(f"DEBUG: Пользователь {user_id} отправил сообщение в чат поддержки: {message.text[:20]}...")
            
            # Если пользователь в списке активных чатов, но состояние не установлено
            if not current_state and user_id in active_chats:
                await state.set_state(SupportState.in_chat)
                print(f"DEBUG: Установлено состояние SupportState.in_chat для пользователя {user_id}")
            
            # Если пользователь не в списке активных чатов, добавляем его
            if user_id not in active_chats:
                active_chats[user_id] = True
                print(f"DEBUG: Пользователь {user_id} добавлен в список активных чатов")
            
            # Пересылаем сообщение оператору
            try:
                await bot.send_message(
                    OPERATOR_CHAT_ID,
                    f"📩 <b>Сообщение от пользователя {user_id}</b>:\n\n{message.text}"
                )
                
                # Отправляем подтверждение пользователю
                await message.answer(
                    "✅ Ваше сообщение отправлено оператору. Ожидайте ответа.",
                    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                        [types.InlineKeyboardButton(text="❌ Завершить чат", callback_data="end_chat")]
                    ])
                )
            except Exception as e:
                logging.error(f"Ошибка при пересылке сообщения оператору: {e}")
                await message.answer(
                    "⚠️ Произошла ошибка при отправке вашего сообщения оператору. Попробуйте еще раз.",
                    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                        [types.InlineKeyboardButton(text="❌ Завершить чат", callback_data="end_chat")],
                        [types.InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_main")]
                    ])
                )

# Обработчик для запуска чата поддержки
async def start_support_chat(callback: types.CallbackQuery, state: FSMContext, bot, OPERATOR_CHAT_ID):
    user_id = callback.from_user.id
    
    try:
        # Добавляем отладочную информацию
        print(f"DEBUG: Получен запрос на техподдержку от пользователя {user_id}")
        
        # Отвечаем на callback
        await callback.answer("Подключаем вас к чату поддержки...")
        
        # Проверяем, активен ли уже чат с этим пользователем
        if user_id in active_chats:
            await callback.message.answer(
                "ℹ️ Вы уже подключены к чату поддержки. Пожалуйста, опишите свой вопрос.",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text="❌ Завершить чат", callback_data=f"end_chat")]
                ])
            )
            return
            
        # Запрашиваем имя пользователя
        await state.set_state(SupportState.waiting_for_name)
        
        # Сохраняем ID сообщения для последующего редактирования
        await state.update_data(last_message_id=callback.message.message_id)
        
        # Запрашиваем имя
        await callback.message.edit_text(
            "👋 <b>Подключение к техподдержке</b>\n\n"
            "Пожалуйста, напишите, как к вам обращаться.\n"
            "Это поможет нашим операторам предоставить вам более персонализированную поддержку.",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="🔙 Отмена", callback_data="back_to_main")]
            ])
        )
        
    except Exception as e:
        logging.error(f"Error in start_support_chat: {e}")
        await callback.message.answer(
            "⚠️ Произошла ошибка при подключении к чату поддержки. Пожалуйста, попробуйте позже.",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_main")]
            ])
        )

# Обработчик получения имени пользователя
async def handle_support_name(message: types.Message, state: FSMContext, bot, OPERATOR_CHAT_ID):
    user_id = message.from_user.id
    user_name = message.text
    
    try:
        # Сохраняем имя пользователя
        await state.update_data(user_support_name=user_name)
        
        # Устанавливаем состояние в чате
        active_chats[user_id] = True
        await state.set_state(SupportState.in_chat)
        print(f"DEBUG: Установлено состояние SupportState.in_chat для пользователя {user_id}")
        
        # Создаем кнопки для чата поддержки
        support_kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="❌ Завершить чат", callback_data="end_chat")],
            [types.InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_main")]
        ])
        
        # Отправляем сообщение пользователю
        await message.answer(
            "👨‍💼 <b>Вы подключены к чату с оператором поддержки.</b>\n\n"
            "Пожалуйста, опишите ваш вопрос или проблему одним сообщением. "
            "Оператор ответит вам в ближайшее время.\n\n"
            "<i>Ваше сообщение будет немедленно передано оператору.</i>",
            reply_markup=support_kb
        )
        
        # Собираем данные о пользователе
        user_info = message.from_user
        username = user_info.username if user_info.username else "отсутствует"
        full_name = user_info.full_name if user_info.full_name else "Не указано"
        phone = user_contacts.get(user_id, "Не предоставлен")
        
        # Уведомляем оператора с расширенной информацией
        await bot.send_message(
            OPERATOR_CHAT_ID,
            f"👤 <b>Новый запрос в техподдержку</b>\n\n"
            f"• ID: <code>{user_id}</code>\n"
            f"• Имя: {user_name}\n"
            f"• Полное имя: {full_name}\n"
            f"• Username: @{username}\n"
            f"• Телефон: {phone}\n\n"
            f"Для ответа используйте формат:\n"
            f"<code>{user_id} Ваше сообщение</code>\n\n"
            f"Для завершения чата: /end {user_id}"
        )
        
    except Exception as e:
        logging.error(f"Error in handle_support_name: {e}")
        await message.answer(
            "⚠️ Произошла ошибка при обработке вашего имени. Пожалуйста, попробуйте позже.",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_main")]
            ])
        )

# Функция для регистрации обработчиков
def register_handlers(dp: Dispatcher, bot: Bot, OPERATOR_CHAT_ID, main_menu_kb):
    print(f"DEBUG: Регистрация обработчиков поддержки, OPERATOR_CHAT_ID={OPERATOR_CHAT_ID}")
    
    # Регистрация обработчика запроса поддержки
    @dp.callback_query(F.data == "support_request")
    async def support_callback_wrapper(callback: types.CallbackQuery, state: FSMContext):
        print(f"DEBUG: Получен callback support_request от {callback.from_user.id}")
        await start_support_chat(callback, state, bot, OPERATOR_CHAT_ID)
    
    # Обработчик для завершения чата с клиентской стороны
    @dp.callback_query(lambda c: c.data == "end_chat")
    async def end_chat_wrapper(callback: types.CallbackQuery, state: FSMContext):
        print(f"DEBUG: Получен callback end_chat от {callback.from_user.id}")
        await end_chat_callback(callback, state, bot, OPERATOR_CHAT_ID)
    
    # Обработчик для принудительной отправки сообщения даже если пользователь не в чате
    @dp.callback_query(lambda c: c.data and c.data.startswith("force_send_"))
    async def force_send_wrapper(callback: types.CallbackQuery, state: FSMContext):
        print(f"DEBUG: Получен callback force_send от {callback.from_user.id}")
        try:
            target_user_id = int(callback.data.split("_")[2])
            # Получаем исходное сообщение оператора
            message_text = callback.message.text.split("\n")[0]  # Берем первую строку с ID пользователя
            parts = message_text.split()
            
            if len(parts) >= 3:  # Проверяем, что есть "Пользователь {id} не находится в активном чате"
                # Запрашиваем новое сообщение
                await callback.message.answer(
                    f"Введите сообщение для пользователя {target_user_id}:\n"
                    f"Формат: {target_user_id} Ваше сообщение"
                )
                
                # Добавляем пользователя в активные чаты
                active_chats[target_user_id] = True
                
                await callback.answer("Готово к отправке. Введите сообщение.")
            else:
                await callback.answer("Не удалось определить ID пользователя.")
                
        except Exception as e:
            logging.error(f"Ошибка в force_send_wrapper: {e}")
            await callback.answer("Произошла ошибка. Попробуйте еще раз.")
    
    # Обработчик для отмены отправки
    @dp.callback_query(lambda c: c.data == "cancel_send")
    async def cancel_send_wrapper(callback: types.CallbackQuery):
        await callback.message.edit_text("✅ Отправка сообщения отменена.")
        await callback.answer()
    
    # Регистрация обработчика для команды завершения чата от оператора
    @dp.message(lambda message: message.chat.id == OPERATOR_CHAT_ID and message.text and message.text.startswith("/end"))
    async def operator_end_chat_wrapper(message: types.Message):
        print(f"DEBUG: Получена команда /end от оператора {message.from_user.id}")
        await operator_end_chat(message, bot)
    
    # Регистрация обработчика для получения контактов
    @dp.message(lambda message: message.contact is not None)
    async def contact_handler_wrapper(message: types.Message):
        print(f"DEBUG: Получен контакт от {message.from_user.id}")
        await handle_contact(message, bot, main_menu_kb)
    
    # Общий обработчик сообщений для чата поддержки (самый низкий приоритет)
    @dp.message()
    async def message_handler_wrapper(message: types.Message, state: FSMContext):
        print(f"DEBUG: Обработка сообщения от {message.from_user.id} в чате {message.chat.id}")
        await handle_messages(message, state, bot, OPERATOR_CHAT_ID) 