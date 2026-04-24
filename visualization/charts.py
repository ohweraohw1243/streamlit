"""
Интерактивные диаграммы на Plotly Express для аналитического приложения.
Каждая функция принимает DataFrame и возвращает plotly Figure с красивым оформлением.
"""

import pandas as pd
import plotly.express as px
from typing import Optional


# Единая цветовая палитра для всех диаграмм
COLOR_PALETTE = px.colors.qualitative.Set2
PRIMARY_COLOR = '#1f77b4'
SECONDARY_COLOR = '#ff7f0e'


def revenue_over_time(df: pd.DataFrame) -> px.line:
    """
    Создает линейный график дневной выручки.
    
    Args:
        df: DataFrame с колонками 'date' (datetime) и 'amount' (float)
    
    Returns:
        plotly.graph_objects.Figure: линейный график выручки по дням
    """
    # Проверяем наличие требуемых столбцов
    if 'date' not in df.columns or 'amount' not in df.columns:
        raise ValueError("DataFrame должен содержать столбцы 'date' и 'amount'")
    
    # Группируем данные по датам, суммируем сумму продаж
    daily_revenue = df.groupby('date')['amount'].sum().reset_index()
    daily_revenue.columns = ['Дата', 'Выручка']
    
    # Создаем линейный график
    fig = px.line(
        daily_revenue,
        x='Дата',
        y='Выручка',
        markers=True,  # Добавляем точки на линию
        title='Выручка по дням',
        labels={'Выручка': 'Сумма, руб.', 'Дата': 'Дата'},
        line_shape='linear'
    )
    
    # Применяем стиль: белый фон, первичный цвет, аккуратные оси
    fig.update_traces(
        line=dict(color=PRIMARY_COLOR, width=3),
        marker=dict(size=8, color=PRIMARY_COLOR)
    )
    
    fig.update_layout(
        template='plotly_white',  # Белый фон, убирает линии сетки
        hovermode='x unified',  # Единый hovermode для всех трасс
        height=450,
        font=dict(size=12),
        xaxis_title='Дата',
        yaxis_title='Выручка, руб.'
    )
    
    return fig


def top_products(df: pd.DataFrame, n: int = 10) -> px.bar:
    """
    Создает горизонтальную диаграмму топ N товаров по выручке.
    
    Args:
        df: DataFrame с колонками 'product' (str) и 'amount' (float)
        n: количество товаров для отображения (по умолчанию 10)
    
    Returns:
        plotly.graph_objects.Figure: горизонтальная столбчатая диаграмма
    """
    # Проверяем наличие требуемых столбцов
    if 'product' not in df.columns or 'amount' not in df.columns:
        raise ValueError("DataFrame должен содержать столбцы 'product' и 'amount'")
    
    # Группируем товары, суммируем выручку, берем топ N
    top_products_data = (
        df.groupby('product')['amount']
        .sum()
        .sort_values(ascending=True)  # ascending для горизонтальной диаграммы
        .tail(n)
        .reset_index()
    )
    top_products_data.columns = ['Товар', 'Выручка']
    
    # Создаем горизонтальную столбчатую диаграмму
    fig = px.bar(
        top_products_data,
        x='Выручка',
        y='Товар',
        orientation='h',  # Горизонтальная ориентация
        title=f'Топ {n} товаров по выручке',
        labels={'Выручка': 'Сумма, руб.', 'Товар': 'Наименование'},
        text='Выручка'  # Показываем значения на столбцах
    )
    
    # Применяем стиль и форматируем текст
    fig.update_traces(
        marker_color=SECONDARY_COLOR,
        textposition='outside',  # Текст за пределами столбца
        textfont=dict(size=10)  # Шрифт для текста
    )
    
    fig.update_layout(
        template='plotly_white',
        height=400 + n * 20,  # Высота зависит от количества товаров
        xaxis_title='Выручка, руб.',
        yaxis_title='',
        showlegend=False,
        hovermode='closest'
    )
    
    return fig


def category_breakdown(df: pd.DataFrame) -> px.pie:
    """
    Создает круговую диаграмму распределения выручки по категориям.
    
    Args:
        df: DataFrame с колонками 'category' (str) и 'amount' (float)
    
    Returns:
        plotly.graph_objects.Figure: круговая диаграмма
    """
    # Проверяем наличие требуемых столбцов
    if 'category' not in df.columns or 'amount' not in df.columns:
        raise ValueError("DataFrame должен содержать столбцы 'category' и 'amount'")
    
    # Группируем категории, суммируем выручку
    category_data = (
        df.groupby('category')['amount']
        .sum()
        .reset_index()
    )
    category_data.columns = ['Категория', 'Выручка']
    
    # Создаем круговую диаграмму
    fig = px.pie(
        category_data,
        values='Выручка',
        names='Категория',
        title='Распределение выручки по категориям',
        color_discrete_sequence=COLOR_PALETTE,
        hole=0  # 0 для полной круговой диаграммы (без дырки в центре)
    )
    
    # Применяем стиль: убираем сетку, настраиваем текст
    fig.update_traces(
        textposition='inside',  # Текст внутри секторов
        textinfo='label+percent',  # Показываем название и процент
        hovertemplate='<b>%{label}</b><br>Выручка: %{value:,.0f} руб.<br>Доля: %{percent}<extra></extra>'
    )
    
    fig.update_layout(
        template='plotly_white',
        height=450,
        font=dict(size=11),
        showlegend=True,
        legend=dict(orientation='v', yanchor='middle', y=0.5, xanchor='left', x=1.05)
    )
    
    return fig


def monthly_comparison(df: pd.DataFrame) -> px.bar:
    """
    Создает столбчатую диаграмму сравнения выручки по месяцам.
    
    Args:
        df: DataFrame с колонкой 'date' (datetime) и 'amount' (float)
    
    Returns:
        plotly.graph_objects.Figure: вертикальная столбчатая диаграмма
    """
    # Проверяем наличие требуемых столбцов
    if 'date' not in df.columns or 'amount' not in df.columns:
        raise ValueError("DataFrame должен содержать столбцы 'date' и 'amount'")
    
    # Убеждаемся, что дата в формате datetime
    if not pd.api.types.is_datetime64_any_dtype(df['date']):
        df['date'] = pd.to_datetime(df['date'])
    
    # Извлекаем год и месяц, группируем данные
    df_copy = df.copy()
    df_copy['YearMonth'] = df_copy['date'].dt.to_period('M')
    
    monthly_revenue = (
        df_copy.groupby('YearMonth')['amount']
        .sum()
        .reset_index()
    )
    # Преобразуем Period обратно в строку для отображения
    monthly_revenue['Месяц'] = monthly_revenue['YearMonth'].astype(str)
    monthly_revenue = monthly_revenue[['Месяц', 'amount']].rename(columns={'amount': 'Выручка'})
    
    # Создаем столбчатую диаграмму
    fig = px.bar(
        monthly_revenue,
        x='Месяц',
        y='Выручка',
        title='Выручка по месяцам',
        labels={'Выручка': 'Сумма, руб.', 'Месяц': 'Месяц'},
        text='Выручка'  # Показываем значения на столбцах
    )
    
    # Применяем стиль и форматируем текст
    fig.update_traces(
        marker_color=PRIMARY_COLOR,
        textposition='outside',  # Текст над столбцом
        textfont=dict(size=10)  # Шрифт для текста
    )
    
    fig.update_layout(
        template='plotly_white',
        height=450,
        xaxis_title='Месяц',
        yaxis_title='Выручка, руб.',
        hovermode='x',
        showlegend=False
    )
    
    return fig
