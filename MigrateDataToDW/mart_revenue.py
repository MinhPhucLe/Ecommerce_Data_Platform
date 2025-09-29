from datetime import datetime, timedelta, timezone
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, desc, lit, sum
from pyspark.sql.functions import udf
from pyspark.sql.types import *

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
# Get total revenue in each hour

df_total_revenue = (df.filter(df["event_type"] == "purchase").filter(df["price"].isNotNull()).withColumn(
    "price", col("price").cast("float")
)
.groupBy("day", "hour")
.agg(sum("price").cast("float").alias("total_revenue")))

df_total_revenue = df_total_revenue.withColumnRenamed("day", "date").select("total_revenue", "date", "hour")
df_total_revenue.show(20)
df_total_revenue.write \
    .format("hive") \
    .mode("overwrite") \
    .insertInto("mart_revenue_hour")

#==========================================================================================
# Get top total revenue for each product

df_revenue = (df.filter(df["event_type"] == "purchase").filter(df["price"].isNotNull()).withColumn(
    "price", col("price").cast("float")
)
.groupBy("product_id","day", "hour",) \
.agg(sum("price").cast("float").alias("revenue"))) \
.orderBy(desc("revenue")) \
.limit(50)

df_revenue = df_revenue.withColumnRenamed("day", "date").select("product_id", "revenue", "date", "hour")
df_revenue.show(20)
df_revenue.write \
    .format("hive") \
    .mode("overwrite") \
    .insertInto("mart_product_revenue_hour")