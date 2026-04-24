"""
Основное Streamlit приложение для аналитического дашборда.
Содержит UI для загрузки файлов, отображения метрик и интерактивных графиков.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from data.db_manager import init_db, save_dataframe, get_data, list_uploads, get_upload_stats
from data.parser import parse_excel
from visualization.charts import revenue_over_time, top_products, category_breakdown, monthly_comparison
from reports.pdf_generator import generate_pdf


# ======================== Инициализация ========================
# Инициализируем базу данных при первом запуске
if 'db_initialized' not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

# Инициализируем переменные сессии для отслеживания загружаемого набора данных
if 'current_upload_id' not in st.session_state:
    st.session_state.current_upload_id = None

if 'current_df' not in st.session_state:
    st.session_state.current_df = None


# ======================== Конфигурация страницы ========================
st.set_page_config(
    page_title="Аналитика продаж",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Применяем пользовательский CSS для лучшего внешнего вида
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .metric-value {
        font-size: 28px;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-label {
        font-size: 14px;
        color: #666;
        margin-top: 5px;
    }
    </style>
""", unsafe_allow_html=True)


# ======================== Боковая панель (Sidebar) ========================
with st.sidebar:
    st.header("📁 Загрузка данных")
    
    # Загрузчик файлов
    uploaded_file = st.file_uploader(
        "Выберите файл Excel или CSV",
        type=['xlsx', 'csv', 'xls'],
        label_visibility='collapsed'
    )
    
    # Кнопка загрузки файла
    if st.button("Загрузить", use_container_width=True, type='primary'):
        if uploaded_file is not None:
            # Показываем спиннер во время обработки
            with st.spinner("⏳ Обработка файла..."):
                try:
                    # Парсим файл с нормализацией столбцов
                    df = parse_excel(uploaded_file)
                    
                    # Сохраняем в базу данных
                    upload_id = save_dataframe(df, uploaded_file.name)
                    
                    # Сохраняем в сессию
                    st.session_state.current_upload_id = upload_id
                    st.session_state.current_df = df
                    
                    # Успешное сообщение
                    st.success(f"✅ Файл загружен успешно! Загружено {len(df)} строк.")
                
                except ValueError as e:
                    # Ошибка валидации данных
                    st.error(f"❌ Ошибка в данных: {e}")
                except Exception as e:
                    # Прочие ошибки
                    st.error(f"❌ Ошибка при обработке файла: {e}")
        else:
            st.warning("⚠️ Пожалуйста, выберите файл перед загрузкой")
    
    # Разделитель
    st.divider()
    
    # Выпадающий список предыдущих загрузок
    st.subheader("📋 Предыдущие загрузки")
    uploads = list_uploads()
    
    if not uploads.empty:
        # Создаем строку выбора в формате "Дата - Файл (N строк)"
        upload_options = [
            f"{row['uploaded_at'][:10]} - {row['filename']} ({row['row_count']} строк)"
            for _, row in uploads.iterrows()
        ]
        
        selected_upload = st.selectbox(
            "Выберите загрузку",
            range(len(uploads)),
            format_func=lambda i: upload_options[i],
            label_visibility='collapsed'
        )
        
        # Кнопка для загрузки выбранной загрузки
        if st.button("Загрузить выбранные данные", use_container_width=True):
            selected_id = uploads.iloc[selected_upload]['id']
            st.session_state.current_upload_id = selected_id
            st.session_state.current_df = get_data(selected_id)
            st.success("✅ Данные загружены из истории")
    else:
        st.info("📭 Нет сохраненных загрузок. Загрузите файл чтобы начать.")


# ======================== Главная область ========================
st.title("📊 Аналитика продаж")

# Проверяем, есть ли текущие данные для отображения
if st.session_state.current_df is None or st.session_state.current_df.empty:
    st.info("👈 Загрузите файл через панель слева чтобы начать анализ")
else:
    df = st.session_state.current_df
    
    # ======================== Метрические карточки ========================
    # Вычисляем метрики
    total_revenue = df['amount'].sum()
    total_transactions = len(df)
    unique_products = df['product'].nunique()
    date_range = f"{df['date'].min().strftime('%d.%m.%Y')} - {df['date'].max().strftime('%d.%m.%Y')}"
    
    # Создаем 4 колонки для метрик
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💰 Общая выручка",
            value=f"₽ {total_revenue:,.0f}",
            delta=None
        )
    
    with col2:
        st.metric(
            label="📝 Всего транзакций",
            value=f"{total_transactions:,}",
            delta=None
        )
    
    with col3:
        st.metric(
            label="📦 Уникальные товары",
            value=f"{unique_products}",
            delta=None
        )
    
    with col4:
        st.metric(
            label="📅 Период данных",
            value=date_range,
            delta=None
        )
    
    # Разделитель
    st.divider()
    
    # ======================== Сетка с 4 диаграммами (2x2) ========================
    st.subheader("📈 Основные показатели")
    
    # Первая строка: 2 графика
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        # График 1: Выручка по дням
        try:
            fig_revenue = revenue_over_time(df)
            st.plotly_chart(fig_revenue, use_container_width=True)
        except Exception as e:
            st.error(f"Ошибка при отрисовке графика выручки: {e}")
    
    with chart_col2:
        # График 2: Топ товаров
        try:
            fig_products = top_products(df, n=10)
            st.plotly_chart(fig_products, use_container_width=True)
        except Exception as e:
            st.error(f"Ошибка при отрисовке графика товаров: {e}")
    
    # Вторая строка: 2 графика
    chart_col3, chart_col4 = st.columns(2)
    
    with chart_col3:
        # График 3: Распределение по категориям
        try:
            fig_category = category_breakdown(df)
            st.plotly_chart(fig_category, use_container_width=True)
        except Exception as e:
            st.error(f"Ошибка при отрисовке графика категорий: {e}")
    
    with chart_col4:
        # График 4: Выручка по месяцам
        try:
            fig_monthly = monthly_comparison(df)
            st.plotly_chart(fig_monthly, use_container_width=True)
        except Exception as e:
            st.error(f"Ошибка при отрисовке графика по месяцам: {e}")
    
    # ======================== Скачивание PDF отчета ========================
    st.divider()
    
    # Создаем колонки для центрирования кнопки
    pdf_col1, pdf_col2, pdf_col3 = st.columns([1, 2, 1])
    
    with pdf_col2:
        # Генерируем PDF и предоставляем кнопку скачивания
        try:
            pdf_bytes = generate_pdf(df, st.session_state.current_upload_id)
            
            st.download_button(
                label="📥 Скачать PDF отчёт",
                data=pdf_bytes,
                file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"❌ Ошибка при создании PDF отчета: {e}")
    
    # ======================== Дополнительная информация ========================
    st.subheader("📊 Детальная таблица данных")
    
    # Позволяем пользователю отфильтровать данные по категории
    categories = df['category'].unique()
    selected_category = st.selectbox(
        "Фильтр по категории",
        ['Все категории'] + list(categories)
    )
    
    # Применяем фильтр
    if selected_category != 'Все категории':
        filtered_df = df[df['category'] == selected_category]
    else:
        filtered_df = df
    
    # Отображаем таблицу
    st.dataframe(
        filtered_df.sort_values('date', ascending=False),
        use_container_width=True,
        hide_index=True
    )
    
    # Показываем статистику по текущему набору данных
    if selected_category != 'Все категории':
        st.info(
            f"📌 Выбрана категория '{selected_category}': "
            f"{len(filtered_df)} транзакций, сумма: ₽ {filtered_df['amount'].sum():,.0f}"
        )
