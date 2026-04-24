"""
Генератор PDF отчетов на fpdf2 для аналитического приложения.
Создает профессиональные отчеты с метриками и таблицами.
Использует встроенные шрифты FPDF для совместимости.
"""

from fpdf import FPDF
from datetime import datetime
import pandas as pd
from pathlib import Path
from typing import Optional


def add_unicode_fonts_if_available(pdf: FPDF) -> bool:
    """
    Пытается добавить Unicode шрифты для поддержки кириллицы.
    Возвращает True если успешно, False если используются встроенные шрифты.
    """
    # Общие пути к DejaVu шрифтам
    font_paths = [
        Path("/System/Library/Fonts"),
        Path("/Library/Fonts"),
        Path.home() / "Library" / "Fonts",
        Path("/usr/share/fonts/truetype/dejavu"),
        Path("/usr/share/fonts/opentype/dejavu"),
    ]
    
    for font_dir in font_paths:
        if not font_dir.exists():
            continue
        
        regular = font_dir / "DejaVuSans.ttf"
        bold = font_dir / "DejaVuSans-Bold.ttf"
        
        if regular.exists():
            try:
                pdf.add_font("DejaVu", "", str(regular), uni=True)
                if bold.exists():
                    pdf.add_font("DejaVu", "B", str(bold), uni=True)
                return True
            except Exception:
                pass
    
    return False


def transliterate_to_latin(text: str) -> str:
    """
    Конвертирует русский текст в латинскую транслитерацию.
    Используется когда Unicode шрифты недоступны.
    """
    transliteration_table = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
        'е': 'e', 'ё': 'e', 'ж': 'zh', 'з': 'z', 'и': 'i',
        'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
        'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
        'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch',
        'ш': 'sh', 'щ': 'sch', 'ъ': '', 'ы': 'y', 'ь': '',
        'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D',
        'Е': 'E', 'Ё': 'E', 'Ж': 'Zh', 'З': 'Z', 'И': 'I',
        'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N',
        'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T',
        'У': 'U', 'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch',
        'Ш': 'Sh', 'Щ': 'Sch', 'Ъ': '', 'Ы': 'Y', 'Ь': '',
        'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
    }
    
    result = []
    for char in text:
        if char in transliteration_table:
            result.append(transliteration_table[char])
        else:
            result.append(char)
    
    return ''.join(result)


class SalesReportPDF(FPDF):
    """
    Пользовательский класс PDF с заголовками и подвалом.
    """
    
    def __init__(self, font_family: str = "Courier"):
        super().__init__()
        self.font_family = font_family
        self.page_title = "SALES REPORT"
        self.unicode_enabled = False
    
    def header(self):
        """Заголовок на каждой странице."""
        self.set_font(self.font_family, "B", 14)
        self.cell(0, 10, self.page_title, ln=True, align="C")
        self.ln(2)
    
    def footer(self):
        """Подвал на каждой странице."""
        self.set_y(-15)
        self.set_font(self.font_family, "I", 8)
        
        # Дата
        date_text = datetime.now().strftime("Created: %d.%m.%Y %H:%M")
        self.cell(100, 10, date_text, 0, 0, "L")
        
        # Номер страницы
        page_text = f"Page {self.page_no()}"
        self.cell(0, 10, page_text, 0, 1, "R")


