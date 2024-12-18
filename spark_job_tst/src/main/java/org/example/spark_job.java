package org.example;

import org.apache.spark.sql.Dataset;
import org.apache.spark.sql.Row;
import org.apache.spark.sql.RowFactory;
import org.apache.spark.sql.SparkSession;
import org.apache.spark.sql.types.DataTypes;
import org.apache.spark.sql.types.StructField;
import org.apache.spark.sql.types.StructType;

import java.util.Arrays;

public class spark_job {
    public static void main(String[] args) {
        // Initialize a SparkSession
        SparkSession spark = SparkSession.builder()
                .appName("SimpleDataFrameExample")
                .config("spark.hadoop.fs.defaultFS", "hdfs://hadoop-hadoop-hdfs-nn:9000/")
                .config("spark.driver.extraJavaOptions", "--add-opens=java.base/java.util=ALL-UNNAMED")
                .config("spark.executor.extraJavaOptions", "--add-opens=java.base/java.util=ALL-UNNAMED")
                        .getOrCreate();

        // Define the schema
        StructType schema = DataTypes.createStructType(new StructField[]{
                DataTypes.createStructField("name", DataTypes.StringType, false),
                DataTypes.createStructField("age", DataTypes.IntegerType, false),
                DataTypes.createStructField("location", DataTypes.StringType, false)
        });

        // Create data
        Object[][] data = new Object[][]{
                {"Alice", 30, "New York"},
                {"Bob", 25, "San Francisco"},
                {"Cathy", 28, "Los Angeles"},
                {"David", 30, "San Francisco"},
        };

        // Convert data into Rows
        Row[] rows = new Row[data.length];
        for (int i = 0; i < data.length; i++) {
            rows[i] = RowFactory.create(data[i]);
        }

        // Create DataFrame
        Dataset<Row> dataFrame = spark.createDataFrame(Arrays.asList(rows), schema);

        // Show the DataFrame
        dataFrame.show();

        Dataset<Row> Sanfrancisco = dataFrame.filter(dataFrame.col("location").equalTo("San Francisco"));
        Sanfrancisco.show();
        Sanfrancisco.write().mode("overwrite").csv("hdfs://hadoop-hadoop-hdfs-nn:9000/tst_folder/data.csv");

        // Stop the SparkSession
        spark.stop();
    }
}
