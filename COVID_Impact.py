import requests
from bs4 import BeautifulSoup
import csv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from pymongo import MongoClient

#                                                                             SCRAPING
url = "https://www.worldometers.info/coronavirus/"
response = requests.get(url)
if response.status_code == 200:
    print("Success!")
else:
    print("Failed!")

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

path = r"D:\FinalProject\covid_impact.csv"
with open(path, 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['Country', 'Total Cases', 'Total Deaths', 'Total Recovered', 'Population', 'Total Tests'])
    writer.writerows(covid_data)
    
print(f"Saved {len(covid_data)} countries succesfully!")

#                                                                           DATA CLEANING&PROCESSING

file_path=r"D:\FinalProject\covid_impact.csv"

data=pd.read_csv(file_path)
print(f"number of rows is:{len(data)}")

print(data.head())
print(data.info())
print(data.describe())
print(f"number of rows is:{len(data)}") #------>number of rows is 231

#check missing values
print(data.isnull())
print(data.isnull().sum())

#delete all missing values rows
data=data.dropna()
print(data.isnull().sum())

#check the missing values ---->0
print(f"the missing values is :{data.isnull().sum()}") 

#check the number of duplicated rows---->0
num_duplicates_rows=data.duplicated().sum()
print(f"number of duplicated rows is :{num_duplicates_rows}")

print(data)

#data processing

#calculate active cases
data['Active Cases']= data['Total Cases'] - (data['Total Deaths'] + data['Total Recovered']) 
print(data[['Country', 'Total Cases', 'Total Deaths', 'Total Recovered', 'Active Cases']].head())


file_path = r"D:\FinalProject\covid_data_cleaned.xlsx"
data.to_excel(file_path, index=False)

print(f"Data has been saved to {file_path}")

#                                                                             DATA ANALYSIS
df = pd.read_excel(r"D:\FinalProject\covid_data_cleaned.xlsx")
df.head()

pd.options.display.float_format = '{:.0f}'.format # i found it (●'◡'●)
df.describe()

df['Recovery Rate'] = (df['Total Recovered'] / df['Total Cases']) * 100
df['Death Rate'] = (df['Total Deaths'] / df['Total Cases']) * 100
print(df[['Country', 'Recovery Rate', 'Death Rate']])

correlation = df[["Total Cases", "Total Recovered"]].corr() # dataset is stupid
print("Correlation between Cases and Recoveries:\n", correlation)

#                                                                            VISUALIZATION
plt.figure(figsize=(12, 6))
sns.boxplot(data=df[["Total Cases", "Total Recovered"]])
plt.title('Boxplot for Total Cases and Total Recovered')
plt.show()

Q1 = df[["Total Cases", "Total Recovered"]].quantile(0.25)
Q3 = df[["Total Cases", "Total Recovered"]].quantile(0.75)
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR
df_cleaned_iqr = df[~((df[["Total Cases", "Total Recovered"]] < lower_bound) | 
                     (df[["Total Cases", "Total Recovered"]] > upper_bound)).any(axis=1)] 

plt.figure(figsize=(12, 6))
sns.boxplot(data=df_cleaned_iqr[["Total Cases", "Total Recovered"]])
plt.title('Boxplot for Total Cases and Total Recovered')
plt.show()

df_cleaned_iqr.shape
df_cleaned_iqr.head()

top_cases = df.sort_values("Total Cases", ascending=False).head(10)
hex_colors = ["#FF6347", "#FF4500", "#32CD32", "#1E90FF", "#FFD700", "#8A2BE2", "#DA70D6", "#FF69B4", "#20B2AA", "#9370DB"] 
plt.figure(figsize=(10,6))
sns.barplot(x="Total Cases", y="Country", data=top_cases , color='#bc5090')
plt.title("Top 10 Countries by Total Cases")
plt.show()

plt.figure(figsize=(10,6))
sns.lineplot(x="Country", y="Total Cases", data=top_cases, label="Cases", color='red')
sns.lineplot(x="Country", y="Total Recovered", data=top_cases, label="Recovered", color='green')
plt.xticks(rotation=45)
plt.title("Cases vs Recovered in Top 10 Countries")
plt.legend()
plt.show()

plt.figure(figsize=(8,6))
sns.heatmap(df[["Total Cases", "Total Deaths", "Total Recovered", "Population", "Total Tests"]].corr(), 
            annot=True, cmap="flare")
plt.title("Correlation Heatmap")
plt.show()

plt.figure(figsize=(8,6))
sns.scatterplot(x="Total Tests", y="Total Cases", data=df , color = '#ff6f61')
plt.title("Total Tests vs Total Cases")
plt.xlabel("Total Tests")
plt.ylabel("Total Cases")
plt.xscale("log") # we use log because the numbers are very large
plt.yscale("log")
plt.show()

plt.figure(figsize=(8,6))
sns.scatterplot(x="Population", y="Total Cases", data=df , color = '#1c9099')
plt.title("Population vs Total Cases")
plt.xlabel("Population")
plt.ylabel("Total Cases")
plt.xscale("log") # same as above
plt.yscale("log")
plt.show()

plt.figure(figsize=(10,6))
sns.boxplot(data=df[["Total Cases", "Total Deaths", "Total Recovered"]], palette="rocket")
plt.title("Distribution of Cases, Deaths, and Recoveries")
plt.yscale("log") # (●'◡'●)
plt.show()

plt.figure(figsize=(10,6))
sns.violinplot(data=df[["Recovery Rate", "Death Rate"]] , palette="mako")
plt.title("Distribution of Recovery and Death Rates")
plt.show()

fig = px.choropleth(df,
                    locations = "Country",
                    locationmode = "country names",
                    color = "Total Cases",
                    hover_name = "Country",
                    color_continuous_scale = "Blues",
                    title = "COVID-19 Total Cases by Country")
fig.show()

df["Recovery Rate"] = df["Total Recovered"] / df["Total Cases"]
fig = px.choropleth(df,
                    locations="Country",
                    locationmode="country names",
                    color="Recovery Rate",
                    hover_name="Country",
                    color_continuous_scale="Greens",
                    title="COVID-19 Recovery Rate by Country")
fig.show()

#                                                                              MANGODB - DATA STORAGE

df = pd.read_excel(r"D:\FinalProject\covid_data_cleaned.xlsx")

data = df.to_dict(orient="records")

client = MongoClient("mongodb://localhost:27017/")

db = client["final_project_db"]
collection = db["covid_cleaned_data"]

collection.insert_many(data)

print("Data uploaded to MongoDB.")