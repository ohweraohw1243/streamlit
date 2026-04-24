"""
Генератор тестовых данных для аналитического приложения.
Создает Excel файл с реалистичными данными о продажах.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path


def generate_test_sales_data():
    """
    Генерирует тестовый Excel файл с данными о продажах.
    200 строк с колонками: дата, товар, категория, сумма, количество
    """
    
    # Список русских названий товаров (10 вариантов)
    products = [
        "Ноутбук Dell XPS 13",
        "Монитор LG 27 дюймов",
        "Клавиатура Logitech MX",
        "Мышка Apple Magic",
        "USB-Hub типа C",
        "Внешний SSD 1TB",
        "Наушники Sony WH-1000XM4",
        "Веб-камера HD Logitech",
        "Охлаждающая подставка для ноутбука",
        "Кабель Lightning 2м"
    ]
    
    # Категории товаров (3-4 варианта)
    categories = [
        "Компьютеры",
        "Периферия",
        "Аксессуары"
    ]
    
    # Генерируем случайные даты в 2024 году
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    date_range = (end_date - start_date).days
    
    # Генерируем 200 строк данных
    np.random.seed(42)  # Для воспроизводимости
    
    data = {
        'дата': [start_date + timedelta(days=int(np.random.uniform(0, date_range))) 
                for _ in range(200)],
        'товар': [np.random.choice(products) for _ in range(200)],
        'категория': [np.random.choice(categories) for _ in range(200)],
        'сумма': np.random.uniform(500, 50000, 200),
        'количество': np.random.randint(1, 21, 200)
    }
    
    # Создаем DataFrame
    df = pd.DataFrame(data)
    
    # Сортируем по дате
    df = df.sort_values('дата').reset_index(drop=True)
    
    # Форматируем столбец сумма до 2 десятичных мест
    df['сумма'] = df['сумма'].round(2)
    
    # Убеждаемся, что папка data существует
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    
    # Сохраняем в Excel
    file_path = data_dir / 'test_sales.xlsx'
    df.to_excel(file_path, sheet_name='Продажи', index=False)
    
    print(f"✓ Файл создан: {file_path}")
    print(f"  Количество строк: {len(df)}")
    print(f"  Период: {df['дата'].min().strftime('%d.%m.%Y')} - {df['дата'].max().strftime('%d.%m.%Y')}")
    print(f"  Сумма всех продаж: ₽ {df['сумма'].sum():,.2f}")
    print(f"  Среднее значение чека: ₽ {df['сумма'].mean():,.2f}")


if __name__ == "__main__":
    generate_test_sales_data()
