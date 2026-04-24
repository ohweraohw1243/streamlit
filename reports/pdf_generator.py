"""
Генератор PDF отчетов на fpdf2 для аналитического приложения.
Создает профессиональные отчеты с метриками и таблицами.
"""

from fpdf import FPDF
from datetime import datetime
import pandas as pd
from io import BytesIO
from typing import Optional


class SalesReportPDF(FPDF):
    """
    Пользовательский класс PDF с поддержкой заголовков и подвалов.
    """
    
    def __init__(self):
        super().__init__()
        self.width = 210  # A4 ширина
        self.height = 297  # A4 высота
        self.title_str = ""
    
    def header(self):
        """Добавляет заголовок на каждую страницу."""
        self.set_font("Arial", "B", 16)
        self.set_xy(10, 8)
        self.cell(0, 10, self.title_str, ln=True, align="C")
        self.ln(2)
    
    def footer(self):
        """Добавляет подвал на каждую страницу с датой и номером страницы."""
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(128, 128, 128)
        
        # Дата генерации слева
        self.cell(0, 10, f"Создано: {datetime.now().strftime('%d.%m.%Y %H:%M')}", 
                 align="L", w=100)
        
        # Номер страницы справа
        page_text = f"Стр. {self.page_no()}"
        self.cell(0, 10, page_text, align="R")


