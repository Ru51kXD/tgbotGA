from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging
import re

# Определение состояний для проверки баланса карты
class BalanceCheckState(StatesGroup):
    waiting_for_card_number = State()

# Клавиатура для меню подарочных карт
gift_cards_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🛒 Как купить?", callback_data="gift_how_to_buy")],
    [InlineKeyboardButton(text="📖 Как использовать?", callback_data="gift_how_to_use")],
    [InlineKeyboardButton(text="👥 Карты для коллег", callback_data="gift_for_colleagues")],
    [InlineKeyboardButton(text="💳 Узнать баланс карты", callback_data="gift_check_balance")],
    [InlineKeyboardButton(text="🔙 Вернуться назад", callback_data="back_to_main")]
])

# Обработчик кнопки "Подарочные карты"
async def gift_cards_menu(callback: types.CallbackQuery):
    try:
        await callback.answer()
        
        await callback.message.answer(
            "🎁 Подарочные карты Gold Apple\n\n"
            "Выберите интересующий вас раздел:",
            reply_markup=gift_cards_kb
        )
    except Exception as e:
        logging.error(f"Error in gift_cards_menu: {e}")
        try:
            await callback.message.answer(
                "Произошла ошибка. Пожалуйста, попробуйте снова или обратитесь в поддержку.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
                ])
            )
        except Exception as ex:
            logging.error(f"Failed to send error message in gift_cards_menu: {ex}")

# Обработчик кнопки "Как купить?"
async def gift_how_to_buy(callback: types.CallbackQuery):
    try:
        await callback.answer()
        
        await callback.message.answer(
            "🛒 Как купить подарочную карту Gold Apple:\n\n"
            "1. Посетите любой магазин Gold Apple\n"
            "2. Выберите подарочную карту на нужную сумму\n"
            "3. Оплатите карту на кассе\n\n"
            "Или купите электронную подарочную карту на сайте:\n"
            "1. Зайдите на сайт goldapple.ru/giftcard\n"
            "2. Выберите дизайн и сумму карты\n"
            "3. Укажите электронную почту получателя\n"
            "4. Оплатите заказ\n\n"
            "Доступны карты номиналом: 1000₽, 3000₽, 5000₽, 10000₽",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад к подарочным картам", callback_data="gift_cards")],
                [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
            ])
        )
    except Exception as e:
        logging.error(f"Error in gift_how_to_buy: {e}")
        try:
            await callback.message.answer(
                "Произошла ошибка. Пожалуйста, попробуйте снова или обратитесь в поддержку.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
                ])
            )
        except Exception as ex:
            logging.error(f"Failed to send error message in gift_how_to_buy: {ex}")

# Обработчик кнопки "Как использовать?"
async def gift_how_to_use(callback: types.CallbackQuery):
    try:
        await callback.answer()
        
        await callback.message.answer(
            "📖 Как использовать подарочную карту Gold Apple:\n\n"
            "В магазине:\n"
            "1. Предъявите карту на кассе при оплате\n"
            "2. Сумма покупки будет списана с баланса карты\n\n"
            "На сайте:\n"
            "1. Добавьте товары в корзину\n"
            "2. При оформлении заказа выберите способ оплаты 'Подарочной картой'\n"
            "3. Введите номер карты и PIN-код (для физических карт)\n"
            "4. Для электронных карт введите код из письма\n\n"
            "Срок действия карты: 1 год с момента активации",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад к подарочным картам", callback_data="gift_cards")],
                [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
            ])
        )
    except Exception as e:
        logging.error(f"Error in gift_how_to_use: {e}")
        try:
            await callback.message.answer(
                "Произошла ошибка. Пожалуйста, попробуйте снова или обратитесь в поддержку.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
                ])
            )
        except Exception as ex:
            logging.error(f"Failed to send error message in gift_how_to_use: {ex}")

