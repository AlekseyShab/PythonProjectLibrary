import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Настройка страницы
st.set_page_config(
    page_title='Дэшборд продаж',
    layout='wide'
)
st.title('Анализ продаж')
st.subheader('Исходные данные')

@st.cache_data
def load_csv_files():
    items_df = pd.read_csv('items.csv')
    orders_df = pd.read_csv('orders.csv')
    users_df = pd.read_csv('users.csv')
    return items_df, orders_df, users_df

items, orders, users = load_csv_files()
orders_users = pd.merge(orders, users, on='user_id')
full_data = pd.merge(orders_users, items, on='item_id')

# Проверка и обработка пропусков
if full_data.isnull().sum().sum() > 0:
    full_data['category'] = full_data['category'].fillna('Unknown')
    full_data['supplier'] = full_data['supplier'].fillna('Unknown')
    full_data['price_per_unit'] = full_data['price_per_unit'].fillna(0)

# Приведение типов данных
full_data['order_date'] = pd.to_datetime(full_data['order_date'], errors='coerce')
full_data['registration_date'] = pd.to_datetime(full_data['registration_date'], errors='coerce')

numeric_columns = ['quantity', 'price_per_unit', 'base_price']
for col in numeric_columns:
    if col in full_data.columns:
        full_data[col] = pd.to_numeric(full_data[col], errors='coerce')

print("Типы данных после обработки:")
print(full_data.dtypes)
print(f"Пропусков после обработки: {full_data.isnull().sum().sum()}")

print(f"Товары: {items.shape[0]:,} записей")
print(f"Заказы: {orders.shape[0]:,} записей")
print(f"Пользователи: {users.shape[0]:,} записей")
print(f"Объединено: {full_data.shape[0]:,} записей")

missing_values = full_data.isnull().sum()
print(f"Нулевых значений: {missing_values}")

## 5.1 Вкладка или блок «Сырые данные» - фильтрация по категории
st.dataframe(full_data)
with st.sidebar:
    st.header('Фильтры')
    selected_category = st.selectbox(
        "Выберите категорию",
        options=full_data['category'].unique()
    )
    filtered_df = full_data[full_data['category'] == selected_category]

st.write(f"Данные по категории: **{selected_category}**")
st.dataframe(filtered_df)

# Отображение метрик
st.subheader("Анализ продаж")
total_orders = len(orders)
total_revenue = (full_data['quantity'] * full_data['price_per_unit']).sum()
unique_users = full_data['user_id'].nunique()
average_check = total_revenue / total_orders

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric('Общее количество заказов: ', f'{total_orders:,}')
with col2:
    st.metric('Общую выручку: ', f'{total_revenue:,.2f} руб.')
with col3:
    st.metric('Количество уникальных пользователей: ',  unique_users)
with col4:
    st.metric('Средний чек: ', f'{average_check:,.2f} руб.')

# Топ-10 товаров по выручке
st.subheader("Топ-10 товаров по выручке")
top_items = full_data.groupby('item_name').agg(
    total_revenue=('price_per_unit', 'sum')
).reset_index()

top_items = top_items.sort_values('total_revenue', ascending=False).head(10)

fig, ax = plt.subplots(figsize=(12, 6))
bars = ax.barh(top_items['item_name'], top_items['total_revenue'])

for i, (bar, value) in enumerate(zip(bars, top_items['total_revenue'])):
    ax.text(value + 500, i, f'{value:,.0f} руб.',
            va='center', fontsize=9)

ax.set_xlabel('Выручка (руб.)', fontsize=12)
ax.set_ylabel('Товары', fontsize=12)
ax.set_title('Топ-10 товаров по выручке', fontsize=14)
ax.grid(axis='x', alpha=0.3)

ax.invert_yaxis()
st.pyplot(fig)

## Выручка по категориям товаров
st.subheader("Выручка по категориям товаров")
category_revenue = full_data.groupby('category').agg(
    total_revenue=('price_per_unit', 'sum')
).reset_index()

category_revenue = category_revenue.sort_values('total_revenue', ascending=False)
fig2, ax2 = plt.subplots(figsize=(10, 8))

wedges, texts, autotexts = ax2.pie(
    category_revenue['total_revenue'],
    autopct=lambda pct: f'{pct:.1f}%',
    startangle=90,
    textprops={'fontsize': 5, 'color': 'black', 'fontweight': 'bold'},
    pctdistance=0.85,
    labeldistance=1.1
)

legend_labels = [f"{row['category']}: {row['total_revenue']:,.0f} руб."
                 for _, row in category_revenue.iterrows()]
ax2.legend(wedges, legend_labels, title="Категории",
           loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
plt.tight_layout()
st.pyplot(fig2)

# Зависимость количества заказов от дня недели
st.subheader("Зависимость количества заказов от дня недели")
full_data['day_of_week'] = full_data['order_date'].dt.dayofweek
full_data['day_name'] = full_data['order_date'].dt.day_name()

days_mapping = {
    'Monday': 'Понедельник',
    'Tuesday': 'Вторник',
    'Wednesday': 'Среда',
    'Thursday': 'Четверг',
    'Friday': 'Пятница',
    'Saturday': 'Суббота',
    'Sunday': 'Воскресенье'
}
full_data['day_name_ru'] = full_data['day_name'].map(days_mapping)
orders_by_day = full_data.groupby(['day_of_week', 'day_name_ru']).size().reset_index(name='order_count')
orders_by_day = orders_by_day.sort_values('day_of_week')
fig3, ax3 = plt.subplots(figsize=(12, 6))

bars = ax3.bar(orders_by_day['day_name_ru'], orders_by_day['order_count'])

ax3.set_xlabel('День недели', fontsize=12, fontweight='bold')
ax3.set_ylabel('Количество заказов', fontsize=12, fontweight='bold')
ax3.grid(axis='y', alpha=0.3)

plt.tight_layout()
st.pyplot(fig3)

# Выводы по анализу
st.subheader("Основные выводы")

# 1. Вывод по категориям
top_category = category_revenue.iloc[0]
top_category_pct = (top_category['total_revenue'] / category_revenue['total_revenue'].sum()) * 100
st.markdown(f"**Основная выручка** приходится на категорию **{top_category['category']}** - {top_category_pct:.1f}%")

# 2. Вывод по дням недели
max_day = orders_by_day.loc[orders_by_day['order_count'].idxmax()]
min_day = orders_by_day.loc[orders_by_day['order_count'].idxmin()]
st.markdown(f"**Пик заказов** наблюдается в **{max_day['day_name_ru']}** ({int(max_day['order_count'])} заказов), минимум - в **{min_day['day_name_ru']}** ({int(min_day['order_count'])} заказов)")

# 3. Вывод по топ-товару
top_item = top_items.iloc[0]
st.markdown(f"**Лидер продаж** - товар **{top_item['item_name']}** с выручкой {top_item['total_revenue']:,.0f} руб.")
