from datetime import datetime, timedelta, timezone
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, desc, lit, sum

# Create SparkSession with Hive support
spark = SparkSession.builder.appName("MoveStagingToWarehouse") \
    .enableHiveSupport() \
    .config("spark.hadoop.fs.defaultFS", "hdfs://hadoop-hadoop-hdfs-nn:9000/") \
    .config("hive.exec.dynamic.partition", "true") \
    .config("hive.exec.dynamic.partition.mode", "nonstrict") \
    .getOrCreate()

# Timezone: GMT+7
now = datetime.now(timezone(timedelta(hours=7)))

START_2019 = datetime(2019, 10, 1).date()
# START_2025 = datetime(2025, 4, 21).date()
START_2025 = datetime(2025, 5, 28).date()

# Calculate the target datetime (last hour)
target_datetime = now - timedelta(hours=1)
last_hour_str = target_datetime.strftime('%H')
target_date = target_datetime.date()

# Calculate days passed and corresponding date for query
days_passed = (target_date - START_2025).days
result_date = START_2019 + timedelta(days=days_passed)
day_query = result_date.strftime("%Y%m%d")

print("Date (GMT+7):", day_query)
print("Last hour (GMT+7):", last_hour_str)

# Load data from Hive staging table
df = spark.sql(f"""
    SELECT * 
    FROM tst_staging 
    WHERE day = '{day_query}' AND hour = '{last_hour_str}'
""")
df.show(5)

#==========================================================================================
# Get top 50 action

df_action = df.groupBy("product_id", "category_id", "day", "hour") \
       .agg(count("*").alias("numberAction")) \
       .orderBy(desc("numberAction")) \
       .limit(50)

df_action = df_action.withColumnRenamed("day", "date")
df_action = df_action.select("numberAction", "product_id", "category_id", "date", "hour")

df_action.show(20)

# Put data to action mart table
df_action.write \
    .format("hive") \
    .mode("overwrite") \
    .insertInto("mart_topviews_hour")

#==========================================================================================
# Get top 50 views in hour

df_view = df.filter(df["event_type"] == "view")

df_view = df_view.groupBy("product_id", "category_id", "day", "hour") \
       .agg(count("*").alias("numberViews")) \
       .orderBy(desc("numberViews")) \
       .limit(50)

df_view = df_view.withColumnRenamed("day", "date")
df_view = df_view.select("numberViews", "product_id", "category_id", "date", "hour")

df_view.show(20)

df_view.write \
    .format("hive") \
    .mode("overwrite") \
    .insertInto("mart_views_hour")

#==========================================================================================
# Get top 50 carts in hour

df_cart = df.filter(df["event_type"] == "cart")
df_cart = df_cart.groupBy("product_id", "category_id", "day", "hour") \
    .agg(count("*").alias("numberCarts")) \
    .orderBy(desc("numberCarts")) \
    .limit(50)

df_cart = df_cart.withColumnRenamed("day", "date")
df_cart = df_cart.select("numberCarts", "product_id", "category_id", "date", "hour")

df_cart.show(20)

df_cart.write \
    .format("hive") \
    .mode("overwrite") \
    .insertInto("mart_carts_hour")


#==========================================================================================
# Get top 50 purchases in hour

df_purchase = df.filter(df["event_type"] == "purchase")
df_purchase = df_purchase.groupBy("product_id", "category_id", "day", "hour") \
    .agg(count("*").alias("numberPurchases")) \
    .orderBy(desc("numberPurchases")) \
    .limit(50)

df_purchase = df_purchase.withColumnRenamed("day", "date")
df_purchase = df_purchase.select("numberPurchases", "product_id", "category_id", "date", "hour")

df_purchase.show(20)

df_purchase.write \
    .format("hive") \
    .mode("overwrite") \
    .insertInto("mart_purchases_hour")