# Обработчик кнопки "Карты для коллег"
async def gift_for_colleagues(callback: types.CallbackQuery):
    try:
        await callback.answer()
        
        await callback.message.answer(
            "👥 Подарочные карты для корпоративных клиентов:\n\n"
            "Преимущества:\n"
            "- Скидки при заказе от 10 карт\n"
            "- Брендирование карт логотипом компании\n"
            "- Возможность доставки по адресу компании\n"
            "- Индивидуальные условия для крупных заказов\n\n"
            "Для заказа корпоративных подарочных карт:\n"
            "1. Напишите на corporate@goldapple.ru\n"
            "2. Укажите количество карт и желаемые номиналы\n"
            "3. Наш менеджер свяжется с вами для уточнения деталей",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад к подарочным картам", callback_data="gift_cards")],
                [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
            ])
        )
    except Exception as e:
        logging.error(f"Error in gift_for_colleagues: {e}")
        try:
            await callback.message.answer(
                "Произошла ошибка. Пожалуйста, попробуйте снова или обратитесь в поддержку.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
                ])
            )
        except Exception as ex:
            logging.error(f"Failed to send error message in gift_for_colleagues: {ex}")

# Обработчик кнопки "Узнать баланс карты"
async def gift_check_balance(callback: types.CallbackQuery):
    try:
        await callback.answer()
        
        balance_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Физическая карта", callback_data="gift_balance_physical")],
            [InlineKeyboardButton(text="💻 Электронная карта", callback_data="gift_balance_digital")],
            [InlineKeyboardButton(text="❓ Проблемы с балансом", callback_data="gift_balance_problem")],
            [InlineKeyboardButton(text="🔙 Назад к подарочным картам", callback_data="gift_cards")]
        ])
        
        await callback.message.answer(
            "💳 Проверка баланса подарочной карты\n\n"
            "Выберите тип вашей подарочной карты:",
            reply_markup=balance_kb
        )
    except Exception as e:
        logging.error(f"Error in gift_check_balance: {e}")
        try:
            await callback.message.answer(
                "Произошла ошибка. Пожалуйста, попробуйте снова или обратитесь в поддержку.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
                ])
            )
        except Exception as ex:
            logging.error(f"Failed to send error message in gift_check_balance: {ex}")

# Обработчик кнопки "Физическая карта"
async def gift_balance_physical(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        
        # Устанавливаем состояние ожидания номера карты
        await state.set_state(BalanceCheckState.waiting_for_card_number)
        
        await callback.message.answer(
            "Пожалуйста, введите номер вашей физической подарочной карты в формате XXXX-XXXX-XXXX-XXXX:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Отмена", callback_data="gift_cards")]
            ])
        )
    except Exception as e:
        logging.error(f"Error in gift_balance_physical: {e}")
        try:
            await callback.message.answer(
                "Произошла ошибка. Пожалуйста, попробуйте снова или обратитесь в поддержку.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
                ])
            )
        except Exception as ex:
            logging.error(f"Failed to send error message in gift_balance_physical: {ex}")

# Обработчик ввода номера карты
async def process_card_number(message: types.Message, state: FSMContext):
    # Шаблон для проверки формата номера карты
    card_pattern = r"^\d{4}-\d{4}-\d{4}-\d{4}$"
    
    try:
        if re.match(card_pattern, message.text.strip()):
            # Получаем номер карты
            card_number = message.text.strip()
            
            # Сбрасываем состояние
            await state.clear()
            
            # Отправляем информацию о балансе карты (здесь будет запрос к API)
            await message.answer(
                f"💳 Информация о карте {card_number}:\n\n"
                f"Текущий баланс: 3500₽\n"
                f"Срок действия: до 31.12.2024\n\n"
                f"Для использования карты предъявите её на кассе или введите номер при оформлении заказа на сайте.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад к подарочным картам", callback_data="gift_cards")],
                    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
                ])
            )
        else:
            # Сообщаем о неверном формате
            await message.answer(
                "❌ Неверный формат номера карты.\n\nПожалуйста, введите номер карты в формате XXXX-XXXX-XXXX-XXXX.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="gift_balance_physical")],
                    [InlineKeyboardButton(text="🔙 Назад к подарочным картам", callback_data="gift_cards")]
                ])
            )
    except Exception as e:
        logging.error(f"Error in process_card_number: {e}")
        try:
            await message.answer(
                "Произошла ошибка при обработке номера карты. Пожалуйста, попробуйте снова или обратитесь в поддержку.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
                ])
            )
        except Exception as ex:
            logging.error(f"Failed to send error message in process_card_number: {ex}")

