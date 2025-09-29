from datetime import datetime, timedelta, timezone

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, expr, substring, when
from pyspark.sql.functions import current_timestamp, date_format
from pyspark.sql.functions import (
    substring, to_date, dayofmonth, month, year, quarter, date_format,
    dayofweek, when, current_timestamp, date_format
)
from pyspark.sql.functions import split

from pyspark.sql import SparkSession
from pyspark.sql.functions import lit, date_format, current_timestamp
from pyspark.sql.functions import col, current_timestamp, date_format, udf
from pyspark.sql.types import IntegerType

# Create SparkSession with Hive support
spark = SparkSession.builder.appName("MoveStagingToWarehouse") \
    .enableHiveSupport() \
    .config("spark.hadoop.fs.defaultFS", "hdfs://hadoop-hadoop-hdfs-nn:9000/") \
    .config("hive.exec.dynamic.partition", "true") \
    .config("hive.exec.dynamic.partition.mode", "nonstrict") \
    .config("spark.sql.session.timeZone", "Asia/Bangkok") \
    .getOrCreate()

now = datetime.now(timezone(timedelta(hours=7))).date()

START_2019 = datetime(2019, 10, 1).date()

# Define real-time mapping
# START_2025 = datetime(2025, 4, 20).date()
START_2025 = datetime(2025, 5, 28).date()

days_passed = (now - START_2025).days

# Add days_passed to START_2019
result_date = START_2019 + timedelta(days=days_passed)

# Format the result in YYYYMMDD format
day_query = result_date.strftime("%Y%m%d")

now = datetime.now().date()

df = spark.sql(f"SELECT * FROM tst_staging WHERE day = '{day_query}'")
df.show(5)
res = df.count()
print("HEREEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE: ", res)
df_res = spark.createDataFrame([(res,)], ["num_rows"])
df_res.show()

fact_df = df.select(
    col("event_time_only").alias("time"),
    col("product_id"),
    col("category_id"),
    col("price"),
    col("user_id"),
    col("user_session"),
    when(col("event_type") == "view", 1)
     .when(col("event_type") == "cart", 2)
     .when(col("event_type") == "purchase", 3)
     .otherwise(None).alias("event_type_id"),
    date_format(current_timestamp(), "yyyy-MM-dd HH:mm:ss").alias("imported_time"),
    col("day"),
    col("hour"))


fact_df.show(5)

fact_df = fact_df.withColumnRenamed("day", "date")

fact_df.write \
    .format("hive") \
    .mode("overwrite") \
    .insertInto("fact_event")

df_dim_date_exist = spark.sql("select * from dim_date").withColumn("day_str", col("date"))

df_dim_date_exist.show()

df_with_date = df.select(col("day")).withColumnRenamed("day", "day_str").distinct() \
    .withColumn("date_formatted", to_date(col("day_str"), "yyyyMMdd"))

df_with_date.show()

df_new_days_only = df_with_date.join(
    df_dim_date_exist.select("day_str"),
    on="day_str",
    how="left_anti"
)
df_new_days_only.show()

# # Create the date dimension-like table
date_df = df_new_days_only.select(
    dayofmonth(col("date_formatted")).alias("day"),
    month(col("date_formatted")).alias("month"),
    year(col("date_formatted")).alias("year"),
    quarter(col("date_formatted")).alias("quarter"),
    date_format(col("date_formatted"), "EEEE").alias("day_of_week"),
    dayofweek(col("date_formatted")).alias("week_day_number"),  # 1=Sunday, ..., 7=Saturday
    when(dayofweek(col("date_formatted")).isin(1, 7), 1).otherwise(0).alias("weekend_or_not"),
    date_format(current_timestamp(), "yyyy-MM-dd HH:mm:ss").alias("imported_time"),
    col("day_str").alias("date")
).distinct()

if date_df.head(1):
    print("Data exist:")
    date_df.show()
else:
    print("Nothing exist")

date_df.write \
    .format("hive") \
    .mode("overwrite") \
    .insertInto("dim_date")

