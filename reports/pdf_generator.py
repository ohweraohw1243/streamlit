"""Генератор PDF-отчетов на fpdf2 с полной поддержкой кириллицы."""

from datetime import datetime
from pathlib import Path
from typing import Optional
import shutil
import ssl
import urllib.request

import pandas as pd
from fpdf import FPDF


def format_rub(value: float, digits: int = 2, currency: str = "₽") -> str:
    """Форматирует число в рубли с пробелом как разделителем тысяч."""
    formatted = f"{value:,.{digits}f}".replace(",", " ").replace(".", ",")
    return f"{formatted} {currency}"


def ensure_unicode_font(fonts_dir: Path) -> Path:
    """Ищет или скачивает Unicode TTF-шрифт для кириллицы и возвращает путь."""
    fonts_dir.mkdir(exist_ok=True)

    # 0) Если в проекте уже лежит нужный шрифт
    font_path = fonts_dir / "DejaVuSans.ttf"
    if font_path.exists():
        return font_path

    font_url = "https://github.com/dejavu-fonts/dejavu-fonts/raw/main/ttf/DejaVuSans.ttf"

    # 1) Стандартная загрузка с проверкой сертификата
    try:
        urllib.request.urlretrieve(font_url, font_path)
        if font_path.exists():
            return font_path
    except Exception:
        pass

    # 2) Fallback для окружений с проблемным сертификатным хранилищем
    try:
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(font_url, context=context, timeout=30) as response:
            font_path.write_bytes(response.read())
        if font_path.exists():
            return font_path
    except Exception:
        pass

    # 3) Локальные системные пути как последний резерв
    system_candidates = [
        Path.home() / "Library" / "Fonts" / "DejaVuSans.ttf",
        Path.home() / "Library" / "Fonts" / "NotoSans-Regular.ttf",
        Path.home() / "Library" / "Fonts" / "Arial Unicode.ttf",
        Path("/Library/Fonts/DejaVuSans.ttf"),
        Path("/Library/Fonts/NotoSans-Regular.ttf"),
        Path("/Library/Fonts/Arial Unicode.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/System/Library/Fonts/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/opentype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"),
    ]
    for candidate in system_candidates:
        if candidate.exists():
            shutil.copyfile(candidate, font_path)
            return font_path

    raise RuntimeError(
        "Не удалось найти Unicode-шрифт для кириллицы. Добавьте файл DejaVuSans.ttf в папку reports/fonts/."
    )


