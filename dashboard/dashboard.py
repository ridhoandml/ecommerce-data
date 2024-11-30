import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency

st.set_page_config(page_title="Ridho's Dashboard")
plt.style.use('dark_background')

all_df = pd.read_csv('all_dataframe.csv')

# Function Data
def create_daily_orders_df(df):
  returned_df = df.resample(rule='D', on='order_delivered_customer_date').agg(
    order_count=("order_id", "nunique"),
    revenue=("payment_value", "sum")
	).reset_index()
  
  returned_df.rename(columns={
    "order_delivered_customer_date": "order_date"
  }, inplace=True)
  return returned_df

def create_sum_order_items_df(df):
  returned_df = df.groupby("product_category_name_english").agg(
     order_count=("order_id", "nunique"),
     revenue=("payment_value", "sum")
	).sort_values(by="revenue", ascending=False).reset_index()
  
  returned_df.rename(columns={
    "product_category_name_english": "category"
  }, inplace=True)
  return returned_df

def create_users_city_df(df):
  return df.groupby("customer_city").agg(
    customer_count=("customer_id", "nunique")
	)

def create_users_payment_type_df(df):
  return df.groupby("payment_type").agg(
    customer_count=("customer_id", "count")
	)

def create_rfm_df(df):
  returned_df = df.groupby(by="customer_id", as_index=False).agg(
    max_order_timestamp=("order_delivered_customer_date", "max"),
    frequency=("order_id", "nunique"),
    monetary=("payment_value", "sum")
	)
  
  returned_df["max_order_timestamp"] = returned_df["max_order_timestamp"].dt.date
  recent_date = df["order_delivered_customer_date"].dt.date.max()
  returned_df["recency"] = returned_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
  returned_df.drop("max_order_timestamp", axis=1, inplace=True)
  returned_df["customer_id_short"] = returned_df["customer_id"].apply(lambda x: x[:5])
  
  return returned_df

# Generate Chart
def generate_couple_chart(data_frame_1, data_frame_2, x_1, x_2, y_1, y_2, title_1, title_2):
	fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(35, 15))

	sns.barplot(x=x_1, y=y_1, data=data_frame_1, ax=ax[0])
	ax[0].set_ylabel(None)
	ax[0].set_xlabel(title_1, fontsize=30)
	ax[0].tick_params(axis='y', labelsize=35)
	ax[0].tick_params(axis='x', labelsize=35)

	sns.barplot(x=x_2, y=y_2, data=data_frame_2, ax=ax[1])
	ax[1].set_ylabel(None)
	ax[1].set_xlabel(title_2, fontsize=30)
	ax[1].invert_xaxis()
	ax[1].yaxis.set_label_position("right")
	ax[1].yaxis.tick_right()
	ax[1].tick_params(axis='y', labelsize=35)
	ax[1].tick_params(axis='x', labelsize=35)

	st.pyplot(fig)

datetime_columns = [
	"order_purchase_timestamp",
	"order_approved_at",
	"order_delivered_carrier_date",
	"order_delivered_customer_date",
	"order_estimated_delivery_date"
]

for column in datetime_columns:
  all_df[column] = pd.to_datetime(all_df[column])

all_df[all_df.select_dtypes(include="object").columns] = all_df.select_dtypes(include="object").astype("string")

all_df.sort_values(by="order_delivered_customer_date", inplace=True)
all_df.reset_index(inplace=True)

min_date = all_df["order_delivered_customer_date"].min()
max_date = all_df["order_delivered_customer_date"].max()

st.subheader('Filter Data')

start_date, end_date = st.date_input(
  label='Rentang Waktu',min_value=min_date,
  max_value=max_date,
  value=[min_date, max_date]
)

main_df = all_df[(all_df["order_delivered_customer_date"] >= str(start_date)) &  (all_df["order_delivered_customer_date"] <= str(end_date))]

total_orders_df = create_daily_orders_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
users_city_df = create_users_city_df(main_df)
users_payment_type_df = create_users_payment_type_df(main_df)
rfm_df = create_rfm_df(main_df)

st.header('Ecommerce Revenue')
st.subheader('Overall Dashboard')

col1, col2 = st.columns(2)
with col1:
    total_orders = total_orders_df.order_count.sum()
    st.metric("Total Orders", value=total_orders)
with col2:
    total_revenue = format_currency(total_orders_df.revenue.sum(), "USD", locale='en_US') 
    st.metric("Total Revenue", value=total_revenue)
    
fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    total_orders_df["order_date"],
    total_orders_df["order_count"],
    marker='o', 
    linewidth=2,
    color="#90CAF9"
)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)

st.pyplot(fig)

st.subheader("Best & Worst Performing Categories")
st.text("Sort by Order Count")
   
generate_couple_chart(
  data_frame_1=sum_order_items_df.head(5),
  data_frame_2=sum_order_items_df.sort_values(by="revenue", ascending=True).head(5),
  x_1="order_count",
  x_2="order_count",
  y_1="category",
  y_2="category",
  title_1="Number of Orders",
  title_2="Number of Orders"
)

st.text("Sort by Order Revenue")

generate_couple_chart(
  data_frame_1=sum_order_items_df.head(5),
  data_frame_2=sum_order_items_df.sort_values(by="revenue", ascending=True).head(5),
  x_1="revenue",
  x_2="revenue",
  y_1="category",
  y_2="category",
  title_1="Number of Revenue",
  title_2="Number of Revenue"
)

st.subheader("Customer Insight")

generate_couple_chart(
  data_frame_1=users_city_df.sort_values(by="customer_count", ascending=False).head(5),
  data_frame_2=users_payment_type_df.sort_values(by="customer_count", ascending=False).head(5),
  x_1="customer_city",
  x_2="payment_type",
  y_1="customer_count",
  y_2="customer_count",
  title_1="Number of User by City",
  title_2="Number of User by Payment Type"
)

st.subheader("Best Customer Based on RFM Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)

with col2:
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)

with col3:
    avg_frequency = format_currency(rfm_df.monetary.mean(), "AUD", locale='es_CO') 
    st.metric("Average Monetary", value=avg_frequency)

fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))

sns.barplot(y="recency", x="customer_id_short", data=rfm_df.sort_values(by="recency", ascending=True).head(5), ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel("customer_id", fontsize=30)
ax[0].set_title("By Recency (days)", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=30)
ax[0].tick_params(axis='x', labelsize=35)

sns.barplot(y="frequency", x="customer_id_short", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel("customer_id", fontsize=30)
ax[1].set_title("By Frequency", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=30)
ax[1].tick_params(axis='x', labelsize=35)

sns.barplot(y="monetary", x="customer_id_short", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), ax=ax[2])
ax[2].set_ylabel(None)
ax[2].set_xlabel("customer_id", fontsize=30)
ax[2].set_title("By Monetary", loc="center", fontsize=50)
ax[2].tick_params(axis='y', labelsize=30)
ax[2].tick_params(axis='x', labelsize=35)

st.pyplot(fig)

st.caption('Copyright © Ridho Anandamal 2024')