def generate_pdf(df: pd.DataFrame, upload_id: Optional[int] = None) -> bytes:
    """
    Генерирует PDF отчет с метриками и таблицей продаж.
    
    Args:
        df: DataFrame с колонками (date, product, category, amount, quantity)
        upload_id: ID загрузки (опционально)
    
    Returns:
        bytes: PDF документ в формате байтов
    """
    
    # Проверяем столбцы
    required_cols = {"date", "product", "category", "amount", "quantity"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"DataFrame должен содержать столбцы: {required_cols}")
    
    # Преобразуем дату
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"])
    
    # ======================== Создаем PDF ========================
    pdf = SalesReportPDF()
    
    # ВАЖНО: Добавляем шрифты ДО add_page()
    # Пытаемся добавить Unicode шрифты
    has_unicode = add_unicode_fonts_if_available(pdf)
    
    if has_unicode:
        font_to_use = "DejaVu"
    else:
        # Если Unicode не доступен, используем встроенный Courier
        font_to_use = "Courier"
    
    pdf.font_family = font_to_use
    pdf.unicode_enabled = has_unicode
    
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # ======================== Заголовок ========================
    pdf.set_font(font_to_use, "B", 18)
    pdf.cell(0, 15, "SALES REPORT", ln=True, align="C")
    
    # Период
    date_min = df["date"].min().strftime("%d.%m.%Y")
    date_max = df["date"].max().strftime("%d.%m.%Y")
    pdf.set_font(font_to_use, "", 11)
    pdf.cell(0, 8, f"Period: {date_min} - {date_max}", ln=True, align="C")
    
    if upload_id:
        pdf.cell(0, 5, f"Upload ID: {upload_id}", ln=True, align="C")
    
    pdf.ln(5)
    
    # ======================== Метрики ========================
    pdf.set_font(font_to_use, "B", 12)
    pdf.cell(0, 10, "KEY METRICS", ln=True)
    
    # Вычисляем метрики
    total_revenue = df["amount"].sum()
    total_transactions = len(df)
    unique_products = df["product"].nunique()
    unique_categories = df["category"].nunique()
    total_quantity = int(df["quantity"].sum())
    avg_check = total_revenue / total_transactions if total_transactions > 0 else 0
    
    # Таблица метрик
    pdf.set_font(font_to_use, "", 10)
    col_width = 90
    row_height = 8
    
    pdf.set_fill_color(220, 220, 220)
    
    metrics_data = [
        ("Total Revenue", f"${total_revenue:,.2f}"),
        ("Transactions", f"{total_transactions}"),
        ("Unique Products", f"{unique_products}"),
        ("Categories", f"{unique_categories}"),
        ("Avg Check", f"${avg_check:,.2f}"),
        ("Total Units", f"{total_quantity}"),
    ]
    
    for label, value in metrics_data:
        pdf.cell(col_width, row_height, label, border=1)
        pdf.cell(col_width, row_height, value, border=1, ln=True)
    
    pdf.ln(8)
    
    # ======================== Топ товаров ========================
    pdf.set_font(font_to_use, "B", 12)
    pdf.cell(0, 10, "TOP 10 PRODUCTS", ln=True)
    
    top_products = (
        df.groupby("product")["amount"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )
    
    # Заголовки таблицы
    pdf.set_font(font_to_use, "B", 10)
    pdf.set_fill_color(25, 110, 180)
    pdf.set_text_color(255, 255, 255)
    
    col_widths = [70, 40, 40]
    pdf.cell(col_widths[0], 8, "Product", border=1, fill=True)
    pdf.cell(col_widths[1], 8, "Revenue", border=1, fill=True, align="R")
    pdf.cell(col_widths[2], 8, "Amount", border=1, fill=True, align="R", ln=True)
    
    # Строки таблицы
    pdf.set_font(font_to_use, "", 9)
    pdf.set_text_color(0, 0, 0)
    
    for idx, row in top_products.iterrows():
        if idx % 2 == 0:
            pdf.set_fill_color(245, 245, 245)
            fill = True
        else:
            fill = False
        
        product_name = str(row["product"])[:60]
        # Если нет Unicode, конвертируем в латиницу
        if not has_unicode:
            product_name = transliterate_to_latin(product_name)
        
        pdf.cell(col_widths[0], 7, product_name, border=1, fill=fill)
        
        revenue_str = f"${row['amount']:,.0f}"
        pdf.cell(col_widths[1], 7, revenue_str, border=1, fill=fill, align="R")
        
        pdf.cell(col_widths[2], 7, "1", border=1, fill=fill, align="R", ln=True)
    
    pdf.ln(8)
    
    # ======================== Категории ========================
    pdf.set_font(font_to_use, "B", 12)
    pdf.cell(0, 10, "BY CATEGORY", ln=True)
    
    categories = (
        df.groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    
    pdf.set_font(font_to_use, "B", 10)
    pdf.set_fill_color(25, 110, 180)
    pdf.set_text_color(255, 255, 255)
    
    col_widths_cat = [70, 40, 40]
    pdf.cell(col_widths_cat[0], 8, "Category", border=1, fill=True)
    pdf.cell(col_widths_cat[1], 8, "Revenue", border=1, fill=True, align="R")
    pdf.cell(col_widths_cat[2], 8, "% of Total", border=1, fill=True, align="R", ln=True)
    
    pdf.set_font(font_to_use, "", 9)
    pdf.set_text_color(0, 0, 0)
    
    total_cat_revenue = categories["amount"].sum()
    
    for idx, row in categories.iterrows():
        if idx % 2 == 0:
            pdf.set_fill_color(245, 245, 245)
            fill = True
        else:
            fill = False
        
        cat_name = str(row["category"])[:60]
        # Если нет Unicode, конвертируем в латиницу
        if not has_unicode:
            cat_name = transliterate_to_latin(cat_name)
        
        pdf.cell(col_widths_cat[0], 7, cat_name, border=1, fill=fill)
        
        revenue_str = f"${row['amount']:,.0f}"
        pdf.cell(col_widths_cat[1], 7, revenue_str, border=1, fill=fill, align="R")
        
        pct = (row["amount"] / total_cat_revenue * 100) if total_cat_revenue > 0 else 0
        pdf.cell(col_widths_cat[2], 7, f"{pct:.1f}%", border=1, fill=fill, align="R", ln=True)
    
    pdf.ln(10)
    pdf.set_font(font_to_use, "I", 8)
    pdf.set_text_color(128, 128, 128)
    pdf.multi_cell(
        0, 
        5, 
        "This report was automatically generated by the Sales Analytics System. "
        "All figures are based on the uploaded data."
    )
    
    # Возвращаем PDF как байты
    return pdf.output()
