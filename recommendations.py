# recommendations.py - Модуль рекомендаций для Telegram бота GoldenAppleBot
# Этот модуль содержит функциональность для автоматического подбора рекомендаций 
# по косметике и отправки их пользователям, а также обработку запросов на подбор товаров

# Импорт стандартных библиотек Python
import logging  # Для логирования ошибок и информационных сообщений
import json  # Для работы с JSON-структурами (используется для атрибутов товаров)
import sqlite3  # Для работы с SQLite базой данных
import random  # Для случайного выбора товаров при формировании рекомендаций
from datetime import datetime  # Для работы с датами и временем
import pandas as pd  # Для анализа данных и создания датафреймов
from aiogram import types, Dispatcher  # Основные компоненты библиотеки aiogram
from aiogram.fsm.context import FSMContext  # Для работы с состояниями пользователей
from aiogram.fsm.state import State, StatesGroup  # Для определения состояний
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton  # Для создания интерактивных кнопок
import asyncio  # Для асинхронного выполнения задач

# Класс состояний для процесса подбора рекомендаций
# Используется для отслеживания на каком этапе взаимодействия находится пользователь
class RecommendationState(StatesGroup):
    choosing_category = State()  # Состояние выбора категории товара
    waiting_for_criteria = State()  # Ожидание ввода критериев пользователем
    choosing_criteria = State()  # Состояние выбора конкретных критериев
    waiting_for_operator_reply = State()  # Ожидание ответа оператора на запрос пользователя

# Временное хранилище для данных пользователей
# Используется для сохранения промежуточных результатов взаимодействия
user_storage = {}

# Словарь для хранения запросов пользователей и ответов операторов
# Ключ - ID пользователя, значение - информация о запросе и ответе
recommendation_requests = {}

# ID чата операторов, который будет инициализирован из main.py при регистрации обработчиков
# В этот чат будут отправляться запросы от пользователей, если автоматический подбор не справился
OPERATOR_CHAT_ID = None

