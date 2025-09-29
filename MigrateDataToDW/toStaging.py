import os
from datetime import datetime, timedelta, timezone

from pyspark.sql import SparkSession
from pyspark.sql.functions import date_format, unix_timestamp, current_timestamp, to_timestamp, concat_ws
from pyspark.sql.types import StringType, StructType, StructField, LongType, FloatType

# Define dataset timeline
START_2019 = datetime(2019, 10, 1).date()
# START_2025 = datetime(2025, 4, 20).date()
START_2025 = datetime(2025, 5, 26).date()

# SparkSession with Asia/Bangkok timezone for current_timestamp()
spark = SparkSession.builder.appName("MoveStagingToWarehouse") \
    .enableHiveSupport() \
    .config("spark.hadoop.fs.defaultFS", "hdfs://hadoop-hadoop-hdfs-nn:9000/") \
    .config("hive.exec.dynamic.partition", "true") \
    .config("hive.exec.dynamic.partition.mode", "nonstrict") \
    .config("spark.sql.session.timeZone", "Asia/Bangkok") \
    .getOrCreate()

# Schema for incoming CSV files
schema = StructType([
    StructField("event_time", StringType(), True),
    StructField("event_type", StringType(), True),
    StructField("product_id", LongType(), True),
    StructField("category_id", StringType(), True),
    StructField("category_code", StringType(), True),
    StructField("brand", StringType(), True),
    StructField("price", FloatType(), True),
    StructField("user_id", LongType(), True),
    StructField("user_session", StringType(), True),
    StructField("event_date", StringType(), True),
    StructField("event_time_only", StringType(), True)
])

def process_day_data(file_path):
    df = spark.read.option("delimiter", ",").option("header", True).csv(file_path, schema=schema)

    df.show(5)

    # Ensure event_date and event_time_only are not null
    df = df.filter(df["event_date"].isNotNull() & df["event_time_only"].isNotNull())

    # Combine event_date and event_time_only to form event_datetime
    df = df.withColumn("event_datetime",
                       to_timestamp(concat_ws(" ", "event_date", "event_time_only"), "yyyy-MM-dd HH:mm:ss"))

    # Ensure event_datetime is not null
    df = df.filter(df["event_datetime"].isNotNull())
    # Use Spark's current_timestamp() (which now respects Asia/Bangkok timezone)
    df = df.withColumn("imported_time", unix_timestamp(current_timestamp()).cast(StringType()))
    df = df.withColumn("day", date_format("event_datetime", "yyyyMMdd").cast(StringType()))
    df = df.withColumn("hour", date_format("event_datetime", "HH").cast(StringType()))

    # Drop event_datetime (optional)
    df = df.drop("event_datetime")

    df.show(5)

    # Filter out rows where day or hour is null
    df = df.filter(df["day"].isNotNull() & df["hour"].isNotNull())

    df.show(5)

    # Write to Hive
    df.write \
        .format("hive") \
        .mode("overwrite") \
        .insertInto("tst_staging")

# Set `now` to GMT+7 for filename lookup

now = datetime.now(timezone(timedelta(hours=7))).date()
print("HEREEEEEEEEEEEEEEEEEEEEEEEE: " + datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S"))
DATA_DIR = "/tmp/data/data_tst/"
days_passed = now - START_2025
dataset_date = START_2019 + days_passed
file_path = DATA_DIR + f"events_{dataset_date}.csv"

process_day_data(file_path)
