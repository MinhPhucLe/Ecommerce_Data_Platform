from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, sum, max, datediff, percent_rank, concat_ws, lit, to_date, when
from pyspark.sql.window import Window
from datetime import datetime, timezone, timedelta

# Create SparkSession
spark = SparkSession.builder \
    .appName("Calculate_RFM") \
    .config("spark.hadoop.fs.defaultFS", "hdfs://hadoop-hadoop-hdfs-nn:9000/") \
    .config("hive.exec.dynamic.partition", "true") \
    .config("hive.exec.dynamic.partition.mode", "nonstrict") \
    .config("spark.sql.session.timeZone", "Asia/Bangkok") \
    .enableHiveSupport() \
    .getOrCreate()

now = datetime.now(timezone(timedelta(hours=7)))

# Reference dates
START_2019 = datetime(2019, 10, 1).date()
START_2025 = datetime(2025, 6, 12).date()
for i in range(20, 21):
    target_date = now.date()
    days_passed = (target_date - START_2025).days
    result_date = START_2019 + timedelta(days=days_passed) + timedelta(days=i)
    day_query = result_date.strftime("%Y%m%d")
    print(day_query)

    # Load data
    df = spark.sql(f"select * from purchase_order WHERE date <= '{day_query}'")

    # Calculate recency
    today = result_date
    df_last_purchase = df.groupBy("user_id") \
        .agg(max("date").alias("last_purchase"))

    df_last_purchase = df_last_purchase.withColumn(
        "recency",
        datediff(
            to_date(lit(day_query), "yyyyMMdd"),
            to_date(col("last_purchase"), "yyyyMMdd")
        )
    )

    df_last_purchase = df_last_purchase.withColumn(
        "r_score",
        when(col("recency") <= 15, 5)
        .when(col("recency") <= 30, 4)
        .when(col("recency") <= 45, 3)
        .when(col("recency") <= 60, 2)
        .otherwise(1)
    )

    # Frequency
    df_freq = df.groupBy("user_id") \
        .agg(count("*").alias("frequency"))

    w_freq = Window.orderBy(col("frequency").desc())
    df_freq = df_freq.withColumn("frequency_rank", percent_rank().over(w_freq))

    df_freq = df_freq.withColumn(
        "f_score",
        when(col("frequency_rank") <= 0.1, 5)
        .when(col("frequency_rank") <= 0.2, 4)
        .when(col("frequency_rank") <= 0.4, 3)
        .when(col("frequency_rank") <= 0.7, 2)
        .otherwise(1)
    )

    # Monetary
    df_monetary = df.groupBy("user_id") \
        .agg(sum("price").alias("monetary"))

    w_m = Window.orderBy(col("monetary").desc())
    df_monetary = df_monetary.withColumn("monetary_rank", percent_rank().over(w_m))

    df_monetary = df_monetary.withColumn(
        "m_score",
         when(col("monetary_rank") <= 0.2, 5)
        .when(col("monetary_rank") <= 0.4, 4)
        .when(col("monetary_rank") <= 0.6, 3)
        .when(col("monetary_rank") <= 0.8, 2)
        .otherwise(1)
    )

    rfm = df_last_purchase \
        .join(df_freq, "user_id") \
        .join(df_monetary, "user_id")

    rfm = rfm.withColumn("rfm_score", concat_ws("", col("r_score").cast("string"), col("f_score").cast("string"), col("m_score").cast("string")))

    rfm = rfm.withColumn("calculated_date", lit(day_query))

    rfm = rfm.withColumn(
        "segment",
        when(col("rfm_score").isin("555", "554", "545", "544", "455", "445"), "Champions") # moi giao dich, hao phong
        .when(col("rfm_score").isin("543", "444", "435", "355", "354", "345", "344", "335"), "Loyal Customers") # trung thanh
        .when(col("rfm_score").isin("553", "551", "552", "541", "542", "533", "532", "531", "452", "451", "442", "441", "431", "453", "433", "432", "423", "353", "352", "351", "342", "341", "333", "323"), "Potential Loyalist") # tiem nang
        .when(col("rfm_score").isin("512", "511", "422", "421", "412", "411", "311"), "Recent Customers") # moi mua gan day
        .when(col("rfm_score").isin("525", "524", "523", "522", "521", "515", "514", "513", "425", "424", "413", "414", "415", "315", "314", "313"), "Promising") # cung moi mua gan day nhung suc mua lon
        .when(col("rfm_score").isin("535", "534", "443", "434", "343", "334", "325", "324"), "Customers Needing Attention") # suc mua va tan suat lon nhung lau khong mua hang
        .when(col("rfm_score").isin("331", "321", "312", "221", "213"), "About To Sleep") # lau chua mua hang va gio hang, tan suat thap truoc do
        .when(col("rfm_score").isin("255", "254", "245", "244", "253", "252", "243", "242", "235", "234", "225", "224", "153", "152", "145", "143", "142", "135", "134", "133", "125", "124"), "At Risk")
        .when(col("rfm_score").isin("155", "154", "144", "214", "215", "115", "114", "113"), "Can’t Lose Them")
        .when(col("rfm_score").isin("332", "322", "231", "241", "251", "233", "232", "223", "222", "132", "123", "122", "212", "211"), "Hibernating")
        .when(col("rfm_score").isin("111", "112", "121", "131", "141", "151"), "Lost")
        .otherwise("Unknown")
    )

    rfm_result = rfm.select("user_id", "recency", "frequency", "monetary", "r_score", "f_score", "m_score", "rfm_score", "segment", "calculated_date")

    rfm_result.show(5)


    rfm_result.write \
        .mode("overwrite") \
        .insertInto("mart_rfm_score")
