"""
Парсер для обработки загруженных файлов Excel и CSV.
Нормализует названия столбцов и валидирует данные перед сохранением в БД.
"""

import pandas as pd
from io import BytesIO, StringIO
from typing import Optional, Dict
from pathlib import Path


# Маппинг русских и английских названий столбцов на стандартные английские имена
COLUMN_NAME_MAPPING = {
    # Дата / Date
    'дата': 'date',
    'date': 'date',
    'день': 'date',
    'день месяца': 'date',
    
    # Товар / Product
    'товар': 'product',
    'product': 'product',
    'название': 'product',
    'название товара': 'product',
    'наименование': 'product',
    'товарное наименование': 'product',
    
    # Категория / Category
    'категория': 'category',
    'category': 'category',
    'тип': 'category',
    'раздел': 'category',
    'группа': 'category',
    'категория товара': 'category',
    
    # Сумма / Amount
    'сумма': 'amount',
    'amount': 'amount',
    'сумма продажи': 'amount',
    'итого': 'amount',
    'стоимость': 'amount',
    'цена': 'amount',
    'сумма значение': 'amount',
    
    # Количество / Quantity
    'количество': 'quantity',
    'quantity': 'quantity',
    'кол-во': 'quantity',
    'кол во': 'quantity',
    'штук': 'quantity',
    'шт': 'quantity',
}

# Требуемые столбцы после нормализации
REQUIRED_COLUMNS = {'date', 'product', 'category', 'amount', 'quantity'}


def normalize_column_name(col_name: str) -> Optional[str]:
    """
    Нормализует название столбца к стандартному английскому варианту.
    
    Args:
        col_name: исходное название столбца
    
    Returns:
        str: нормализованное название или None если совпадения не найдено
    """
    # Приводим к нижнему регистру и удаляем пробелы
    normalized = col_name.strip().lower()
    
    # Ищем в маппинге
    if normalized in COLUMN_NAME_MAPPING:
        return COLUMN_NAME_MAPPING[normalized]
    
    # Частичный поиск для вариантов с дополнительными символами
    for key, value in COLUMN_NAME_MAPPING.items():
        if key in normalized:
            return value
    
    return None


def parse_excel(file) -> pd.DataFrame:
    """
    Парсит файл Excel или CSV, нормализует столбцы, валидирует данные.
    
    Args:
        file: файл-подобный объект (от Streamlit uploader)
                поддерживает .xlsx, .xls и .csv форматы
    
    Returns:
        pd.DataFrame: очищенный DataFrame с правильными типами данных
    
    Raises:
        ValueError: если не найдены требуемые столбцы
        pd.errors.ParserError: если файл повреждён или имеет неверный формат
    """
    
    # Определяем расширение файла из имени
    filename = getattr(file, 'name', 'file').lower()
    
    try:
        # Читаем файл в зависимости от типа
        if filename.endswith('.csv'):
            # Для CSV пробуем разные кодировки
            try:
                df = pd.read_csv(file)
            except UnicodeDecodeError:
                file.seek(0)
                df = pd.read_csv(file, encoding='utf-8-sig')
        
        elif filename.endswith(('.xlsx', '.xls')):
            # Для Excel используем openpyxl (уже в requirements.txt)
            df = pd.read_excel(file, engine='openpyxl')
        
        else:
            # По умолчанию пробуем как Excel, потом как CSV
            try:
                df = pd.read_excel(file, engine='openpyxl')
            except Exception:
                file.seek(0)
                df = pd.read_csv(file)
    
    except Exception as e:
        raise ValueError(f"Ошибка при чтении файла: {str(e)}")
    
    # Проверяем, что DataFrame не пустой
    if df.empty:
        raise ValueError("Загруженный файл пустой. Пожалуйста, загрузите файл с данными.")
    
    # Нормализуем названия столбцов
    new_columns = {}
    for col in df.columns:
        normalized = normalize_column_name(str(col))
        if normalized:
            new_columns[col] = normalized
    
    # Переименовываем столбцы
    df = df.rename(columns=new_columns)
    
    # Оставляем только известные столбцы
    known_columns = [col for col in df.columns if col in REQUIRED_COLUMNS]
    df = df[known_columns]
    
    # Валидируем, что все требуемые столбцы присутствуют
    missing_columns = REQUIRED_COLUMNS - set(df.columns)
    if missing_columns:
        raise ValueError(
            f"Отсутствуют требуемые столбцы: {', '.join(missing_columns)}. "
            f"Найденные столбцы: {', '.join(df.columns)}. "
            f"Используйте названия: дата/date, товар/product, категория/category, "
            f"сумма/amount, количество/quantity"
        )
    
    # Преобразуем типы данных
    try:
        # Дата: конвертируем в datetime
        df['date'] = pd.to_datetime(df['date'], format='mixed', dayfirst=True)
    except Exception as e:
        raise ValueError(f"Ошибка формата даты. Используйте формат ДД.MM.ГГГГ или ДД-ММ-ГГГГ: {str(e)}")
    
    try:
        # Сумма: конвертируем в float, заменяем запятые на точки
        df['amount'] = df['amount'].astype(str).str.replace(',', '.').astype(float)
    except Exception as e:
        raise ValueError(f"Ошибка при преобразовании суммы в число: {str(e)}")
    
    try:
        # Количество: конвертируем в int
        df['quantity'] = pd.to_numeric(df['quantity'], downcast='integer')
    except Exception as e:
        raise ValueError(f"Ошибка при преобразовании количества в число: {str(e)}")
    
    # Удаляем дублирующиеся строки
    df = df.drop_duplicates()
    
    # Удаляем строки с пустыми значениями в критичных полях
    df = df.dropna(subset=['date', 'product', 'category', 'amount', 'quantity'])
    
    # Приводим текстовые поля к корректному формату
    df['product'] = df['product'].astype(str).str.strip()
    df['category'] = df['category'].astype(str).str.strip()
    
    # Сортируем по дате
    df = df.sort_values('date').reset_index(drop=True)
    
    return df


# Пример использования и маппинга
if __name__ == "__main__":
    # Пример: как использовать функцию
    print("Маппинг названий столбцов:")
    print(COLUMN_NAME_MAPPING)
    print("\nТребуемые столбцы:", REQUIRED_COLUMNS)