def init_db():
    """Инициализирует базу данных рекомендаций, если она не существует
    
    Функция создаёт или проверяет структуру базы данных SQLite со списком товаров.
    В случае отсутствия базы или проблем со структурой таблицы, создаёт её заново и
    заполняет демонстрационными данными.
    
    Структура таблицы products:
    - id: уникальный идентификатор товара
    - name: название товара
    - category: категория товара (например, mascara, lipstick, perfume)
    - price: цена товара
    - rating: рейтинг товара (от 0 до 5)
    - attributes: JSON-строка с атрибутами товара (тип, эффект, цвет и т.д.)
    """
    try:
        import os
        # Проверяем наличие файла базы данных
        db_exists = os.path.exists('recommendations.db')
        
        # Подключаемся к базе данных (если файл не существует, он будет создан)
        conn = sqlite3.connect('recommendations.db')
        cursor = conn.cursor()
        
        # Проверяем структуру существующей таблицы, если база данных уже существует
        if db_exists:
            cursor.execute("PRAGMA table_info(products)")
            columns = [col[1] for col in cursor.fetchall()]
            print(f"Существующие столбцы таблицы products: {columns}")
            
            # Если таблица существует, но нет столбца attributes (необходимого для работы),
            # удаляем таблицу и пересоздаем её
            if 'attributes' not in columns:
                print("Столбец attributes отсутствует. Пересоздаем таблицу...")
                cursor.execute('DROP TABLE IF EXISTS products')
                db_exists = False
        
        # Создаем таблицу, если она не существует или была удалена
        if not db_exists:
            print("Создаем таблицу products...")
            cursor.execute('''CREATE TABLE IF NOT EXISTS products
                          (id INTEGER PRIMARY KEY,
                          name TEXT,
                          category TEXT,
                          price REAL,
                          rating REAL,
                          attributes TEXT)''')
            
            # Тестовые данные с расширенными атрибутами в формате JSON
            # Каждый товар имеет свой набор атрибутов в зависимости от категории
            products = [
                (1, 'Тушь для ресниц Volume', 'mascara', 1500, 4.8, 
                 json.dumps({
                     "effect": ["volume", "length"],  # Эффект: объем, длина
                     "type": "waterproof",  # Тип: водостойкая
                     "brush": "silicone",  # Щеточка: силиконовая
                     "price": "medium"  # Ценовая категория: средняя
                 })),
                (2, 'Помада матовая Ruby', 'lipstick', 2300, 4.5,
                 json.dumps({
                     "type": "matte",  # Тип: матовая
                     "finish": "velvet",  # Финиш: бархатный
                     "longevity": "long",  # Стойкость: долгая
                     "color": "red",  # Цвет: красный
                     "price": "premium"  # Ценовая категория: премиум
                 })),
                (3, 'Парфюм Rose Garden', 'perfume', 4500, 4.9,
                 json.dumps({
                     "type": ["floral", "sweet"],  # Тип: цветочный, сладкий
                     "intensity": "medium",  # Интенсивность: средняя
                     "longevity": "long",  # Стойкость: долгая
                     "season": ["spring", "summer"],  # Сезон: весна, лето
                     "price": "medium"  # Ценовая категория: средняя
                 })),
                (4, 'Помада глянцевая Pearl', 'lipstick', 1800, 4.7,
                 json.dumps({
                     "type": "glossy",  # Тип: глянцевая
                     "finish": "shimmer",  # Финиш: с шиммером
                     "longevity": "medium",  # Стойкость: средняя
                     "color": "nude",  # Цвет: нюдовый
                     "price": "medium"  # Ценовая категория: средняя
                 })),
                (5, 'Тушь для ресниц Dramatic', 'mascara', 2500, 4.6,
                 json.dumps({
                     "effect": ["volume", "curl"],  # Эффект: объем, подкручивание
                     "type": "waterproof",  # Тип: водостойкая
                     "brush": "curved",  # Щеточка: изогнутая
                     "price": "premium"  # Ценовая категория: премиум
                 })),
                (6, 'Тушь для ресниц Natural Look', 'mascara', 900, 4.3,
                 json.dumps({
                     "effect": ["separation", "definition"],  # Эффект: разделение, четкость
                     "type": "regular",  # Тип: обычная
                     "brush": "traditional",  # Щеточка: традиционная
                     "price": "budget"  # Ценовая категория: бюджетная
                 })),
                (7, 'Помада жидкая Velvet', 'lipstick', 1700, 4.8,
                 json.dumps({
                     "type": "liquid",  # Тип: жидкая
                     "finish": "velvet",  # Финиш: бархатный
                     "longevity": "long",  # Стойкость: долгая
                     "color": "berry",  # Цвет: ягодный
                     "price": "medium"  # Ценовая категория: средняя
                 })),
                (8, 'Парфюм Citrus Fresh', 'perfume', 3500, 4.3,
                 json.dumps({
                     "type": ["citrus", "fresh"],  # Тип: цитрусовый, свежий
                     "intensity": "light",  # Интенсивность: легкая
                     "longevity": "medium",  # Стойкость: средняя
                     "season": ["summer"],  # Сезон: лето
                     "price": "medium"  # Ценовая категория: средняя
                 })),
                (9, 'Тушь для ресниц Natural', 'mascara', 900, 4.2,
                 json.dumps({
                     "effect": ["length", "separation"],  # Эффект: длина, разделение
                     "type": "regular",  # Тип: обычная
                     "brush": "natural",  # Щеточка: натуральная
                     "price": "budget"  # Ценовая категория: бюджетная
                 })),
                (10, 'Парфюм Tropical Night', 'perfume', 5500, 4.7,
                 json.dumps({
                     "type": ["tropical", "spicy"],  # Тип: тропический, пряный
                     "intensity": "strong",  # Интенсивность: сильная
                     "longevity": "long",  # Стойкость: долгая
                     "season": ["summer", "autumn"],  # Сезон: лето, осень
                     "price": "premium"  # Ценовая категория: премиум
                 })),
                # Румяна
                (11, 'Румяна гелевые Rose Glow', 'blush', 2500, 4.6,
                 json.dumps({
                     "texture": "gel",  # Текстура: гелевые
                     "color": "nude",   # Цвет: нюдовые оттенки
                     "price": "medium"  # Ценовая категория: средняя
                 })),
                (12, 'Румяна пудровые Bright Berry', 'blush', 3200, 4.4,
                 json.dumps({
                     "texture": "powder",  # Текстура: пудровые
                     "color": "bright",    # Цвет: яркие оттенки
                     "price": "medium"     # Ценовая категория: средняя
                 })),
                (13, 'Румяна кремовые Peachy', 'blush', 2800, 4.7,
                 json.dumps({
                     "texture": "cream",  # Текстура: кремовые
                     "color": "nude",     # Цвет: нюдовые оттенки
                     "price": "medium"    # Ценовая категория: средняя
                 })),
                # Хайлайтер
                (14, 'Хайлайтер жидкий Golden Glow', 'highlighter', 3500, 4.8,
                 json.dumps({
                     "texture": "liquid",  # Текстура: жидкий
                     "shade": "warm",      # Оттенки: теплые
                     "price": "medium"     # Ценовая категория: средняя
                 })),
                (15, 'Хайлайтер стик Silver Light', 'highlighter', 2900, 4.5,
                 json.dumps({
                     "texture": "stick",  # Текстура: стик
                     "shade": "cool",     # Оттенки: холодные
                     "price": "medium"    # Ценовая категория: средняя
                 })),
                (16, 'Хайлайтер пудровый Pearl Shine', 'highlighter', 3800, 4.9,
                 json.dumps({
                     "texture": "powder",  # Текстура: пудровый
                     "shade": "warm",      # Оттенки: теплые
                     "price": "medium"     # Ценовая категория: средняя
                 })),
                # Пудра
                (17, 'Пудра рассыпчатая Transparent', 'powder', 2200, 4.3,
                 json.dumps({
                     "texture": "loose",      # Текстура: рассыпчатая
                     "shade": "transparent",  # Оттенки: прозрачная
                     "price": "medium"        # Ценовая категория: средняя
                 })),
                (18, 'Пудра прессованная Beige', 'powder', 2700, 4.6,
                 json.dumps({
                     "texture": "pressed",  # Текстура: прессованная
                     "shade": "tinted",     # Оттенки: тонированная
                     "price": "medium"      # Ценовая категория: средняя
                 })),
                # Тени
                (19, 'Тени сухие Nude Palette', 'eyeshadow', 2400, 4.5,
                 json.dumps({
                     "texture": "dry",    # Текстура: сухие
                     "shade": "nude",     # Оттенки: нюдовые
                     "price": "medium"    # Ценовая категория: средняя
                 })),
                (20, 'Тени жидкие Bright Color', 'eyeshadow', 3100, 4.7,
                 json.dumps({
                     "texture": "liquid",  # Текстура: жидкие
                     "shade": "bright",    # Оттенки: яркие
                     "price": "medium"     # Ценовая категория: средняя
                 })),
                (21, 'Тени сухие Smoky Eyes', 'eyeshadow', 2800, 4.8,
                 json.dumps({
                     "texture": "dry",    # Текстура: сухие
                     "shade": "bright",   # Оттенки: яркие
                     "price": "medium"    # Ценовая категория: средняя
                 }))
            ]
            
            # Вставляем тестовые данные в таблицу
            cursor.executemany('INSERT INTO products VALUES (?,?,?,?,?,?)', products)
            conn.commit()
            print(f"Добавлено {len(products)} товаров в базу данных")
        
        # Проверяем количество записей в таблице products
        cursor.execute("SELECT COUNT(*) FROM products")
        row_count = cursor.fetchone()[0]
        print(f"Количество товаров в базе данных: {row_count}")
        
        conn.close()
    except Exception as e:
        # Логируем ошибку инициализации базы данных
        logging.error(f"Ошибка инициализации базы данных: {e}")
        print(f"Ошибка при инициализации БД: {e}")
        # Если возникла ошибка, пробуем создать базу данных заново
        try:
            import os
            # Удаляем файл базы данных, если он существует
            if os.path.exists('recommendations.db'):
                os.remove('recommendations.db')
            
            # Создаем новую базу данных с базовой структурой
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
            # Логируем критическую ошибку, если не удалось пересоздать базу данных
            logging.error(f"Критическая ошибка при пересоздании базы данных: {inner_e}")
            print(f"Критическая ошибка: {inner_e}")

