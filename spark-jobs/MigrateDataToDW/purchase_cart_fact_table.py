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

# Reference dates
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
# Load data to cart fact table

df_action_cart = df.filter(df["event_type"] == "cart").withColumn("event_type_id", lit(2)).select("user_id", "product_id", "category_code", "price", "event_type_id", "day", "hour")
df_action_cart = df_action_cart.withColumnRenamed("day", "date")
df_action_cart.show(20)
df_action_cart.write \
    .format("hive") \
    .mode("overwrite") \
    .insertInto("cart_order")

#==========================================================================================
# Load data to purchase fact table

df_action_purchase = df.filter(df["event_type"] == "purchase").withColumn("event_type_id", lit(3)).select("user_id", "product_id", "category_code", "price", "event_type_id", "day", "hour")
df_action_cart = df_action_purchase.withColumnRenamed("day", "date")
df_action_purchase.show(20)
df_action_purchase.write \
    .format("hive") \
    .mode("overwrite") \
    .insertInto("purchase_order")