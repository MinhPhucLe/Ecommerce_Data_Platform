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

spark = SparkSession.builder.appName("testWriteDimTime") \
    .enableHiveSupport() \
    .config("spark.hadoop.fs.defaultFS", "hdfs://hadoop-hadoop-hdfs-nn:9000/") \
    .config("hive.exec.dynamic.partition", "true") \
    .config("hive.exec.dynamic.partition.mode", "nonstrict") \
    .config("spark.sql.session.timeZone", "Asia/Bangkok") \
    .getOrCreate()

def get_part_of_day(hour):
    hour = int(hour)
    if 0 <= hour < 6:
        return "Night"
    elif 6 <= hour < 12:
        return "Morning"
    elif 12 <= hour < 18:
        return "Afternoon"
    else:
        return "Evening"

# # Prepare 24 rows of time data
data = []
for i in range(24):
    hour_str = f"{i:02d}"  # "00", "01", ...
    time = f"{hour_str}:00"
    part_of_day = get_part_of_day(hour_str)
    data.append((time, part_of_day, hour_str))

# Create DataFrame
df_dim_time = spark.createDataFrame(data, ["time", "partOfDay", "hour"]) \
    .withColumn("imported_time", date_format(current_timestamp(), "yyyy-MM-dd HH:mm:ss"))

df_dim_time.show()

df_dim_time = df_dim_time.select("time", "partOfDay", "imported_time", "hour")

# Write to Hive table partitioned by `hour`
df_dim_time.write \
  .mode("overwrite") \
  .format("hive") \
  .insertInto("dim_time")


def get_event_type(id):
    id = int(id)
    if id == 1:
        return "view"
    elif id == 2:
        return "cart"
    elif id == 3:
        return "purchase"

data = []
for i in range(1, 4):
    event_type_id = int(i)
    event_type = get_event_type(event_type_id)
    data.append((event_type_id, event_type))

# Create DataFrame
df_dim_user_behavior = spark.createDataFrame(data, ["event_type_id", "event_type"]) \
    .withColumn("imported_time", date_format(current_timestamp(), "yyyy-MM-dd HH:mm:ss"))

df_dim_user_behavior.show()

# Write to Hive table partitioned by `hour`
df_dim_user_behavior.write \
  .mode("overwrite") \
  .format("hive") \
  .insertInto("dim_user_behavior")