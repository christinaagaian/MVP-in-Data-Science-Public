import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
@st.cache_data
def process_inflation(df):
    df = df[['Год', 'Всего']].dropna()
    df.columns = ['year', 'inflation']
    df['year'] = df['year'].astype(int)
    df['inflation'] = df['inflation'].astype(float)
    df = df.sort_values('year')
    df['cumulative_index'] = (1 + df['inflation'] / 100).cumprod()
    df['deflator'] = df['cumulative_index'].iloc[-1] / df['cumulative_index']
    return df
@st.cache_data
def process_salary(df, selected_sectors):
    df = df.dropna(subset=['Вид деятельности'])
    mask = df['Вид деятельности'].str.lower().str.contains('|'.join([s.lower() for s in selected_sectors]))
    df = df[mask]
    df_long = df.melt(id_vars='Вид деятельности', var_name='year', value_name='salary_nominal')
    df_long['year'] = df_long['year'].astype(int)
    df_long = df_long.reset_index(drop=True)
    return df_long
@st.cache_data
def load_data(file_salary, file_salary_old, file_inflation):
    salary_df = pd.read_excel(file_salary)
    salary_old_df = pd.read_csv(file_salary_old, sep=';')
    inflation_df = pd.read_excel(file_inflation)
    
    inflation_df = process_inflation(inflation_df)
    selected_sectors_new = [
        'государственное управление и обеспечение военной безопасности; социальное обеспечение',
        'деятельность в области информации и связи',
        'деятельность финансовая и страховая'
    ]
    selected_sectors_old = [
        'государственное управление и обеспечение военной безопасности; социальное страхование',
        'финансовая деятельность',
        'из них связь'
    ]
    salary_long = process_salary(salary_df, selected_sectors_new)
    salary_old_long = process_salary(salary_old_df, selected_sectors_old)
    def mapping(x):
        if x == "Государственное управление и обеспечение военной безопасности; социальное страхование":
            return "государственное управление и обеспечение военной безопасности; социальное обеспечение"
        elif x == "Финансовая деятельность":
            return "деятельность финансовая и страховая"
        elif x == "из них связь":
            return "деятельность в области информации и связи"
        return x
    salary_old_long['Вид деятельности'] = salary_old_long['Вид деятельности'].apply(mapping)
    combined_salary_df = pd.concat([salary_old_long, salary_long], ignore_index=True)
    combined_salary_df = combined_salary_df.drop_duplicates(subset=['Вид деятельности', 'year'])
    combined_salary_df = combined_salary_df.sort_values(by=['Вид деятельности', 'year']).reset_index(drop=True)
    merged_df = combined_salary_df.merge(inflation_df[['year', 'deflator']], on='year', how='left')
    merged_df['salary_real'] = merged_df['salary_nominal'] * merged_df['deflator']
    return merged_df
st.title("Анализ зарплат по отраслям (2000–2024 гг.)")
file_salary = st.file_uploader("Загрузите файл с данными по зарплатам 2024 (Excel)", type=["xlsx", "xls"])
file_salary_old = st.file_uploader("Загрузите файл с данными по зарплатам 2000 (CSV, с ;)", type=["csv"])
file_inflation = st.file_uploader("Загрузите файл с данными по инфляции (Excel)", type=["xlsx", "xls"])
if file_salary and file_salary_old and file_inflation:
    data = load_data(file_salary, file_salary_old, file_inflation)
    sectors = data['Вид деятельности'].unique()
    selected_sector = st.selectbox("Выберите отрасль", sectors)
    salary_type = st.radio("Выберите тип зарплаты:", ('Номинальная', 'Реальная'))
    plot_data = data[data['Вид деятельности'] == selected_sector]
    fig, ax = plt.subplots(figsize=(10, 6))
    if salary_type == 'Номинальная':
        sns.lineplot(data=plot_data, x='year', y='salary_nominal', marker='o', ax=ax)
        ax.set_ylabel("Номинальная зарплата (₽)")
    else:
        sns.lineplot(data=plot_data, x='year', y='salary_real', marker='o', ax=ax)
        ax.set_ylabel("Реальная зарплата (₽, цены 2024 года)")
    ax.set_title(f"{salary_type} зарплата: {selected_sector}")
    ax.set_xlabel("Год")
    ax.grid(True)
    st.pyplot(fig)
    st.markdown("### Ключевые показатели")
    col_name = 'salary_nominal' if salary_type == 'Номинальная' else 'salary_real'
    st.write(f"Минимальная {salary_type.lower()} зарплата: {plot_data[col_name].min():.2f} ₽")
    st.write(f"Максимальная {salary_type.lower()} зарплата: {plot_data[col_name].max():.2f} ₽")
    st.write(f"Средняя {salary_type.lower()} зарплата: {plot_data[col_name].mean():.2f} ₽")
else:
    st.info("Пожалуйста, загрузите все три файла для анализа.")


