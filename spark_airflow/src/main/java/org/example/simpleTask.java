package org.example;

import org.apache.spark.sql.*;

public class simpleTask {
    public static void main(String[] args) {
        SparkSession spark = SparkSession.builder()
                .appName("Load data from staging to Staging")
                .master("yarn")
                .config("spark.sql.catalogImplementation", "hive")
                .config("spark.hadoop.fs.defaultFS", "hdfs://hadoop-hadoop-hdfs-nn:9000")
                .config("spark.executor.memory", "1g")
                .config("spark.driver.memory", "1g")
                .enableHiveSupport()
                .getOrCreate();

        Dataset<Row> df = spark.read().parquet("hdfs://hadoop-hadoop-hdfs-nn:9000/data/event_ecommerce/event_date=20191001");
        Dataset<Row> df1 = df.limit(100);
        df1.show();
        df1.write().mode(SaveMode.Overwrite).parquet("hdfs://hadoop-hadoop-hdfs-nn:9000/test_simple_task");
    }
}
