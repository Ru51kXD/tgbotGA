import logging
import json
import sqlite3
import random
from datetime import datetime
import pandas as pd
from aiogram import types, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio

# Состояния для рекомендаций
class RecommendationState(StatesGroup):
    choosing_category = State()
    waiting_for_criteria = State()
    choosing_criteria = State()
    waiting_for_operator_reply = State()

# Временное хранилище данных пользователей
user_storage = {}

# Словарь для хранения запросов пользователей и ответов операторов
recommendation_requests = {}

# ID чата операторов (будет заполнено из main.py при регистрации)
OPERATOR_CHAT_ID = None

def init_db():
    """Инициализировать базу данных рекомендаций, если она не существует"""
    try:
        import os
        # Проверяем наличие файла БД
        db_exists = os.path.exists('recommendations.db')
        
        # Подключаемся к БД
        conn = sqlite3.connect('recommendations.db')
        cursor = conn.cursor()
        
        # Проверяем структуру существующей таблицы, если БД уже существует
        if db_exists:
            cursor.execute("PRAGMA table_info(products)")
            columns = [col[1] for col in cursor.fetchall()]
            print(f"Существующие столбцы таблицы products: {columns}")
            
            # Если таблица существует, но нет столбца attributes, удаляем и пересоздаем
            if 'attributes' not in columns:
                print("Столбец attributes отсутствует. Пересоздаем таблицу...")
                cursor.execute('DROP TABLE IF EXISTS products')
                db_exists = False
        
        # Создаем таблицу, если она не существует
        if not db_exists:
            print("Создаем таблицу products...")
            cursor.execute('''CREATE TABLE IF NOT EXISTS products
                          (id INTEGER PRIMARY KEY,
                          name TEXT,
                          category TEXT,
                          price REAL,
                          rating REAL,
                          attributes TEXT)''')
            
            # Тестовые данные с расширенными атрибутами
            products = [
                (1, 'Тушь для ресниц Volume', 'mascara', 1500, 4.8, 
                 json.dumps({
                     "effect": ["volume", "length"],
                     "type": "waterproof",
                     "brush": "silicone",
                     "price": "medium"
                 })),
                (2, 'Помада матовая Ruby', 'lipstick', 2300, 4.5,
                 json.dumps({
                     "type": "matte",
                     "finish": "velvet",
                     "longevity": "long",
                     "color": "red",
                     "price": "premium"
                 })),
                (3, 'Парфюм Rose Garden', 'perfume', 4500, 4.9,
                 json.dumps({
                     "type": ["floral", "sweet"],
                     "intensity": "medium",
                     "longevity": "long",
                     "season": ["spring", "summer"],
                     "price": "medium"
                 })),
                (4, 'Помада глянцевая Pearl', 'lipstick', 1800, 4.7,
                 json.dumps({
                     "type": "glossy",
                     "finish": "shimmer",
                     "longevity": "medium",
                     "color": "nude",
                     "price": "medium"
                 })),
                (5, 'Тушь для ресниц Dramatic', 'mascara', 2500, 4.6,
                 json.dumps({
                     "effect": ["volume", "curl"],
                     "type": "waterproof",
                     "brush": "curved",
                     "price": "premium"
                 })),
                (6, 'Тушь для ресниц Natural Look', 'mascara', 900, 4.3,
                 json.dumps({
                     "effect": ["separation", "definition"],
                     "type": "regular",
                     "brush": "traditional",
                     "price": "budget"
                 })),
                (7, 'Помада жидкая Velvet', 'lipstick', 1700, 4.8,
                 json.dumps({
                     "type": "liquid",
                     "finish": "velvet",
                     "longevity": "long",
                     "color": "berry",
                     "price": "medium"
                 })),
                (8, 'Парфюм Citrus Fresh', 'perfume', 3500, 4.3,
                 json.dumps({
                     "type": ["citrus", "fresh"],
                     "intensity": "light",
                     "longevity": "medium",
                     "season": ["summer"],
                     "price": "medium"
                 })),
                (9, 'Тушь для ресниц Natural', 'mascara', 900, 4.2,
                 json.dumps({
                     "effect": ["length", "separation"],
                     "type": "regular",
                     "brush": "natural",
                     "price": "budget"
                 })),
                (10, 'Парфюм Tropical Night', 'perfume', 5500, 4.7,
                 json.dumps({
                     "type": ["tropical", "spicy"],
                     "intensity": "strong",
                     "longevity": "long",
                     "season": ["summer", "autumn"],
                     "price": "premium"
                 }))
            ]
            
            # Вставляем данные
            cursor.executemany('INSERT INTO products VALUES (?,?,?,?,?,?)', products)
            conn.commit()
            print(f"Добавлено {len(products)} товаров в базу данных")
        
        # Проверяем содержимое таблицы
        cursor.execute("SELECT COUNT(*) FROM products")
        row_count = cursor.fetchone()[0]
        print(f"Количество товаров в базе данных: {row_count}")
        
        conn.close()
    except Exception as e:
        logging.error(f"Ошибка инициализации базы данных: {e}")
        print(f"Ошибка при инициализации БД: {e}")
        # Если возникла ошибка, создаем новую БД
        try:
            import os
            if os.path.exists('recommendations.db'):
                os.remove('recommendations.db')
            
            # Создаем новую БД
            conn = sqlite3.connect('recommendations.db')
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS products
                          (id INTEGER PRIMARY KEY,
                          name TEXT,
                          category TEXT,
                          price REAL,
                          rating REAL,
                          attributes TEXT)''')
            conn.commit()
            conn.close()
            print("База данных пересоздана после ошибки")
        except Exception as inner_e:
            logging.error(f"Критическая ошибка при пересоздании базы данных: {inner_e}")
            print(f"Критическая ошибка: {inner_e}")

def get_category_criteria_keyboard(category: str, selected_criteria: list = None) -> InlineKeyboardMarkup:
    """Создает клавиатуру с критериями для выбранной категории"""
    if selected_criteria is None:
        selected_criteria = []
    
    # Получаем критерии для выбранной категории
    category_data = getattr(ProductCategories, category.upper(), {})
    
    buttons = []
    # Добавляем смайлики для разных групп критериев
    emoji_map = {
        "type": "🏷️",
        "effect": "✨",
        "finish": "🎨",
        "longevity": "⏱️",
        "color": "🌈",
        "brush": "🖌️",
        "price": "💰",
        "intensity": "💪",
        "season": "🍃"
    }
    
    # Для каждой группы критериев создаем заголовок и кнопки
    for criteria_group, criteria_values in category_data.items():
        # Заголовок группы критериев с эмодзи
        group_emoji = emoji_map.get(criteria_group, "📋")
        buttons.append([InlineKeyboardButton(
            text=f"{group_emoji} {criteria_group.title()}",
            callback_data=f"header_{criteria_group}"
        )])
        
        # Кнопки отдельных критериев
        criteria_buttons = []
        for criteria_id, criteria_name in criteria_values.items():
            # Выбран ли этот критерий
            is_selected = f"{criteria_group}_{criteria_id}" in selected_criteria
            marker = "✅ " if is_selected else "⬜ "
            criteria_emoji = ""
            
            # Добавляем тематические эмодзи для критериев
            if criteria_group == "type":
                if criteria_id == "matte": criteria_emoji = "🎭 "
                elif criteria_id == "glossy": criteria_emoji = "✨ "
                elif criteria_id == "liquid": criteria_emoji = "💧 "
                elif criteria_id == "satin": criteria_emoji = "🧵 "
                elif criteria_id == "waterproof": criteria_emoji = "💦 "
                elif criteria_id == "regular": criteria_emoji = "📏 "
                elif criteria_id == "floral": criteria_emoji = "🌸 "
                elif criteria_id == "citrus": criteria_emoji = "🍊 "
                elif criteria_id == "woody": criteria_emoji = "🌲 "
                elif criteria_id == "spicy": criteria_emoji = "🌶️ "
                elif criteria_id == "sweet": criteria_emoji = "🍬 "
                elif criteria_id == "fresh": criteria_emoji = "❄️ "
            elif criteria_group == "effect":
                if criteria_id == "volume": criteria_emoji = "🔝 "
                elif criteria_id == "length": criteria_emoji = "📏 "
                elif criteria_id == "curl": criteria_emoji = "↪️ "
                elif criteria_id == "separation": criteria_emoji = "🔀 "
            elif criteria_group == "finish":
                if criteria_id == "velvet": criteria_emoji = "🧸 "
                elif criteria_id == "shimmer": criteria_emoji = "✨ "
                elif criteria_id == "cream": criteria_emoji = "🍦 "
            elif criteria_group == "longevity":
                if criteria_id == "short": criteria_emoji = "⏱️ "
                elif criteria_id == "medium": criteria_emoji = "⏲️ "
                elif criteria_id == "long": criteria_emoji = "⏰ "
            elif criteria_group == "color":
                if criteria_id == "nude": criteria_emoji = "🤎 "
                elif criteria_id == "red": criteria_emoji = "❤️ "
                elif criteria_id == "berry": criteria_emoji = "🍓 "
                elif criteria_id == "pink": criteria_emoji = "💗 "
            elif criteria_group == "brush":
                if criteria_id == "silicone": criteria_emoji = "🔬 "
                elif criteria_id == "curved": criteria_emoji = "↪️ "
                elif criteria_id == "traditional": criteria_emoji = "🖌️ "
            elif criteria_group == "price":
                if criteria_id == "budget": criteria_emoji = "💸 "
                elif criteria_id == "medium": criteria_emoji = "💵 "
                elif criteria_id == "premium": criteria_emoji = "💎 "
            elif criteria_group == "intensity":
                if criteria_id == "light": criteria_emoji = "🕯️ "
                elif criteria_id == "medium": criteria_emoji = "💡 "
                elif criteria_id == "strong": criteria_emoji = "🔆 "
            elif criteria_group == "season":
                if criteria_id == "spring": criteria_emoji = "🌱 "
                elif criteria_id == "summer": criteria_emoji = "☀️ "
                elif criteria_id == "autumn": criteria_emoji = "🍂 "
                elif criteria_id == "winter": criteria_emoji = "❄️ "
                
            criteria_buttons.append(InlineKeyboardButton(
                text=f"{marker}{criteria_emoji}{criteria_name}",
                callback_data=f"criteria_{category}_{criteria_group}_{criteria_id}"
            ))
            
        # Группируем кнопки критериев по 2 в ряд
        row = []
        for button in criteria_buttons:
            row.append(button)
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:  # Добавляем оставшиеся кнопки
            buttons.append(row)
    
    # Добавляем кнопки управления
    buttons.extend([
        [InlineKeyboardButton(text="✨ Показать рекомендации", callback_data=f"show_recommendations_{category}")],
        [InlineKeyboardButton(text="🔄 Сбросить", callback_data=f"reset_criteria_{category}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_categories")]
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def get_user_data(user_id: int) -> dict:
    """Возвращает данные пользователя из временного хранилища"""
    return user_storage.get(user_id, {
        'view_history': [],
        'purchase_history': [],
        'preferences': {}
    })

# Класс с категориями товаров и их критериями
class ProductCategories:
    # Категория туши
    MASCARA = {
        "effect": {
            "volume": "Объем ресниц",
            "length": "Удлинение ресниц",
            "curl": "Подкручивание ресниц",
            "separation": "Разделение ресниц"
        },
        "type": {
            "waterproof": "Водостойкая",
            "regular": "Обычная",
            "fibrous": "С фибрами"
        },
        "brush": {
            "silicone": "Силиконовая щеточка",
            "curved": "Изогнутая щеточка",
            "traditional": "Классическая щеточка"
        },
        "price": {
            "budget": "Бюджетная (до 1000р)",
            "medium": "Средняя (1000-2000р)",
            "premium": "Премиум (от 2000р)"
        }
    }

    # Категория помады
    LIPSTICK = {
        "type": {
            "matte": "Матовая",
            "glossy": "Глянцевая",
            "liquid": "Жидкая",
            "satin": "Сатиновая"
        },
        "finish": {
            "velvet": "Бархатный финиш",
            "shimmer": "С шиммером",
            "cream": "Кремовый финиш"
        },
        "longevity": {
            "short": "Обычная стойкость",
            "medium": "Средняя стойкость",
            "long": "Долгая стойкость"
        },
        "color": {
            "nude": "Нюдовые оттенки",
            "red": "Красные оттенки",
            "berry": "Ягодные оттенки",
            "pink": "Розовые оттенки"
        }
    }

    # Категория парфюма
    PERFUME = {
        "type": {
            "floral": "Цветочные",
            "citrus": "Цитрусовые",
            "woody": "Древесные",
            "spicy": "Пряные",
            "sweet": "Сладкие",
            "fresh": "Свежие"
        },
        "intensity": {
            "light": "Легкий аромат",
            "medium": "Средняя интенсивность",
            "strong": "Насыщенный аромат"
        },
        "longevity": {
            "short": "Непродолжительный",
            "medium": "Средняя стойкость",
            "long": "Стойкий"
        },
        "season": {
            "spring": "Весенний",
            "summer": "Летний",
            "autumn": "Осенний",
            "winter": "Зимний"
        }
    }

# Рекомендательная система
class RecommendationSystem:
    def __init__(self):
        self.last_update = datetime.now()
        self.products = self._load_from_db()
        
    def _load_from_db(self):
        """Загрузка данных из БД"""
        conn = sqlite3.connect('recommendations.db')
        df = pd.read_sql_query('SELECT * FROM products', conn)
        conn.close()
        return df

    def _refresh_data(self):
        """Обновление данных каждые 2 часа"""
        if (datetime.now() - self.last_update).seconds > 7200:
            self.products = self._load_from_db()
            self.last_update = datetime.now()

    def get_recommendations(self, user_data: dict) -> list:
        self._refresh_data()
        strategies = [
            self._popularity_based,
            self._price_based,
            self._category_based,
            self._random_mix
        ]
        strategy = random.choice(strategies)
        return strategy(user_data)

    def _popularity_based(self, user_data) -> list:
        """Топ товаров по рейтингу"""
        return self.products.sort_values('rating', ascending=False).head(3).to_dict('records')

    def _price_based(self, user_data) -> list:
        """Подбор по ценовому диапазону"""
        avg_price = user_data.get('avg_purchase_price', 2000)
        return self.products[
            (self.products['price'] > avg_price * 0.8) &
            (self.products['price'] < avg_price * 1.2)
        ].sample(3, random_state=random.randint(0, 1000)).to_dict('records')

    def _category_based(self, user_data) -> list:
        """Подбор по предпочитаемым категориям"""
        preferred_categories = user_data.get('preferred_categories', ['mascara', 'lipstick', 'perfume'])
        result = []
        
        for category in preferred_categories:
            category_products = self.products[self.products['category'] == category]
            if not category_products.empty:
                result.append(category_products.sample(1, random_state=random.randint(0, 1000)).iloc[0].to_dict())
                
        # Если не набрали 3 товара, добавляем случайные
        while len(result) < 3 and len(self.products) > len(result):
            random_product = self.products.sample(1, random_state=random.randint(0, 1000)).iloc[0].to_dict()
            if random_product not in result:
                result.append(random_product)
                
        return result

    def _random_mix(self, user_data) -> list:
        """Случайная выборка товаров"""
        return self.products.sample(3, random_state=random.randint(0, 1000)).to_dict('records')

# Расширенная система рекомендаций
class AdvancedRecommendationSystem:
    def get_recommendations(self, category: str, criteria: list) -> list:
        # Добавим вывод для отладки
        print(f"Поиск рекомендаций для категории: {category}, критерии: {criteria}")
        conn = sqlite3.connect('recommendations.db')
        cursor = conn.cursor()
        
        try:
            # Проверяем, есть ли столбец attributes в таблице
            cursor.execute("PRAGMA table_info(products)")
            columns = [col[1] for col in cursor.fetchall()]
            print(f"Столбцы таблицы products: {columns}")
            
            # Базовый запрос
            query = f"SELECT * FROM products WHERE category = ?"
            params = [category]
            
            # Если есть столбец attributes и заданы критерии, добавляем фильтры
            if 'attributes' in columns and criteria:
                query += " AND " + " AND ".join(["attributes LIKE ?" for _ in criteria])
                params += [f'%{c}%' for c in criteria]
            
            # Выполняем запрос
            print(f"SQL запрос: {query}, параметры: {params}")
            cursor.execute(query, params)
            results = cursor.fetchall()
            print(f"Найдено результатов: {len(results)}")
            
            return self._parse_results(results, columns)
        except Exception as e:
            logging.error(f"Ошибка при получении рекомендаций: {e}")
            print(f"Ошибка SQL: {e}")
            return []
        finally:
            conn.close()

    def _parse_results(self, results, columns):
        try:
            parsed_results = []
            # Индекс столбца attributes
            attributes_index = columns.index('attributes') if 'attributes' in columns else None
            
            for row in results:
                product = {
                    'id': row[0],
                    'name': row[1],
                    'category': row[2],
                    'price': row[3]
                }
                
                # Добавляем атрибуты, если столбец существует
                if attributes_index is not None and len(row) > attributes_index:
                    try:
                        product['attributes'] = json.loads(row[attributes_index])
                    except (json.JSONDecodeError, TypeError) as e:
                        logging.error(f"Ошибка парсинга JSON для товара {row[0]}: {e}")
                        product['attributes'] = {}
                else:
                    product['attributes'] = {}
                
                parsed_results.append(product)
            
            return parsed_results
        except Exception as e:
            logging.error(f"Ошибка при парсинге результатов: {e}")
            return []

# Обработчики для рекомендаций
async def start_recommendations(callback: types.CallbackQuery, state: FSMContext = None):
    try:
        # Отвечаем на callback
        await callback.answer()
        
        # Если есть состояние, сбрасываем его
        if state:
            await state.clear()
        
        # Создаем клавиатуру с категориями товаров
        categories_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💄 Помада", callback_data="category_lipstick")],
            [InlineKeyboardButton(text="👁️ Тушь для ресниц", callback_data="category_mascara")],
            [InlineKeyboardButton(text="🧴 Парфюм", callback_data="category_perfume")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
        ])
        
        # Отправляем сообщение с выбором категорий
        await callback.message.edit_text(
            "🔍 *Персональные рекомендации*\n\n"
            "Выберите категорию товаров, и мы подберем для вас лучшие варианты!",
            parse_mode="Markdown",
            reply_markup=categories_kb
        )
    except Exception as e:
        logging.error(f"Error in start_recommendations: {e}")
        await callback.message.answer(
            "😞 Произошла ошибка. Пожалуйста, попробуйте позже.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_main")]
            ])
        )

async def select_category(callback: types.CallbackQuery, state: FSMContext):
    try:
        # Отвечаем на callback
        await callback.answer()
        
        # Получаем выбранную категорию
        category = callback.data.split("_")[1]
        
        # Отладочный вывод для диагностики
        print(f"DEBUG: select_category - пользователь {callback.from_user.id}, выбрана категория {category}")
        
        # Получаем имя пользователя или ID, если имя отсутствует
        user_tag = f"@{callback.from_user.username}" if callback.from_user.username else f"ID: {callback.from_user.id}"
        user_name = callback.from_user.full_name
        
        # Сохраняем в состоянии выбранную категорию
        await state.update_data(selected_category=category)
        
        # Получаем и отправляем клавиатуру с критериями выбранной категории
        message = await callback.message.edit_text(
            f"✨ *Выберите критерии для {get_category_name(category)}*\n\n"
            "Отметьте важные для вас параметры и нажмите 'Показать рекомендации':",
            parse_mode="Markdown",
            reply_markup=get_category_criteria_keyboard(category)
        )
        
        # Сохраняем ID сообщения для будущего использования
        await state.update_data(recommendation_message_id=message.message_id)
        
        # Сохраняем информацию о запросе в словаре
        recommendation_requests[callback.from_user.id] = {
            "category": category,
            "message_id": message.message_id,
            "user_tag": user_tag,
            "user_name": user_name
        }
        
        print(f"DEBUG: Сохранили данные в recommendation_requests: {recommendation_requests[callback.from_user.id]}")
        
        # Устанавливаем состояние выбора критериев
        await state.set_state(RecommendationState.choosing_criteria)
    except Exception as e:
        logging.error(f"Error in select_category: {e}")
        print(f"DEBUG: Ошибка в select_category: {e}")
        await callback.message.answer(
            "😞 Произошла ошибка. Пожалуйста, попробуйте позже.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_main")]
            ])
        )

async def toggle_criteria(callback: types.CallbackQuery, state: FSMContext):
    try:
        # Отвечаем на callback, чтобы убрать часы загрузки
        await callback.answer()
        
        # Получаем данные о выбранной категории и критериях
        parts = callback.data.split("_")
        category = parts[1]
        criteria_group = parts[2]
        criteria_id = parts[3]
        criteria_key = f"{criteria_group}_{criteria_id}"
        
        # Получаем текущие данные состояния
        data = await state.get_data()
        selected_criteria = data.get("selected_criteria", [])
        
        # Отладочный вывод перед изменением
        print(f"DEBUG: Выбранные критерии ДО изменения: {selected_criteria}")
        
        # Переключаем статус критерия (добавляем или удаляем)
        if criteria_key in selected_criteria:
            selected_criteria.remove(criteria_key)
        else:
            selected_criteria.append(criteria_key)
        
        # Обновляем данные в состоянии (ВАЖНО: создаем новый список)
        await state.update_data(selected_criteria=selected_criteria.copy())
        
        # Отладочный вывод после изменения
        print(f"DEBUG: Выбранные критерии ПОСЛЕ изменения: {selected_criteria}")
        
        # Обновляем сообщение с заголовком и клавиатурой
        try:
            await callback.message.edit_text(
                f"✨ *Выберите критерии для {get_category_name(category)}*\n\n"
                "Отметьте важные для вас параметры и нажмите 'Показать рекомендации':",
                parse_mode="Markdown",
                reply_markup=get_category_criteria_keyboard(category, selected_criteria.copy())
            )
        except Exception as e:
            # Если не удалось обновить всё сообщение, пробуем обновить только клавиатуру
            logging.error(f"Ошибка при обновлении сообщения: {e}")
            await callback.message.edit_reply_markup(
                reply_markup=get_category_criteria_keyboard(category, selected_criteria.copy())
            )
        
    except Exception as e:
        logging.error(f"Error in toggle_criteria: {e}")
        # Тихо обрабатываем ошибку, без отправки сообщения

async def reset_criteria(callback: types.CallbackQuery, state: FSMContext):
    try:
        # Отвечаем на callback
        await callback.answer("Критерии сброшены")
        
        # Получаем категорию из callback данных
        category = callback.data.split("_")[2]
        
        # Сбрасываем выбранные критерии в состоянии
        await state.update_data(selected_criteria=[])
        
        # Обновляем всё сообщение с заголовком
        try:
            await callback.message.edit_text(
                f"✨ *Выберите критерии для {get_category_name(category)}*\n\n"
                "Отметьте важные для вас параметры и нажмите 'Показать рекомендации':",
                parse_mode="Markdown",
                reply_markup=get_category_criteria_keyboard(category, [])
            )
        except Exception as e:
            logging.error(f"Ошибка при обновлении сообщения: {e}")
            # Если не удалось обновить всё сообщение, пробуем обновить только клавиатуру
            await callback.message.edit_reply_markup(
                reply_markup=get_category_criteria_keyboard(category, [])
            )
        
    except Exception as e:
        logging.error(f"Error in reset_criteria: {e}")
        # Тихо обрабатываем ошибку, без отправки сообщения

async def show_recommendations(callback: types.CallbackQuery, state: FSMContext):
    try:
        # Отвечаем на callback
        await callback.answer("Подбираем рекомендации...")
        
        # Получаем данные из состояния
        data = await state.get_data()
        category = callback.data.split("_")[2]
        selected_criteria = data.get("selected_criteria", [])
        
        # Отладочный вывод для диагностики
        print(f"DEBUG: Выбраны критерии перед отправкой: {selected_criteria}")
        
        # Отправляем пользователю сообщение о том, что подбираем рекомендации
        waiting_message = await callback.message.edit_text(
            "⏳ *Наши консультанты подбирают для вас лучшие товары*\n\n"
            "Это займет немного времени. Мы учтем все ваши пожелания и подберем идеальные варианты.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Изменить критерии", callback_data=f"category_{category}")],
                [InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_main")]
            ])
        )
        
        # Сохраняем ID сообщения и пользователя
        user_id = callback.from_user.id
        message_id = waiting_message.message_id
        
        # Получаем информацию о пользователе для отправки оператору
        user_info = callback.from_user
        username = user_info.username if user_info.username else "отсутствует"
        full_name = user_info.full_name
        
        # Формируем текст критериев для оператора
        criteria_text = ""
        for criteria_key in selected_criteria:
            parts = criteria_key.split('_')
            if len(parts) == 2:
                group, value = parts
                # Получаем текстовое описание критерия
                category_data = getattr(ProductCategories, category.upper(), {})
                if group in category_data and value in category_data[group]:
                    criteria_description = category_data[group][value]
                    criteria_text += f"- {group.title()}: {criteria_description}\n"
        
        if not criteria_text:
            criteria_text = "Критерии не выбраны"
        
        # Формируем сообщение для операторов с username пользователя
        operator_message = (
            f"🔔 *Новый запрос на рекомендации*\n\n"
            f"От пользователя: {full_name} (ID: {user_id})\n"
            f"Username: @{username}\n"
            f"Категория: *{get_category_name(category)}*\n\n"
            f"Выбранные критерии:\n{criteria_text}\n\n"
            f"Для отправки ссылки пользователю используйте команду:\n"
            f"`/send_link {user_id} [ссылка на товар]`"
        )
        
        # Отправляем сообщение в чат операторов
        from main import bot
        
        # Отправляем запрос оператору
        try:
            await bot.send_message(
                chat_id=OPERATOR_CHAT_ID,
                text=operator_message,
                parse_mode="Markdown"
            )
            
            # Сохраняем информацию о запросе
            recommendation_requests[user_id] = {
                "message_id": message_id,
                "category": category,
                "criteria": selected_criteria,
                "waiting_since": asyncio.get_event_loop().time()
            }
            
            # Устанавливаем состояние ожидания ответа от оператора
            await state.set_state(RecommendationState.waiting_for_operator_reply)
            await state.update_data(
                waiting_message_id=message_id,
                category=category,
                selected_criteria=selected_criteria
            )
            
        except Exception as e:
            logging.error(f"Ошибка при отправке запроса оператору: {e}")
            # Если не удалось отправить запрос оператору, используем автоматические рекомендации
            advanced_system = AdvancedRecommendationSystem()
            recommendations = advanced_system.get_recommendations(category, selected_criteria)
            
            # Отправляем автоматические рекомендации
            await send_auto_recommendations(callback.message, category, recommendations)
            await state.clear()
        
    except Exception as e:
        logging.error(f"Error in show_recommendations: {e}")
        await callback.message.answer(
            "😞 Произошла ошибка при подборе рекомендаций. Пожалуйста, попробуйте позже.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_main")]
            ])
        )

async def send_auto_recommendations(message, category, recommendations):
    """Отправляет автоматические рекомендации, если оператор недоступен"""
    try:
        # Если рекомендаций нет, сообщаем об этом
        if not recommendations:
            await message.edit_text(
                "😔 К сожалению, по вашим критериям не найдено товаров.\n\n"
                "Попробуйте изменить критерии поиска или выбрать другую категорию.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад к критериям", callback_data=f"category_{category}")],
                    [InlineKeyboardButton(text="🔙 К категориям", callback_data="recommend_products")],
                    [InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_main")]
                ])
            )
            return
        
        # Формируем текст с рекомендациями
        text = "✨ *Вот что мы вам рекомендуем:*\n\n"
        
        for i, product in enumerate(recommendations, 1):
            text += f"*{i}. {product['name']}*\n"
            text += f"💰 Цена: {product['price']} руб.\n"
            
            # Добавляем атрибуты товара
            if 'attributes' in product:
                for attr_type, attr_value in product['attributes'].items():
                    if isinstance(attr_value, list):
                        attr_value = ", ".join(attr_value)
                    text += f"- {attr_type.capitalize()}: {attr_value}\n"
            
            text += "\n"
        
        # Создаем клавиатуру для действий после рекомендаций
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Подобрать ещё", callback_data=f"category_{category}")],
            [InlineKeyboardButton(text="📝 Оформить заказ", callback_data="order")],
            [InlineKeyboardButton(text="🔙 К категориям", callback_data="recommend_products")],
            [InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_main")]
        ])
        
        # Отправляем сообщение с рекомендациями
        await message.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при отправке автоматических рекомендаций: {e}")

async def test_send_link(message: types.Message):
    """Тестовый обработчик команды /send_link для отладки проблем с отправкой ссылки пользователю"""
    try:
        # Отладочные сообщения (только в консоль)
        print(f"DEBUG: test_send_link получил сообщение. ID чата: {message.chat.id}, Текст: {message.text}")
        logging.info(f"test_send_link получил сообщение: {message.text}")
        
        # Проверка формата команды
        parts = message.text.split(' ', 2)
        if len(parts) < 3:
            await message.reply(
                "❌ Неверный формат команды.\n"
                "Используйте: `/send_link USER_ID ССЫЛКА [ОПИСАНИЕ]`",
                parse_mode="Markdown"
            )
            return
        
        # Извлечение данных
        try:
            user_id = int(parts[1])
            link = parts[2].split(' ')[0]
            description = ""
            if len(parts[2].split(' ')) > 1:
                description = ' '.join(parts[2].split(' ')[1:])
            
            # Вывод информации для отладки
            print(f"DEBUG: Отправка сообщения пользователю {user_id} с ссылкой {link}")
            
            # Импорт бота
            from main import bot
            
            # Создание клавиатуры
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🌐 Перейти по ссылке", url=link)],
                [InlineKeyboardButton(text="🔍 Подобрать другие товары", callback_data="recommend_products")],
                [InlineKeyboardButton(text="📝 Оформить заказ", callback_data="order")],
                [InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_main")]
            ])
            
            # Текст сообщения
            text = (
                "✨ *Наш консультант подобрал для вас идеальный вариант:*\n\n"
                f"[Нажмите здесь, чтобы посмотреть товар]({link})\n\n"
            )
            
            if description:
                text += f"💬 *Комментарий консультанта:*\n{description}\n\n"
            
            text += "Вы можете перейти по ссылке для просмотра товара или выбрать другой вариант."
            
            # Отправка сообщения пользователю
            sent_message = await bot.send_message(
                chat_id=user_id,
                text=text,
                parse_mode="Markdown",
                reply_markup=keyboard,
                disable_web_page_preview=False
            )
            
            print(f"DEBUG: Сообщение успешно отправлено. ID сообщения: {sent_message.message_id}")
            
            # Отправка подтверждения
            await message.reply(
                f"✅ Ссылка успешно отправлена пользователю {user_id}",
                parse_mode="Markdown"
            )
            
        except ValueError:
            await message.reply(
                "❌ Неверный формат ID пользователя. Используйте числовой ID.",
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"DEBUG: Ошибка при отправке ссылки: {e}")
            logging.error(f"Ошибка при отправке ссылки: {e}")
            await message.reply(
                f"❌ Ошибка при отправке: {e}",
                parse_mode="Markdown"
            )
    except Exception as e:
        print(f"DEBUG: Общая ошибка в обработчике: {e}")
        logging.error(f"Общая ошибка в обработчике: {e}")
        await message.reply(
            f"❌ Общая ошибка обработчика: {e}",
            parse_mode="Markdown"
        )

# Добавим тестовый обработчик сразу после существующего test_send_link
async def send_link_test(message: types.Message):
    """Сверхпростой тестовый обработчик для отладки отправки сообщений"""
    try:
        print(f"DEBUG: [send_link_test] Получено сообщение: {message.text}")
        
        # Разбор команды
        parts = message.text.split(' ', 2)
        if len(parts) < 3:
            await message.reply("❌ Используйте: /send_link_test ID ССЫЛКА")
            return
        
        # Извлечение данных
        user_id = parts[1]
        link = parts[2]
        
        print(f"DEBUG: [send_link_test] ID пользователя: {user_id}, ссылка: {link}")
        
        # Импорт бота
        from main import bot
        
        # Отправка прямого текстового сообщения
        sent_message = await bot.send_message(
            chat_id=user_id,
            text=f"Тестовая ссылка: {link}"
        )
        
        print(f"DEBUG: [send_link_test] Сообщение отправлено, ID: {sent_message.message_id}")
        
        # Отправка подтверждения оператору
        await message.reply(f"✅ Тестовое сообщение отправлено пользователю {user_id}")
        
    except Exception as e:
        print(f"DEBUG: [send_link_test] ОШИБКА: {e}")
        await message.reply(f"❌ Ошибка: {e}")

def get_category_name(category: str) -> str:
    """Получить русское название категории товаров"""
    categories = {
        "lipstick": "помады",
        "mascara": "туши для ресниц",
        "perfume": "парфюма"
    }
    return categories.get(category, category)

# Функция для регистрации обработчиков
def register_handlers(dp: Dispatcher):
    # Инициализация базы данных при запуске
    init_db()
    
    # Получаем ID чата операторов из main.py
    global OPERATOR_CHAT_ID
    from main import OPERATOR_CHAT_ID as MAIN_OPERATOR_CHAT_ID
    OPERATOR_CHAT_ID = MAIN_OPERATOR_CHAT_ID
    
    print(f"DEBUG: Регистрация обработчиков рекомендаций, OPERATOR_CHAT_ID={OPERATOR_CHAT_ID}")
    
    # Регистрация диагностического обработчика ПЕРВЫМ в списке
    dp.message(lambda message: message.text and message.text.startswith("/debug_send"))(debug_send_message)
    
    # Регистрация других тестовых обработчиков
    dp.message(lambda message: message.text and message.text.startswith("/send_link_test"))(send_link_test)
    dp.message(lambda message: message.text and message.text.startswith("/send_link"))(test_send_link)
    
    # Регистрация обработчиков для рекомендаций
    dp.callback_query(lambda c: c.data == "product_recommendations")(start_recommendations)
    dp.callback_query(lambda c: c.data == "recommend_products")(start_recommendations)
    dp.callback_query(lambda c: c.data.startswith("category_"))(select_category)
    dp.callback_query(lambda c: c.data.startswith("criteria_"))(toggle_criteria)
    dp.callback_query(lambda c: c.data.startswith("header_"))(lambda c: c.answer("Это заголовок категории"))
    dp.callback_query(lambda c: c.data.startswith("reset_criteria_"))(reset_criteria)
    dp.callback_query(lambda c: c.data.startswith("show_recommendations_"))(show_recommendations)
    dp.callback_query(lambda c: c.data == "back_to_categories")(start_recommendations)

async def process_category_selection(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора категории товаров"""
    try:
        # Извлекаем выбранную категорию из callback_data
        category = callback.data.split('_')[1]
        
        # Получаем данные состояния
        user_data = await state.get_data()
        
        # Получаем ID сообщения (если есть) или используем текущее сообщение
        message_id = user_data.get('recommendation_message_id', callback.message.message_id)
        
        print(f"DEBUG: process_category_selection - пользователь {callback.from_user.id}, категория {category}, message_id {message_id}")
        
        # Отправляем ответ на callback, чтобы убрать индикатор загрузки
        await callback.answer()
        
        # Получаем имя пользователя или ID, если имя отсутствует
        user_tag = f"@{callback.from_user.username}" if callback.from_user.username else f"ID: {callback.from_user.id}"
        user_name = callback.from_user.full_name
        
        # Сохраняем информацию о запросе
        recommendation_requests[callback.from_user.id] = {
            "category": category,
            "message_id": message_id,
            "message": callback.message,
            "user_tag": user_tag,
            "user_name": user_name
        }
        
        print(f"DEBUG: Сохраняем запрос в recommendation_requests: {recommendation_requests[callback.from_user.id]}")
        logging.info(f"Сохранен запрос на рекомендации: user_id={callback.from_user.id}, category={category}, message_id={message_id}")
        
        # Формируем сообщение для оператора
        operator_message = (
            f"🔔 *Новый запрос на подбор рекомендаций*\n\n"
            f"👤 Пользователь: {user_name} ({user_tag})\n"
            f"📂 Категория: *{category}*\n\n"
            f"*Инструкция:*\n"
            f"Для отправки ссылки на товар используйте команду:\n"
            f"`/send_link {callback.from_user.id} ССЫЛКА [Описание]`\n\n"
            f"Пример: `/send_link {callback.from_user.id} https://example.com/product Отличный вариант!`"
        )
        
        # Отправляем сообщение оператору
        from main import bot
        await bot.send_message(
            chat_id=OPERATOR_CHAT_ID,
            text=operator_message,
            parse_mode="Markdown"
        )
        
        # Отправляем сообщение пользователю о том, что его запрос принят
        await callback.message.edit_text(
            "⏳ *Ваш запрос на подбор рекомендаций принят в обработку!*\n\n"
            f"Вы выбрали категорию: *{category}*\n\n"
            "Наш консультант скоро подберет для вас оптимальный вариант и пришлет ссылку на товар. "
            "Пожалуйста, оставайтесь в чате.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_main")]
            ]),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        print(f"DEBUG: Ошибка при обработке выбора категории: {e}")
        logging.error(f"Ошибка при обработке выбора категории: {e}")
        await callback.answer("Произошла ошибка при обработке запроса.")
        
        try:
            # Отправляем сообщение об ошибке
            await callback.message.edit_text(
                "😞 Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_main")]
                ])
            )
        except Exception as edit_error:
            logging.error(f"Ошибка при отправке сообщения об ошибке: {edit_error}") 

async def debug_send_message(message: types.Message):
    """Диагностический обработчик для проверки отправки сообщений"""
    try:
        print(f"DEBUG: [debug_send_message] Получена команда: {message.text}")
        
        # Разбор команды
        parts = message.text.split(' ', 2)
        if len(parts) < 3:
            await message.reply("❌ Используйте: /debug_send USER_ID ТЕКСТ")
            return
            
        # Получаем параметры
        user_id = parts[1]
        text_message = parts[2]
        
        print(f"DEBUG: [debug_send_message] ID пользователя: {user_id}, текст: {text_message}")
        
        # Отвечаем отправителю для подтверждения получения команды
        await message.reply(f"👍 Попытка отправки сообщения пользователю {user_id}...")
        
        # Импортируем бот напрямую
        from main import bot
        
        try:
            # Запрос информации о пользователе для проверки его существования
            try:
                print(f"DEBUG: [debug_send_message] Проверка существования пользователя {user_id}")
                user_info = await bot.get_chat(user_id)
                print(f"DEBUG: [debug_send_message] Информация о пользователе: {user_info.id}, {user_info.type}")
            except Exception as user_error:
                print(f"DEBUG: [debug_send_message] ОШИБКА при получении информации о пользователе: {user_error}")
                await message.reply(f"❌ Не удалось получить информацию о пользователе {user_id}: {user_error}")
                return
                
            # Проверяем разрешения и блокировки бота
            try:
                print(f"DEBUG: [debug_send_message] Проверка разрешений бота для пользователя {user_id}")
                chat_member = await bot.get_chat_member(user_id, bot.id)
                print(f"DEBUG: [debug_send_message] Разрешения бота: {chat_member.status}")
            except Exception as perm_error:
                print(f"DEBUG: [debug_send_message] ОШИБКА при проверке разрешений: {perm_error}")
                # Продолжаем, так как эта проверка может не работать для личных чатов
            
            # Последний этап - отправка сообщения без разметки и клавиатуры
            try:
                print(f"DEBUG: [debug_send_message] Отправка сообщения пользователю {user_id}")
                sent_message = await bot.send_message(
                    chat_id=user_id,
                    text=f"Тестовое сообщение: {text_message}"
                )
                print(f"DEBUG: [debug_send_message] Сообщение успешно отправлено! ID: {sent_message.message_id}")
                await message.reply(f"✅ Сообщение успешно отправлено пользователю {user_id}!")
            except Exception as send_error:
                print(f"DEBUG: [debug_send_message] КРИТИЧЕСКАЯ ОШИБКА при отправке: {send_error}")
                await message.reply(f"❌ Ошибка отправки сообщения: {send_error}")
        
        except Exception as bot_error:
            print(f"DEBUG: [debug_send_message] ОШИБКА при работе с ботом: {bot_error}")
            await message.reply(f"❌ Ошибка при работе с ботом: {bot_error}")
        
    except Exception as global_error:
        print(f"DEBUG: [debug_send_message] ГЛОБАЛЬНАЯ ОШИБКА: {global_error}")
        try:
            await message.reply(f"❌ Глобальная ошибка: {global_error}")
        except:
            print("Невозможно отправить даже сообщение об ошибке!") 