class SalesReportPDF(FPDF):
    """Пользовательский класс PDF с заголовком и подвалом."""

    def __init__(self, font_family: str = "DejaVu"):
        super().__init__()
        self.font_family = font_family
        self.page_title = "ОТЧЁТ ПО ПРОДАЖАМ"
    
    def header(self):
        """Заголовок на каждой странице."""
        self.set_font(self.font_family, "", 14)
        self.cell(0, 10, self.page_title, ln=True, align="C")
        self.ln(2)
    
    def footer(self):
        """Подвал на каждой странице."""
        self.set_y(-15)
        self.set_font(self.font_family, "", 8)

        date_text = datetime.now().strftime("Сформирован: %d.%m.%Y %H:%M")
        self.cell(100, 10, date_text, 0, 0, "L")

        page_text = f"Стр. {self.page_no()}"
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
    
    pdf = SalesReportPDF()

    fonts_dir = Path(__file__).parent / "fonts"
    font_path = ensure_unicode_font(fonts_dir)
    pdf.add_font("DejaVu", "", str(font_path))
    pdf.font_family = "DejaVu"
    pdf.page_title = "ОТЧЁТ ПО ПРОДАЖАМ"
    pdf.set_font(pdf.font_family, size=12)
    
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # ======================== Заголовок ========================
    pdf.set_font(pdf.font_family, "", 18)
    pdf.cell(0, 15, "ОТЧЁТ ПО ПРОДАЖАМ", ln=True, align="C")
    
    # Период
    date_min = df["date"].min().strftime("%d.%m.%Y")
    date_max = df["date"].max().strftime("%d.%m.%Y")
    pdf.set_font(pdf.font_family, "", 11)
    pdf.cell(0, 8, f"Период: {date_min} - {date_max}", ln=True, align="C")
    
    if upload_id:
        pdf.cell(0, 5, f"ID загрузки: {upload_id}", ln=True, align="C")
    
    pdf.ln(5)
    
    # ======================== Метрики ========================
    pdf.set_font(pdf.font_family, "", 12)
    pdf.cell(0, 10, "КЛЮЧЕВЫЕ ПОКАЗАТЕЛИ", ln=True)
    
    # Вычисляем метрики
    total_revenue = df["amount"].sum()
    total_transactions = len(df)
    unique_products = df["product"].nunique()
    unique_categories = df["category"].nunique()
    total_quantity = int(df["quantity"].sum())
    avg_check = total_revenue / total_transactions if total_transactions > 0 else 0
    
    # Таблица метрик
    pdf.set_font(pdf.font_family, "", 10)
    col_width = 90
    row_height = 8
    
    pdf.set_fill_color(220, 220, 220)
    
    metrics_data = [
        ("Общая выручка", format_rub(total_revenue, 2, "₽")),
        ("Транзакции", f"{total_transactions}"),
        ("Уникальные товары", f"{unique_products}"),
        ("Категории", f"{unique_categories}"),
        ("Средний чек", format_rub(avg_check, 2, "₽")),
        ("Единиц продано", f"{total_quantity}"),
    ]
    
    for label, value in metrics_data:
        pdf.cell(col_width, row_height, label, border=1)
        pdf.cell(col_width, row_height, value, border=1, ln=True)
    
    pdf.ln(8)
    
    # ======================== Топ товаров ========================
    pdf.set_font(pdf.font_family, "", 12)
    pdf.cell(0, 10, "ТОП 10 ТОВАРОВ", ln=True)
    
    top_products = (
        df.groupby("product", as_index=False)
        .agg({"amount": "sum", "quantity": "sum"})
        .sort_values("amount", ascending=False)
        .head(10)
    )
    
    # Заголовки таблицы
    pdf.set_font(pdf.font_family, "", 10)
    pdf.set_fill_color(25, 110, 180)
    pdf.set_text_color(255, 255, 255)
    
    col_widths = [70, 40, 40]
    pdf.cell(col_widths[0], 8, "Товар", border=1, fill=True)
    pdf.cell(col_widths[1], 8, "Выручка", border=1, fill=True, align="R")
    pdf.cell(col_widths[2], 8, "Количество", border=1, fill=True, align="R", ln=True)
    
    # Строки таблицы
    pdf.set_font(pdf.font_family, "", 9)
    pdf.set_text_color(0, 0, 0)
    
    for idx, row in top_products.iterrows():
        if idx % 2 == 0:
            pdf.set_fill_color(245, 245, 245)
            fill = True
        else:
            fill = False
        
        product_name = str(row["product"])[:60]
        
        pdf.cell(col_widths[0], 7, product_name, border=1, fill=fill)
        
        revenue_str = format_rub(float(row["amount"]), 0, "₽")
        pdf.cell(col_widths[1], 7, revenue_str, border=1, fill=fill, align="R")

        pdf.cell(col_widths[2], 7, f"{int(row['quantity'])}", border=1, fill=fill, align="R", ln=True)
    
    pdf.ln(8)
    
    # ======================== Категории ========================
    pdf.set_font(pdf.font_family, "", 12)
    pdf.cell(0, 10, "ПО КАТЕГОРИЯМ", ln=True)
    
    categories = (
        df.groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    
    pdf.set_font(pdf.font_family, "", 10)
    pdf.set_fill_color(25, 110, 180)
    pdf.set_text_color(255, 255, 255)
    
    col_widths_cat = [70, 40, 40]
    pdf.cell(col_widths_cat[0], 8, "Категория", border=1, fill=True)
    pdf.cell(col_widths_cat[1], 8, "Выручка", border=1, fill=True, align="R")
    pdf.cell(col_widths_cat[2], 8, "Доля", border=1, fill=True, align="R", ln=True)
    
    pdf.set_font(pdf.font_family, "", 9)
    pdf.set_text_color(0, 0, 0)
    
    total_cat_revenue = categories["amount"].sum()
    
    for idx, row in categories.iterrows():
        if idx % 2 == 0:
            pdf.set_fill_color(245, 245, 245)
            fill = True
        else:
            fill = False
        
        cat_name = str(row["category"])[:60]
        
        pdf.cell(col_widths_cat[0], 7, cat_name, border=1, fill=fill)
        
        revenue_str = format_rub(float(row["amount"]), 0, "₽")
        pdf.cell(col_widths_cat[1], 7, revenue_str, border=1, fill=fill, align="R")
        
        pct = (row["amount"] / total_cat_revenue * 100) if total_cat_revenue > 0 else 0
        pdf.cell(col_widths_cat[2], 7, f"{pct:.1f}%", border=1, fill=fill, align="R", ln=True)
    
    pdf.ln(10)
    pdf.set_font(pdf.font_family, "", 8)
    pdf.set_text_color(128, 128, 128)
    pdf.multi_cell(
        0,
        5,
        "Отчёт сформирован автоматически системой аналитики продаж."
    )
    
    # Streamlit download_button принимает bytes, а fpdf2 может вернуть bytearray/str.
    pdf_data = pdf.output(dest="S")
    if isinstance(pdf_data, str):
        return pdf_data.encode("latin-1")
    return bytes(pdf_data)
