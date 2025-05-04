import streamlit as st
import requests
from bs4 import BeautifulSoup
import csv
import pandas as pd

st.set_page_config(page_title="COVID-19 Impact", layout="wide")
st.title("COVID-19 Impact")

#=== Data extraction ===
st.header("1. Data scrape")

@st.cache_data
def scrape_data():
    url = "https://www.worldometers.info/coronavirus/"
    response = requests.get(url)
    
    if response.status_code == 200:
        st.success("Successfully connected!")
    else:
        st.error("Connection failed!")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    covid_data = []

    table = soup.find('table', id='main_table_countries_today')
    all_rows = table.find_all('tr')
    data_rows = all_rows[1:]
    start_index = 8
    end_index = len(data_rows) - 8
    selected_rows = data_rows[start_index:end_index]

    for row in selected_rows:
        cols = row.find_all('td')
        country = cols[1].text.strip()
        total_cases = cols[2].text.strip().replace(',', '')
        total_deaths = cols[4].text.strip().replace(',', '')
        total_recovered = cols[6].text.strip().replace(',', '')
        population = cols[14].text.strip().replace(',', '')
        total_tests = cols[12].text.strip().replace(',','')
        covid_data.append([country, total_cases, total_deaths, total_recovered, population, total_tests])

    return covid_data

covid_data = scrape_data()

path = r"D:\FinalProject\covid_impact.csv"
with open(path, 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['Country', 'Total Cases', 'Total Deaths', 'Total Recovered', 'Population', 'Total Tests'])
    writer.writerows(covid_data)
    
st.success(f"Saved {len(covid_data)} countries successfully to CSV!")

#=== Data cleaning & pre-processing ===
st.header("2. Data cleaning & processing")
    
file_path = r"D:\FinalProject\covid_impact.csv"
data = pd.read_csv(file_path)

with st.expander("Data sample and overview"):
    st.write(f"Number of rows: {len(data)}")
    st.dataframe(data.head())
        
    st.write("Description of data (statistics):")
    st.dataframe(data.describe())

with st.expander("Data cleaning"):
        
    st.write("Check missing values:")
    st.dataframe(data.isnull().sum())
        
    data = data.dropna()
    st.write("Review after dropping nulls:")
    st.dataframe(data.isnull().sum())
        
    st.write("Check duplicates:")
    st.write(f"number of duplicated rows is : {data.duplicated().sum()}")

data['Active Cases'] = data['Total Cases'] - (data['Total Deaths'] + data['Total Recovered'])

file_path = r"D:\FinalProject\covid_data_cleaned.xlsx"
data.to_excel(file_path, index=False)
st.success(f"Data has been saved to {file_path}")

# === Analysis ===
df = pd.read_excel(r"D:\FinalProject\covid_data_cleaned.xlsx")
pd.options.display.float_format = '{:.0f}'.format

df['Recovery Rate'] = (df['Total Recovered'] / df['Total Cases']) * 100
df['Death Rate'] = (df['Total Deaths'] / df['Total Cases']) * 100

with st.expander("Show Recovery & Death rates"):
    st.dataframe(df[['Country', 'Recovery Rate', 'Death Rate']])

st.write("Correlation between Cases and Recoveries:")
correlation = df[["Total Cases", "Total Recovered"]].corr()
st.dataframe(correlation)

import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

st.header("4. Visualization")
    
st.sidebar.header("Filter")
top_number = st.sidebar.slider("Select nuimber of top countries you would like to display (by total cases):", 2, 20, 10)
selected_countries = st.sidebar.multiselect(
    "Select countries for comparison (case vs recovered):",
    df['Country'].unique(),
    default=df['Country'].head(2).tolist()
    )

st.subheader("Boxplot for Total Cases and Total Recovered")

fig1, ax1 = plt.subplots(figsize=(12, 6))
sns.boxplot(data=df[["Total Cases", "Total Recovered"]], ax=ax1)
st.pyplot(fig1)

st.subheader ("Boxplot for Total Cases and Total Recovered (with outliers removed)")
Q1 = df[["Total Cases", "Total Recovered"]].quantile(0.25)
Q3 = df[["Total Cases", "Total Recovered"]].quantile(0.75)
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR
df_cleaned_iqr = df[~((df[["Total Cases", "Total Recovered"]] < lower_bound) |
                        (df[["Total Cases", "Total Recovered"]] > upper_bound)).any(axis=1)]
    
