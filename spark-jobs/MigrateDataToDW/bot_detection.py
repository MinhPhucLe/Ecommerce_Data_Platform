from datetime import datetime, timedelta, timezone
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, desc, lit, sum, date_format, current_timestamp

# Create SparkSession with Hive support
spark = SparkSession.builder.appName("MoveStagingToWarehouse") \
    .enableHiveSupport() \
    .config("spark.hadoop.fs.defaultFS", "hdfs://hadoop-hadoop-hdfs-nn:9000/") \
    .config("hive.exec.dynamic.partition", "true") \
    .config("hive.exec.dynamic.partition.mode", "nonstrict") \
    .getOrCreate()

now = datetime.now(timezone(timedelta(hours=7)))

START_2019 = datetime(2019, 10, 1).date()

START_2025 = datetime(2025, 5, 28).date()

target_datetime = now - timedelta(hours=1)
last_hour_str = target_datetime.strftime('%H')
target_date = target_datetime.date()

days_passed = (target_date - START_2025).days
result_date = START_2019 + timedelta(days=days_passed)
day_query = result_date.strftime("%Y%m%d")

print("Date (GMT+7):", day_query)
print("Last hour (GMT+7):", last_hour_str)

# Get Bot or suspicious user in hour

# Load data from Hive staging table
df = spark.sql(f"""
    SELECT * 
    FROM tst_staging 
    WHERE day = '{day_query}' AND hour = '{last_hour_str}'
""")

df = df.withColumnRenamed("day", "date")

df_view = df.filter(df["event_type"] == "view")

df_view = df_view.groupBy("user_id", "date", "hour") \
                    .agg(count("*").alias("numberActions"))

df_view = df_view.filter(col("numberActions") > 150)

df_cart = df.filter(df["event_type"] == "cart")

df_cart = df_cart.groupBy("user_id", "date", "hour") \
                    .agg(count("*").alias("numberActions"))

df_cart = df_cart.filter(col("numberActions") > 70)


df_purchase = df.filter(df["event_type"] == "purchase")

df_res_view = df_view.join(
    df_purchase,
    on=["user_id", "date", "hour"],
    how="left_anti"
)

df_res_cart = df_cart.join(
    df_purchase,
    on=["user_id", "date", "hour"],
    how="left_anti"
)

df_res_view = (df_res_view.withColumn("imported_time", date_format(current_timestamp(), "yyyy-MM-dd HH:mm:ss"))
          .withColumnRenamed("numberActions", "total_suspicious_actions")
          .withColumn("type_suspicious", lit("View"))
)

df_res_cart = (df_res_cart.withColumn("imported_time", date_format(current_timestamp(), "yyyy-MM-dd HH:mm:ss"))
          .withColumnRenamed("numberActions", "total_suspicious_actions")
          .withColumn("type_suspicious", lit("Cart"))
)

df_res = df_res_view.union(df_res_cart)

df_res = df_res.select("user_id", "total_suspicious_actions", "type_suspicious", "imported_time", "date", "hour")

df_res.show(5)

df_res.write \
    .format("hive") \
    .mode("overwrite") \
    .insertInto("bot_detection")
