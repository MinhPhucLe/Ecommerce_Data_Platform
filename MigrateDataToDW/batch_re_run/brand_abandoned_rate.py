from datetime import datetime, timedelta, timezone
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, lit, split, current_timestamp, date_format, round

# Create SparkSession with Hive support
spark = SparkSession.builder.appName("CalculateAbandonedRate") \
    .enableHiveSupport() \
    .config("spark.hadoop.fs.defaultFS", "hdfs://hadoop-hadoop-hdfs-nn:9000/") \
    .config("hive.exec.dynamic.partition", "true") \
    .config("hive.exec.dynamic.partition.mode", "nonstrict") \
    .getOrCreate()

# Timezone: GMT+7
now = datetime.now(timezone(timedelta(hours=7)))

START_2019 = datetime(2019, 10, 1).date()
START_2025 = datetime(2025, 4, 22).date()

target_purchase = now - timedelta(days=1)
target_time1 = now - timedelta(days=2)
target_time2 = now - timedelta(days=3)
target_date1 = target_time1.date()
target_date2 = target_time2.date()
target_date_purchase = target_purchase.date()

days_passed1 = (target_date1 - START_2025).days
result_date1 = START_2019 + timedelta(days=days_passed1)
day_query1 = result_date1.strftime("%Y%m%d")

days_passed2 = (target_date2 - START_2025).days
result_date2 = START_2019 + timedelta(days=days_passed2)
day_query2 = result_date2.strftime("%Y%m%d")

days_passed_purchase = (target_date_purchase - START_2025).days
result_date_purchase = START_2019 + timedelta(days=days_passed_purchase)
day_query_purchase = result_date_purchase.strftime("%Y%m%d")

# Load cart data
df_cart = spark.sql(f"""
    SELECT * 
    FROM cart_order
    WHERE date = '{day_query1}' OR date = '{day_query2}'
""")

# Load abandoned data
# df_abandoned = spark.sql(f"""
#     SELECT *
#     FROM mart_abandoned_product
#     WHERE date = '{day_query_purchase}'
# """)

df_purchase = spark.sql(f"""
    SELECT * 
    FROM purchase_order 
    WHERE date = '{day_query_purchase}'
"""
)

# Filter out NULL category_type
# df_cart = df_cart.withColumn("category_main_code", split(col("category_code"), "\.").getItem(0)) \
#                  .withColumn("category_type", split(col("category_code"), "\.").getItem(1)) \
#                  .filter(col("category_type").isNotNull())
#
# df_cart.show(5)
#
# df_abandoned = df_abandoned.filter(col("category_type").isNotNull())
# df_abandoned.show(5)
#
# # Count cart per category_type
# df_cart_count = df_cart.groupBy("category_type").count().withColumnRenamed("count", "cart_count")
#
# # Count abandoned per category_type
# df_abandoned_count = df_abandoned.groupBy("category_type").count().withColumnRenamed("count", "abandoned_count")
#
# df_abandoned_count.show(5)
#
# # Join and calculate abandoned rate
# df_conversion = df_cart_count.join(
#     df_abandoned_count,
#     on="category_type",
#     how="left"
# ).withColumn(
#     "abandoned_rate",
#     (col("abandoned_count") / col("cart_count"))
# )
#
# # Add extra columns
# df_conversion = df_conversion.withColumn("date", lit(day_query_purchase)) \
#                              .withColumn("imported_time", date_format(current_timestamp(), "yyyy-MM-dd HH:mm:ss"))
#
# df_conversion.show(5)

# Final select
# df_conversion = df_conversion.select(
#     "category_type",
#     "cart_count",
#     "abandoned_count",
#     "abandoned_rate",
#     "date",
#     "imported_time"
# )
#
# # Show results
# df_conversion.show(5)
#
# # Insert into Hive
# df_conversion.write \
#     .format("hive") \
#     .mode("overwrite") \
#     .insertInto("mart_abandoned_rate_by_category")