fig2, ax2 = plt.subplots(figsize=(12,6))
sns.boxplot(data=df_cleaned_iqr[["Total Cases", "Total Recovered"]], ax=ax2)
st.pyplot(fig2)
st.write(f"Shape without outliers: {df_cleaned_iqr.shape}")
st.subheader("We will continue to use the original Dataframe, as we need the outliers. The above boxplot is only for clarification.")

st.subheader(f"Top {top_number} Countries by Total Cases")
top_cases = df.sort_values("Total Cases", ascending=False).head(top_number)
    
fig3, ax3 = plt.subplots(figsize=(10,6))
sns.barplot(x="Total Cases", y="Country", data=top_cases, color='#bc5090', ax=ax3)
st.pyplot(fig3)

if selected_countries:
    st.subheader("Cases vs Recovered comparison")
    compare_df = df[df['Country'].isin(selected_countries)]
        
    fig4, ax4 = plt.subplots(figsize=(10,6))
    sns.lineplot(x="Country", y="Total Cases", data=compare_df, label="Cases", color='red')
    sns.lineplot(x="Country", y="Total Recovered", data=compare_df, label="Recovered", color='green')
    plt.xticks(rotation=45)
    plt.legend()
    st.pyplot(fig4)

st.subheader("Correlation Heatmap")
fig5, ax5 = plt.subplots(figsize=(8,6))
sns.heatmap(df[["Total Cases", "Total Deaths", "Total Recovered", "Population", "Total Tests"]].corr(), 
            annot=True, cmap="flare", ax=ax5)
st.pyplot(fig5)

col1, col2 = st.columns(2)
with col1:
    st.subheader("Total Tests vs Total Cases")
    fig6, ax6 = plt.subplots(figsize=(8,6))
    sns.scatterplot(x="Total Tests", y="Total Cases", data=df, color='#ff6f61')
    plt.xscale("log")
    plt.yscale("log")
    st.pyplot(fig6)

with col2:
    st.subheader("Population vs Total Cases")
    fig7, ax7 = plt.subplots(figsize=(8,6))
    sns.scatterplot(x="Population", y="Total Cases", data=df, color='#1c9099')
    plt.xscale("log")
    plt.yscale("log")
    st.pyplot(fig7)

st.subheader ("Distribution of Cases, Deaths and Recoveries")
fig8, ax8 = plt.subplots(figsize=(10,6))
sns.boxplot(data=df[["Total Cases", "Total Deaths", "Total Recovered"]], palette="rocket", ax = ax8)
plt.yscale("log")
st.pyplot(fig8)

st.subheader("Distribution of Recovery & Death rates")
fig9, ax9 = plt.subplots(figsize=(10,6))
sns.violinplot(data=df[["Recovery Rate", "Death Rate"]] , palette="mako", ax= ax9)
st.pyplot(fig9)

st.subheader("Geographical Distribution")
tab1, tab2 = st.tabs(["COVID-19 Total Cases by Country", "COVID-19 Recovery Rate by Country"])
    
with tab1:
    fig10 = px.choropleth(df,
                        locations="Country",
                        locationmode="country names",
                        color="Total Cases",
                        hover_name="Country",
                        color_continuous_scale="Blues")
    st.plotly_chart(fig10, use_container_width=True)
    
with tab2:
    fig11 = px.choropleth(df,
                        locations="Country",
                        locationmode="country names",
                        color="Recovery Rate",
                        hover_name="Country",
                        color_continuous_scale="Greens")
    st.plotly_chart(fig11, use_container_width=True)

#=== MongoDB ===
from pymongo import MongoClient

st.header("5. Data Storage")
    
if st.button("Store in MongoDB"):
    try:
        client = MongoClient("mongodb://localhost:27017/")
        db = client["final_project_db"]
        collection = db["covid_cleaned_data"]
        data = df.to_dict(orient="records")
        collection.insert_many(data)
        st.success("Data uploaded to MongoDB successfully!")
    except Exception as e:
        st.error(f"Error connecting to MongoDB: {str(e)}")
