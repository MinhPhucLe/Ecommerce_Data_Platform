from datetime import datetime, timedelta, timezone
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, desc, lit, sum, split, current_timestamp, date_format, round, when

# Create SparkSession with Hive support
spark = SparkSession.builder.appName("MoveStagingToWarehouse") \
    .enableHiveSupport() \
    .config("spark.hadoop.fs.defaultFS", "hdfs://hadoop-hadoop-hdfs-nn:9000/") \
    .config("hive.exec.dynamic.partition", "true") \
    .config("hive.exec.dynamic.partition.mode", "nonstrict") \
    .getOrCreate()

now = datetime.now(timezone(timedelta(hours=7)))

START_2019 = datetime(2019, 10, 1).date()
# START_2025 = datetime(2025, 4, 21).date()
START_2025 = datetime(2025, 5, 28).date()

# Day N - 1
target_purchase = now - timedelta(days=1)
target_time1 = now - timedelta(days=2)
target_time2 = now - timedelta(days=3)
target_date1 = target_time1.date()
target_date2 = target_time2.date()
target_date_purchase = target_purchase.date()

# Day N - 2 and N - 3
days_passed1 = (target_date1 - START_2025).days
result_date1 = START_2019 + timedelta(days=days_passed1)
day_query1 = result_date1.strftime("%Y%m%d")

days_passed2 = (target_date2 - START_2025).days
result_date2 = START_2019 + timedelta(days=days_passed2)
day_query2 = result_date2.strftime("%Y%m%d")

days_passed_purchase = (target_date_purchase - START_2025).days
result_date_purchase = START_2019 + timedelta(days=days_passed_purchase)
day_query_purchase = result_date_purchase.strftime("%Y%m%d")

# Get cart data in day N - 2 and N - 3
df_cart = spark.sql(f"""
    SELECT * 
    FROM cart_order
    WHERE date <= '{day_query1}'
    and date >= '{day_query2}'
""")
df_cart.show(5)

# Get purchase data in day N - 1
df_purchase = spark.sql(f"""
    SELECT * 
    FROM purchase_order 
    WHERE date = '{day_query_purchase}'
"""
)

df_purchase.show(5)

#=======================================================================================================================
# Get and load data of product abandoned by user

df_res = df_cart.join(
    df_purchase,
    on=["user_id", "product_id"],
    how="left_anti"
)

df_res = df_res.withColumn("date", lit(day_query_purchase))

df_res = df_res \
    .withColumn("category_main_code", split(col("category_code"), "\.").getItem(0)) \
    .withColumn("category_type", split(col("category_code"), "\.").getItem(1))

df_res = df_res.withColumn("imported_time", date_format(current_timestamp(), "yyyy-MM-dd HH:mm:ss"))

df_res = df_res.select("user_id", "product_id", "category_main_code", "category_type", "price", "imported_time", "date")

df_res.show(5)

df_res.write \
    .format("hive") \
    .mode("overwrite") \
    .insertInto("mart_abandoned_product")

#=======================================================================================================================
# Get and load conversion rate of each product in day N - 1

df_cart_count = df_cart.groupBy("product_id").count().withColumnRenamed("count", "cart_count")

df_purchase_count = df_purchase.groupBy("product_id").count().withColumnRenamed("count", "purchase_count")

df_conversion = df_cart_count.join(
    df_purchase_count,
    on="product_id",
    how="left"
)

df_conversion = df_conversion.fillna({"purchase_count": 0})

df_conversion = df_conversion.withColumn(
    "raw_conversion_rate", col("purchase_count") / col("cart_count")
)

df_conversion = df_conversion.withColumn(
    "conversion_rate", when(col("raw_conversion_rate") > 1, lit(1)).otherwise(round(col("raw_conversion_rate"), 4))
)

df_conversion = df_conversion.withColumn(
    "abandoned_rate", round(1 - col("conversion_rate"), 4)
)
df_conversion = df_conversion.withColumn("date", lit(day_query_purchase))

df_conversion = df_conversion.withColumn("imported_time", date_format(current_timestamp(), "yyyy-MM-dd HH:mm:ss"))
df_conversion = df_conversion.select("product_id", "conversion_rate", "abandoned_rate", "imported_time", "date")
df_conversion.show(5)

df_conversion.write \
    .format("hive") \
    .mode("overwrite") \
    .insertInto("mart_conversion_product")