# Обработчик кнопки "Электронная карта"
async def gift_balance_digital(callback: types.CallbackQuery):
    try:
        await callback.answer()
        
        await callback.message.answer(
            "💻 Баланс электронной подарочной карты\n\n"
            "Для проверки баланса электронной подарочной карты:\n"
            "1. Найдите письмо с электронной картой в вашей почте\n"
            "2. Перейдите по ссылке из письма\n"
            "3. Введите код карты на странице проверки баланса\n\n"
            "Также вы можете проверить баланс на сайте goldapple.ru/giftcard/balance, введя код карты.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад к подарочным картам", callback_data="gift_cards")],
                [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
            ])
        )
    except Exception as e:
        logging.error(f"Error in gift_balance_digital: {e}")
        try:
            await callback.message.answer(
                "Произошла ошибка. Пожалуйста, попробуйте снова или обратитесь в поддержку.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
                ])
            )
        except Exception as ex:
            logging.error(f"Failed to send error message in gift_balance_digital: {ex}")

# Обработчик кнопки "Проблемы с балансом"
async def gift_balance_problem(callback: types.CallbackQuery):
    try:
        await callback.answer()
        
        await callback.message.answer(
            "❓ Проблемы с балансом подарочной карты\n\n"
            "Возможные проблемы:\n"
            "1. Карта неактивна или просрочена\n"
            "2. Неверно введен номер или PIN-код\n"
            "3. Технические проблемы с системой\n\n"
            "Для решения проблемы рекомендуем:\n"
            "- Проверить правильность ввода данных\n"
            "- Убедиться, что карта активирована\n"
            "- Проверить срок действия карты\n\n"
            "Если проблема не решена, обратитесь в службу поддержки по телефону 8-800-555-33-22 "
            "или на email support@goldapple.ru",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад к подарочным картам", callback_data="gift_cards")],
                [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
            ])
        )
    except Exception as e:
        logging.error(f"Error in gift_balance_problem: {e}")
        try:
            await callback.message.answer(
                "Произошла ошибка. Пожалуйста, попробуйте снова или обратитесь в поддержку.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_to_main")]
                ])
            )
        except Exception as ex:
            logging.error(f"Failed to send error message in gift_balance_problem: {ex}")

# Функция для регистрации обработчиков в диспетчере
def register_handlers(dp):
    dp.callback_query(lambda c: c.data == "gift_cards")(gift_cards_menu)
    dp.callback_query(lambda c: c.data == "gift_how_to_buy")(gift_how_to_buy)
    dp.callback_query(lambda c: c.data == "gift_how_to_use")(gift_how_to_use)
    dp.callback_query(lambda c: c.data == "gift_for_colleagues")(gift_for_colleagues)
    dp.callback_query(lambda c: c.data == "gift_check_balance")(gift_check_balance)
    dp.callback_query(lambda c: c.data == "gift_balance_physical")(gift_balance_physical)
    dp.message(BalanceCheckState.waiting_for_card_number)(process_card_number)
    dp.callback_query(lambda c: c.data == "gift_balance_digital")(gift_balance_digital)
    dp.callback_query(lambda c: c.data == "gift_balance_problem")(gift_balance_problem) 