def get_category_criteria_keyboard(category: str, selected_criteria: list = None) -> InlineKeyboardMarkup:
    """Создает клавиатуру с критериями для выбранной категории товаров
    
    Формирует интерактивную клавиатуру с доступными критериями для выбранной категории.
    Выбранные критерии отмечаются специальным символом.
    
    Args:
        category (str): Категория товара (mascara, lipstick, perfume и т.д.)
        selected_criteria (list, optional): Список уже выбранных критериев
        
    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками для выбора критериев
    """
    if selected_criteria is None:
        selected_criteria = []
    
    # Получаем критерии для выбранной категории из константного класса ProductCategories
    category_data = getattr(ProductCategories, category.upper(), {})
    
    buttons = []
    # Добавляем смайлики для разных групп критериев для улучшения пользовательского опыта
    emoji_map = {
        "type": "🏷️",  # Тип
        "effect": "✨",  # Эффект
        "finish": "🎨",  # Финиш
        "longevity": "⏱️",  # Стойкость
        "color": "🌈",  # Цвет
        "brush": "🖌️",  # Щеточка
        "price": "💰",  # Цена
        "intensity": "💪",  # Интенсивность
        "season": "🍃",   # Сезон
        "texture": "🏷️",  # Текстура
        "shade": "🌈"   # Оттенки
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
                elif criteria_id == "bright": criteria_emoji = "🌟 "
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
            elif criteria_group == "texture":
                if criteria_id == "gel": criteria_emoji = "🧴 "
                elif criteria_id == "powder": criteria_emoji = "💎 "
                elif criteria_id == "cream": criteria_emoji = "🍦 "
                elif criteria_id == "liquid": criteria_emoji = "💧 "
                elif criteria_id == "stick": criteria_emoji = "🖍️ "
                elif criteria_id == "loose": criteria_emoji = "💨 "
                elif criteria_id == "pressed": criteria_emoji = "⬜ "
                elif criteria_id == "dry": criteria_emoji = "🌪️ "
            elif criteria_group == "shade":
                if criteria_id == "cool": criteria_emoji = "❄️ "
                elif criteria_id == "warm": criteria_emoji = "🔥 "
                elif criteria_id == "transparent": criteria_emoji = "👻 "
                elif criteria_id == "tinted": criteria_emoji = "🎨 "
                
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
    """Возвращает данные пользователя из временного хранилища
    
    Получает или создает запись о пользователе в хранилище данных.
    Если запись существует, возвращает её. Если нет - создает пустую запись.
    
    Args:
        user_id (int): ID пользователя в Telegram
        
    Returns:
        dict: Словарь с данными пользователя, включающий историю просмотров,
              историю покупок и предпочтения
    """
    return user_storage.get(user_id, {
        'view_history': [],  # История просмотров товаров пользователем
        'purchase_history': [],  # История покупок пользователя
        'preferences': {}  # Предпочтения пользователя (выбранные критерии)
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

    # Категория парфюма и её критерии
    PERFUME = {
        "type": {  # Группа критериев: тип аромата
            "floral": "Цветочные",
            "citrus": "Цитрусовые",
            "woody": "Древесные",
            "spicy": "Пряные",
            "sweet": "Сладкие",
            "fresh": "Свежие"
        },
        "intensity": {  # Группа критериев: интенсивность аромата
            "light": "Легкая",
            "medium": "Средняя",
            "strong": "Сильная"
        },
        "longevity": {  # Группа критериев: стойкость аромата
            "short": "Обычная стойкость",
            "medium": "Средняя стойкость",
            "long": "Долгая стойкость"
        },
        "season": {  # Группа критериев: сезонность аромата
            "spring": "Весенний",
            "summer": "Летний",
            "autumn": "Осенний",
            "winter": "Зимний"
        },
        "price": {  # Группа критериев: ценовая категория
            "budget": "Бюджетная (до 3000р)",
            "medium": "Средняя (3000-5000р)",
            "premium": "Премиум (от 5000р)"
        }
    }

    # Категория румян
    BLUSH = {
        "texture": {
            "gel": "Гелевые",
            "powder": "Пудровые", 
            "cream": "Кремовые"
        },
        "color": {
            "nude": "Нюдовые оттенки",
            "bright": "Яркие оттенки"
        },
        "price": {
            "medium": "Средняя (2000-10000р)"
        }
    }

    # Категория хайлайтера
    HIGHLIGHTER = {
        "texture": {
            "liquid": "Жидкий",
            "stick": "Стик",
            "powder": "Пудровый"
        },
        "shade": {
            "cool": "Холодные",
            "warm": "Теплые"
        },
        "price": {
            "medium": "Средняя (2000-10000р)"
        }
    }

    # Категория пудры
    POWDER = {
        "texture": {
            "loose": "Рассыпчатая",
            "pressed": "Прессованная"
        },
        "shade": {
            "transparent": "Прозрачная",
            "tinted": "Тонированная"
        },
        "price": {
            "medium": "Средняя (2000-10000р)"
        }
    }

    # Категория теней
    EYESHADOW = {
        "texture": {
            "dry": "Сухие",
            "liquid": "Жидкие"
        },
        "shade": {
            "bright": "Яркие",
            "nude": "Нюдовые"
        },
        "price": {
            "medium": "Средняя (2000-10000р)"
        }
    }

# Класс для управления системой рекомендаций
class RecommendationSystem:
    """Базовый класс системы рекомендаций
    
    Предоставляет основные методы для загрузки данных из базы данных
    и генерации рекомендаций по различным критериям.
    """
    
    def __init__(self):
        """Инициализация системы рекомендаций
        
        Создает пустые структуры данных для хранения информации о товарах.
        Данные будут загружены при первом запросе.
        """
        self.products = []  # Список всех товаров
        self.products_by_category = {}  # Словарь товаров по категориям
        self.data_loaded = False  # Флаг загрузки данных
        
    def load_data(self):
        """Загружает данные о товарах из базы данных
        
        Заполняет self.products и self.products_by_category данными из БД.
        Если данные уже загружены, повторная загрузка не производится.
        """
        if self.data_loaded:
            return
        
        try:
            # Подключение к БД и получение данных
            conn = sqlite3.connect('recommendations.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, category, price, rating, attributes FROM products")
            rows = cursor.fetchall()
            
            # Обработка результатов запроса
            for row in rows:
                product_id, name, category, price, rating, attributes_json = row
                try:
                    # Преобразуем JSON строку из БД в словарь Python
                    attributes = json.loads(attributes_json) if attributes_json else {}
                except json.JSONDecodeError as e:
                    # Если не удалось распарсить JSON, создаем пустой словарь
                    print(f"Ошибка при обработке JSON для товара {product_id}: {e}")
                    attributes = {}
                
                # Создаем словарь с информацией о товаре
                product = {
                    'id': product_id,
                    'name': name,
                    'category': category,
                    'price': price,
                    'rating': rating,
                    'attributes': attributes
                }
                
                # Добавляем товар в общий список
                self.products.append(product)
                
                # Добавляем товар в словарь по категориям
                if category not in self.products_by_category:
                    self.products_by_category[category] = []
                self.products_by_category[category].append(product)
            
            conn.close()
            self.data_loaded = True
            print(f"Загружено {len(self.products)} товаров из базы данных")
        
        except Exception as e:
            # Логирование ошибки при загрузке данных
            logging.error(f"Ошибка при загрузке данных из БД: {e}")
            print(f"Ошибка при загрузке данных: {e}")
    
    def refresh_data(self):
        """Принудительно обновляет данные из базы данных
        
        Очищает кеш и заново загружает данные о товарах.
        Используется, если данные в базе были изменены.
        """
        self.products = []
        self.products_by_category = {}
        self.data_loaded = False
        self.load_data()
    
    def get_recommendations_by_popularity(self, category=None, limit=5):
        """Возвращает рекомендации на основе рейтинга популярности
        
        Выбирает товары с наивысшим рейтингом из указанной категории.
        
        Args:
            category (str, optional): Категория товаров для рекомендаций.
                                      Если None, выбираются товары из всех категорий.
            limit (int, optional): Максимальное количество рекомендаций. По умолчанию 5.
            
        Returns:
            list: Список словарей с информацией о рекомендованных товарах.
        """
        # Загружаем данные, если они ещё не загружены
        self.load_data()
        
        # Выбираем товары из указанной категории или из всех категорий
        if category:
            products = self.products_by_category.get(category, [])
        else:
            products = self.products
        
        # Сортируем товары по рейтингу (от высшего к низшему)
        sorted_products = sorted(products, key=lambda x: x['rating'], reverse=True)
        
        # Возвращаем лимитированное количество товаров
        return sorted_products[:limit]
    
    def get_recommendations_by_price(self, category=None, limit=5, ascending=True):
        """Возвращает рекомендации на основе цены
        
        Выбирает товары с наименьшей или наибольшей ценой из указанной категории.
        
        Args:
            category (str, optional): Категория товаров для рекомендаций.
                                      Если None, выбираются товары из всех категорий.
            limit (int, optional): Максимальное количество рекомендаций. По умолчанию 5.
            ascending (bool, optional): Если True, сортировка по возрастанию цены (от дешевых).
                                        Если False, по убыванию (от дорогих).
            
        Returns:
            list: Список словарей с информацией о рекомендованных товарах.
        """
        # Загружаем данные, если они ещё не загружены
        self.load_data()
        
        # Выбираем товары из указанной категории или из всех категорий
        if category:
            products = self.products_by_category.get(category, [])
        else:
            products = self.products
        
        # Сортируем товары по цене (по возрастанию или убыванию)
        sorted_products = sorted(products, key=lambda x: x['price'], reverse=not ascending)
        
        # Возвращаем лимитированное количество товаров
        return sorted_products[:limit]

# Расширенная система рекомендаций
class AdvancedRecommendationSystem:
    """Расширенная система рекомендаций с возможностью фильтрации по критериям
    
    Этот класс предоставляет продвинутые методы для поиска товаров, соответствующих
    заданным критериям. Работает напрямую с базой данных для более гибкого поиска.
    """
    
    def get_recommendations(self, category: str, criteria: list) -> list:
        """Возвращает рекомендации по категории и списку критериев
        
        Выполняет запрос к базе данных и фильтрует товары, соответствующие 
        всем указанным критериям из выбранной категории.
        
        Args:
            category (str): Категория товаров для поиска (mascara, lipstick, perfume и т.д.)
            criteria (list): Список строк с критериями в формате "группа_идентификатор"
                            (например, ["type_matte", "price_premium"])
            
        Returns:
            list: Список словарей с информацией о рекомендованных товарах
        """
        # Вывод отладочной информации для отслеживания вызовов
        print(f"Поиск рекомендаций для категории: {category}, критерии: {criteria}")
        
        # Подключение к базе данных SQLite
        conn = sqlite3.connect('recommendations.db')
        cursor = conn.cursor()
        
        try:
            # Проверяем структуру таблицы products и наличие столбца attributes
            # Это важно, так как критерии хранятся в JSON формате в этом столбце
            cursor.execute("PRAGMA table_info(products)")
            columns = [col[1] for col in cursor.fetchall()]
            print(f"Столбцы таблицы products: {columns}")
            
            # Формируем базовый SQL запрос для выборки товаров заданной категории
            query = f"SELECT * FROM products WHERE category = ?"
            params = [category]
            
            # Если в таблице есть столбец attributes и заданы критерии,
            # расширяем запрос дополнительными условиями LIKE для каждого критерия
            # Поиск выполняется по вхождению критерия в JSON строку атрибутов
            if 'attributes' in columns and criteria:
                query += " AND " + " AND ".join(["attributes LIKE ?" for _ in criteria])
                params += [f'%{c}%' for c in criteria]
            
            # Выполняем SQL запрос с параметрами
            print(f"SQL запрос: {query}")
            print(f"Параметры: {params}")
            cursor.execute(query, params)
            
            # Получаем результаты запроса
            rows = cursor.fetchall()
            print(f"Найдено товаров: {len(rows)}")
            
            # Преобразуем результаты запроса в список словарей для удобства использования
            results = self._parse_results(rows, columns)
            
            # Возвращаем результаты, если они найдены, или пустой список
            return results
        
        except Exception as e:
            # Логируем ошибку при выполнении запроса
            logging.error(f"Ошибка при поиске рекомендаций: {e}")
            print(f"Ошибка при поиске рекомендаций: {e}")
            return []
        
        finally:
            # Закрываем соединение с базой данных в любом случае
            conn.close()

    def _parse_results(self, rows, columns) -> list:
        """Преобразует результаты SQL запроса в список словарей
        
        Args:
            rows (list): Список кортежей с результатами запроса
            columns (list): Список имен столбцов таблицы
            
        Returns:
            list: Список словарей с данными о товарах
        """
        results = []
        
        # Индекс столбца attributes для быстрого доступа
        attributes_idx = columns.index('attributes') if 'attributes' in columns else -1
        
        for row in rows:
            # Создаем словарь товара из данных запроса
            item = {}
            for i, col in enumerate(columns):
                if i < len(row):
                    item[col] = row[i]
            
            # Преобразуем JSON строку атрибутов в словарь Python
            if attributes_idx >= 0 and attributes_idx < len(row) and row[attributes_idx]:
                try:
                    item['attributes'] = json.loads(row[attributes_idx])
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"Ошибка декодирования JSON для товара: {e}")
                    item['attributes'] = {}
            else:
                item['attributes'] = {}
            
            results.append(item)
        
        return results
    
    def get_random_recommendations(self, category, limit=3):
        """Возвращает случайные рекомендации из указанной категории
        
        Используется, когда нет конкретных критериев или для разнообразия предложений.
        
        Args:
            category (str): Категория товаров (mascara, lipstick, perfume и т.д.)
            limit (int, optional): Максимальное количество рекомендаций. По умолчанию 3.
            
        Returns:
            list: Список словарей с информацией о случайно выбранных товарах
        """
        conn = sqlite3.connect('recommendations.db')
        cursor = conn.cursor()
        
        try:
            # Получаем структуру таблицы для корректного парсинга результатов
            cursor.execute("PRAGMA table_info(products)")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Выполняем запрос с случайной сортировкой и ограничением количества
            cursor.execute(
                "SELECT * FROM products WHERE category = ? ORDER BY RANDOM() LIMIT ?", 
                (category, limit)
            )
            
            results = cursor.fetchall()
            return self._parse_results(results, columns)
            
        except Exception as e:
            logging.error(f"Ошибка при получении случайных рекомендаций: {e}")
            print(f"Ошибка: {e}")
            return []
            
        finally:
            conn.close()

# Инициализация системы рекомендаций (будет использоваться далее)
recommendation_system = AdvancedRecommendationSystem()

# Функция для рендеринга клавиатуры с категориями товаров
def get_categories_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру с доступными категориями товаров
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками категорий
    """
    buttons = [
        [
            InlineKeyboardButton(text="💄 Помада", callback_data="select_category_lipstick"),
            InlineKeyboardButton(text="👁 Тушь", callback_data="select_category_mascara")
        ],
        [
            InlineKeyboardButton(text="🧴 Парфюм", callback_data="select_category_perfume"),
            InlineKeyboardButton(text="🌸 Румяна", callback_data="select_category_blush")
        ],
        [
            InlineKeyboardButton(text="✨ Хайлайтер", callback_data="select_category_highlighter"),
            InlineKeyboardButton(text="🌟 Пудра", callback_data="select_category_powder")
        ],
        [
            InlineKeyboardButton(text="👀 Тени", callback_data="select_category_eyeshadow"),
            InlineKeyboardButton(text="🔍 Другие категории", callback_data="more_categories")
        ],
        [InlineKeyboardButton(text="🔙 Назад в главное меню", callback_data="back_to_main")]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Функция для форматирования текста рекомендации
def format_recommendation(product: dict) -> str:
    """Форматирует информацию о товаре для отображения пользователю
    
    Args:
        product (dict): Словарь с информацией о товаре
        
    Returns:
        str: Отформатированный текст с информацией о товаре
    """
    # Получаем эмодзи для категории товара
    category_emoji = {
        'lipstick': '💄',
        'mascara': '👁',
        'perfume': '🧴',
        'blush': '🌸',
        'highlighter': '✨',
        'powder': '🌟',
        'eyeshadow': '👀'
    }
    emoji = category_emoji.get(product['category'], '🎀')
    
    # Создаем основной текст с названием и ценой
    text = f"{emoji} <b>{product['name']}</b>\n"
    text += f"💰 Цена: {product['price']} ₽\n"
    text += f"⭐ Рейтинг: {product['rating']} / 5.0\n\n"
    
    # Добавляем информацию об атрибутах товара, если они есть
    if 'attributes' in product and product['attributes']:
        text += "<b>Характеристики:</b>\n"
        
        # Словарь с русскими названиями групп атрибутов
        attr_groups = {
            "type": "Тип",
            "effect": "Эффект",
            "finish": "Финиш",
            "longevity": "Стойкость",
            "color": "Цвет",
            "brush": "Щеточка",
            "price": "Ценовая категория",
            "intensity": "Интенсивность",
            "season": "Сезон",
            "texture": "Текстура",
            "shade": "Оттенки"
        }
        
        # Словарь с эмодзи для групп атрибутов
        attr_emoji = {
            "type": "🏷️",
            "effect": "✨",
            "finish": "🎨",
            "longevity": "⏱️",
            "color": "🌈",
            "brush": "🖌️",
            "price": "💰",
            "intensity": "💪",
            "season": "🍃",
            "texture": "🏷️",
            "shade": "🌈"
        }
        
        # Добавляем атрибуты в текст
        for attr_group, attr_value in product['attributes'].items():
            group_name = attr_groups.get(attr_group, attr_group.title())
            emoji = attr_emoji.get(attr_group, "📋")
            
            # Обрабатываем случай, когда значение атрибута - список
            if isinstance(attr_value, list):
                # Получаем человекочитаемые названия из ProductCategories
                category_data = getattr(ProductCategories, product['category'].upper(), {})
                group_data = category_data.get(attr_group, {})
                
                # Форматируем значения из списка
                values = []
                for val in attr_value:
                    # Пытаемся получить человекочитаемое название, если не найдено - используем значение как есть
                    if val in group_data:
                        values.append(group_data[val])
                    else:
                        values.append(val)
                
                text += f"{emoji} {group_name}: {', '.join(values)}\n"
            else:
                # Простой случай - одно значение
                category_data = getattr(ProductCategories, product['category'].upper(), {})
                group_data = category_data.get(attr_group, {})
                
                # Пытаемся получить человекочитаемое название
                if attr_value in group_data:
                    text += f"{emoji} {group_name}: {group_data[attr_value]}\n"
                else:
                    text += f"{emoji} {group_name}: {attr_value}\n"
    
    return text

# Функция для отображения рекомендаций пользователю
async def show_recommendations(message_or_callback, products, edit=False, user_id=None):
    """Отображает рекомендации пользователю
    
    Args:
        message_or_callback: Объект сообщения или callback запроса
        products (list): Список товаров для отображения
        edit (bool, optional): Если True, редактирует существующее сообщение вместо отправки нового
        user_id (int, optional): ID пользователя, если нужно отправить рекомендации напрямую
    """
    if not products:
        # Если рекомендации не найдены, сообщаем об этом
        text = "😞 К сожалению, по вашим критериям ничего не найдено.\n\nПопробуйте изменить критерии или выбрать другую категорию."
        
        # Создаем клавиатуру с кнопками для продолжения
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Попробовать другие критерии", callback_data="back_to_categories")],
            [InlineKeyboardButton(text="👨‍💼 Связаться с оператором", callback_data="contact_operator")],
            [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main")]
        ])
        
        # Отправляем или редактируем сообщение
        if edit and hasattr(message_or_callback, 'message'):
            await message_or_callback.message.edit_text(text, reply_markup=keyboard)
        elif user_id:
            await bot.send_message(user_id, text, reply_markup=keyboard)
        else:
            await message_or_callback.answer(text, reply_markup=keyboard)
        return
    
    # Форматируем рекомендации в текст
    text = "✨ <b>Рекомендации для вас:</b>\n\n"
    
    # Добавляем информацию о каждом товаре
    for i, product in enumerate(products, 1):
        text += f"<b>{i}.</b> {format_recommendation(product)}\n"
    
    # Добавляем информацию о том, как получить ссылку
    text += "\n🔗 Для получения ссылки на товар напишите оператору командой /send_link c номером товара из списка."
    
    # Создаем клавиатуру с кнопками для управления
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Показать другие рекомендации", callback_data=f"refresh_recommendations_{products[0]['category']}")],
        [InlineKeyboardButton(text="🔍 Изменить критерии", callback_data=f"select_category_{products[0]['category']}")],
        [InlineKeyboardButton(text="👨‍💼 Связаться с оператором", callback_data="contact_operator")],
        [InlineKeyboardButton(text="🔙 Вернуться к категориям", callback_data="back_to_categories")]
    ])
    
    # Отправляем или редактируем сообщение
    try:
        if edit and hasattr(message_or_callback, 'message'):
            await message_or_callback.message.edit_text(text, reply_markup=keyboard)
        elif user_id:
            await bot.send_message(user_id, text, reply_markup=keyboard)
        else:
            await message_or_callback.answer(text, reply_markup=keyboard)
    except Exception as e:
        # Если текст слишком длинный, отправляем сокращенную версию
        logging.error(f"Ошибка при отправке рекомендаций: {e}")
        
        # Создаем сокращенный текст с первыми двумя рекомендациями
        short_text = "✨ <b>Рекомендации для вас:</b>\n\n"
        for i, product in enumerate(products[:2], 1):
            short_text += f"<b>{i}.</b> {format_recommendation(product)}\n"
        
        short_text += "\n⚠️ Текст был сокращен из-за ограничений Telegram.\n"
        short_text += "\n🔗 Для получения ссылки на товар напишите оператору командой /send_link c номером товара из списка."
        
        # Повторяем отправку с сокращенным текстом
        if edit and hasattr(message_or_callback, 'message'):
            await message_or_callback.message.edit_text(short_text, reply_markup=keyboard)
        elif user_id:
            await bot.send_message(user_id, short_text, reply_markup=keyboard)
        else:
            await message_or_callback.answer(short_text, reply_markup=keyboard)

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
            [InlineKeyboardButton(text="🌸 Румяна", callback_data="category_blush")],
            [InlineKeyboardButton(text="✨ Хайлайтер", callback_data="category_highlighter")],
            [InlineKeyboardButton(text="🌟 Пудра", callback_data="category_powder")],
            [InlineKeyboardButton(text="👀 Тени", callback_data="category_eyeshadow")],
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
        "perfume": "парфюма",
        "blush": "румян",
        "highlighter": "хайлайтера",
        "powder": "пудры",
        "eyeshadow": "теней"
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