# Define partOfDay logic
# def get_part_of_day(hour):
#     hour = int(hour)
#     if 0 <= hour < 6:
#         return "Night"
#     elif 6 <= hour < 12:
#         return "Morning"
#     elif 12 <= hour < 18:
#         return "Afternoon"
#     else:
#         return "Evening"
#
# # # Prepare 24 rows of time data
# data = []
# for i in range(24):
#     hour_str = f"{i:02d}"  # "00", "01", ...
#     time = f"{hour_str}:00"
#     part_of_day = get_part_of_day(hour_str)
#     data.append((time, part_of_day, hour_str))
#
# # Create DataFrame
# df_dim_time = spark.createDataFrame(data, ["time", "partOfDay", "hour"]) \
#     .withColumn("imported_time", date_format(current_timestamp(), "yyyy-MM-dd HH:mm:ss"))
#
# df_dim_time.show()
#
# df_dim_time = df_dim_time.select("time", "partOfDay", "imported_time", "hour")
#
# # Write to Hive table partitioned by `hour`
# df_dim_time.write \
#   .mode("overwrite") \
#   .format("hive") \
#   .insertInto("dim_time")

# def get_event_type(id):
#     id = int(id)
#     if id == 1:
#         return "view"
#     elif id == 2:
#         return "cart"
#     elif id == 3:
#         return "purchase"
#
# data = []
# for i in range(1, 4):
#     event_type_id = int(i)
#     event_type = get_event_type(event_type_id)
#     data.append((event_type_id, event_type))
#
# # Create DataFrame
# df_dim_user_behavior = spark.createDataFrame(data, ["event_type_id", "event_type"]) \
#     .withColumn("imported_time", date_format(current_timestamp(), "yyyy-MM-dd HH:mm:ss"))
#
# df_dim_user_behavior.show()
#
# # Write to Hive table partitioned by `hour`
# df_dim_user_behavior.write \
#   .mode("overwrite") \
#   .format("hive") \
#   .insertInto("dim_user_behavior")


def get_part(id):
    id = int(id)
    base = 10000000
    lo = 1
    hi = 1000
    res = 0
    while (lo <= hi):
        mid = (lo + hi) >> 1
        if (mid * base > id):
            res = mid * base
            hi = mid - 1
        else:
            lo = mid + 1
    return res

get_part_udf = udf(get_part, IntegerType())

df_dim_product_exist = spark.sql("select * from dim_product")

df_dim_product_exist.show(5)

df_with_product = df.select(col("product_id"), col("category_id"), col("brand"), col("price")).distinct()

df_with_product.show(5)

df_new_product = df_with_product.join(
    df_dim_product_exist.select("product_id", "brand", "price"),
    on=["product_id", "brand", "price"],
    how="left_anti"
).distinct()

df_new_product.show(5)

df_res_product = df_new_product.select(col("product_id"), col("category_id"), col("brand"), col("price")).withColumn("unix_import_time", current_timestamp().cast("long")) .withColumn("imported_time", date_format(current_timestamp(), "yyyy-MM-dd HH:mm:ss")).withColumn("part", get_part_udf(col("product_id"))) \

df_res_product.write \
    .format("hive") \
    .mode("append") \
    .insertInto("dim_product")

df_dim_category_exist = spark.sql("select * from dim_category")
df_dim_category_exist.show(5)

df_with_category = df.select(col("category_id"), col("category_code")).distinct()

df_with_category_split = df_with_category \
    .withColumn("category_main_code", split(col("category_code"), "\.").getItem(0)) \
    .withColumn("category_type", split(col("category_code"), "\.").getItem(1))

df_with_category_split.show(5)

df_new_category = df_with_category_split.join(
    df_dim_category_exist.select("category_id", "category_type"),
    on=["category_id", "category_type"],
    how="left_anti"
).distinct()

df_new_category = (df_new_category.select(col("category_id"), col("category_main_code"), col("category_type"))
                   .withColumn("unix_import_time", current_timestamp().cast("long")) \
                   .withColumn("imported_time", date_format(current_timestamp(), "yyyy-MM-dd HH:mm:ss"))) \

df_new_category.show(5)

df_new_category.write \
    .format("hive") \
    .mode("append") \
    .insertInto("dim_category")