def generate_pdf(df: pd.DataFrame, upload_id: Optional[int] = None) -> bytes:
    """
    Генерирует PDF отчет с метриками и таблицей продаж.
    
    Args:
        df: pandas DataFrame с колонками (date, product, category, amount, quantity)
        upload_id: ID загрузки (опционально, для справки)
    
    Returns:
        bytes: PDF документ в формате байтов
    """
    
    # Проверяем требуемые столбцы
    required_cols = {'date', 'product', 'category', 'amount', 'quantity'}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"DataFrame должен содержать столбцы: {required_cols}")
    
    # Убеждаемся, что дата в формате datetime
    if not pd.api.types.is_datetime64_any_dtype(df['date']):
        df['date'] = pd.to_datetime(df['date'])
    
    # ======================== Инициализация PDF ========================
    pdf = SalesReportPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.title_str = "Отчёт по продажам"
    
    # ======================== Заголовок ========================
    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 15, "Отчёт по продажам", ln=True, align="C")
    
    # Период данных
    date_min = df['date'].min().strftime('%d.%m.%Y')
    date_max = df['date'].max().strftime('%d.%m.%Y')
    pdf.set_font("Arial", "", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, f"Период: {date_min} - {date_max}", ln=True, align="C")
    
    if upload_id:
        pdf.cell(0, 5, f"ID загрузки: {upload_id}", ln=True, align="C")
    
    pdf.ln(5)  # Отступ
    
    # ======================== Ключевые метрики ========================
    pdf.set_font("Arial", "B", 13)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "Ключевые показатели", ln=True)
    
    # Вычисляем метрики
    total_revenue = df['amount'].sum()
    total_transactions = len(df)
    unique_products = df['product'].nunique()
    unique_categories = df['category'].nunique()
    total_quantity = int(df['quantity'].sum())
    avg_check = total_revenue / total_transactions if total_transactions > 0 else 0
    
    # Метрики в виде таблицы (2 колонки)
    pdf.set_font("Arial", "", 10)
    
    # Ширина колонок для метрик
    col_width = 90
    row_height = 8
    
    # Фон для таблицы метрик
    pdf.set_fill_color(220, 220, 220)
    
    # Метрика 1: Общая выручка
    pdf.cell(col_width, row_height, "Общая выручка:", border=1, fill=False)
    pdf.cell(col_width, row_height, f"₽ {total_revenue:,.2f}", border=1, ln=True, fill=False)
    
    # Метрика 2: Транзакции
    pdf.cell(col_width, row_height, "Всего транзакций:", border=1, fill=False)
    pdf.cell(col_width, row_height, f"{total_transactions}", border=1, ln=True, fill=False)
    
    # Метрика 3: Товары
    pdf.cell(col_width, row_height, "Уникальные товары:", border=1, fill=False)
    pdf.cell(col_width, row_height, f"{unique_products}", border=1, ln=True, fill=False)
    
    # Метрика 4: Категории
    pdf.cell(col_width, row_height, "Категории:", border=1, fill=False)
    pdf.cell(col_width, row_height, f"{unique_categories}", border=1, ln=True, fill=False)
    
    # Метрика 5: Среднее
    pdf.cell(col_width, row_height, "Средний чек:", border=1, fill=False)
    pdf.cell(col_width, row_height, f"₽ {avg_check:,.2f}", border=1, ln=True, fill=False)
    
    # Метрика 6: Количество
    pdf.cell(col_width, row_height, "Всего единиц:", border=1, fill=False)
    pdf.cell(col_width, row_height, f"{total_quantity}", border=1, ln=True, fill=False)
    
    pdf.ln(8)  # Отступ после таблицы
    
    # ======================== Таблица Топ-10 товаров ========================
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 10, "Топ-10 товаров по выручке", ln=True)
    
    # Вычисляем топ товаров
    top_products = (
        df.groupby('product')
        .agg({'amount': 'sum', 'quantity': 'sum'})
        .sort_values('amount', ascending=False)
        .head(10)
        .reset_index()
    )
    
    # Заголовки таблицы
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(25, 110, 180)  # Синий фон
    pdf.set_text_color(255, 255, 255)  # Белый текст
    
    # Ширины колонок
    col_widths = [70, 40, 40]  # Товар, Выручка, Кол-во
    
    # Заголовки
    pdf.cell(col_widths[0], 8, "Товар", border=1, fill=True)
    pdf.cell(col_widths[1], 8, "Выручка", border=1, fill=True, align="R")
    pdf.cell(col_widths[2], 8, "Кол-во", border=1, fill=True, align="R", ln=True)
    
    # Строки таблицы
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(0, 0, 0)
    
    row_height = 7
    for idx, row in top_products.iterrows():
        # Чередуем цвет фона для лучшей читаемости
        if idx % 2 == 0:
            pdf.set_fill_color(245, 245, 245)
            fill = True
        else:
            fill = False
        
        # Название товара (обрезаем если длинное)
        product_name = str(row['product'])[:60]
        pdf.cell(col_widths[0], row_height, product_name, border=1, fill=fill)
        
        # Выручка
        revenue_str = f"₽ {row['amount']:,.0f}"
        pdf.cell(col_widths[1], row_height, revenue_str, border=1, fill=fill, align="R")
        
        # Количество
        qty_str = f"{int(row['quantity'])}"
        pdf.cell(col_widths[2], row_height, qty_str, border=1, fill=fill, align="R", ln=True)
    
    # ======================== Категориев разбивка ========================
    pdf.ln(8)
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 10, "Распределение по категориям", ln=True)
    
    # Вычисляем категории
    categories = (
        df.groupby('category')
        .agg({'amount': 'sum', 'quantity': 'sum'})
        .sort_values('amount', ascending=False)
        .reset_index()
    )
    
    # Заголовки таблицы категорий
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(25, 110, 180)
    pdf.set_text_color(255, 255, 255)
    
    col_widths_cat = [70, 40, 40]
    
    pdf.cell(col_widths_cat[0], 8, "Категория", border=1, fill=True)
    pdf.cell(col_widths_cat[1], 8, "Выручка", border=1, fill=True, align="R")
    pdf.cell(col_widths_cat[2], 8, "% от всего", border=1, fill=True, align="R", ln=True)
    
    # Строки таблицы категорий
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(0, 0, 0)
    
    total_cat_revenue = categories['amount'].sum()
    
    for idx, row in categories.iterrows():
        if idx % 2 == 0:
            pdf.set_fill_color(245, 245, 245)
            fill = True
        else:
            fill = False
        
        # Название категории
        category_name = str(row['category'])[:60]
        pdf.cell(col_widths_cat[0], row_height, category_name, border=1, fill=fill)
        
        # Выручка
        revenue_str = f"₽ {row['amount']:,.0f}"
        pdf.cell(col_widths_cat[1], row_height, revenue_str, border=1, fill=fill, align="R")
        
        # Процент
        pct = (row['amount'] / total_cat_revenue * 100) if total_cat_revenue > 0 else 0
        pct_str = f"{pct:.1f}%"
        pdf.cell(col_widths_cat[2], row_height, pct_str, border=1, fill=fill, align="R", ln=True)
    
    # ======================== Примечание в конце ========================
    pdf.ln(10)
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(128, 128, 128)
    pdf.multi_cell(0, 5, 
        "Данный отчет был автоматически сгенерирован системой аналитики продаж. "
        "Все цифры основаны на загруженных данных.")
    
    # ======================== Возвращаем PDF как байты ========================
    # Сохраняем в BytesIO вместо файла
    pdf_output = BytesIO()
    pdf_bytes = pdf.output()
    
    return pdf_bytes
