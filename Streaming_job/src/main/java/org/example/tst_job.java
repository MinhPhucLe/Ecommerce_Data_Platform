package org.example;

import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.text.SimpleDateFormat;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import static org.apache.spark.sql.functions.col;  // Static import for column functions
import static org.apache.spark.sql.functions.date_format;
import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.common.serialization.StringDeserializer;
import org.apache.spark.SparkConf;
import org.apache.spark.api.java.JavaRDD;
import org.apache.spark.api.java.JavaSparkContext;
import org.apache.spark.sql.*;
import org.apache.spark.streaming.Duration;
import org.apache.spark.streaming.api.java.JavaDStream;
import org.apache.spark.streaming.api.java.JavaInputDStream;
import org.apache.spark.streaming.api.java.JavaStreamingContext;
import org.apache.spark.streaming.kafka010.*;
import com.google.protobuf.InvalidProtocolBufferException;
import org.example.proto.Message;
import java.util.Base64;
import java.util.Objects;
import static org.apache.spark.sql.functions.from_unixtime;
import org.apache.spark.sql.types.DataTypes;
import org.apache.spark.sql.types.StructField;
import org.apache.spark.sql.types.StructType;
import org.apache.spark.sql.*;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.IvParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

public class tst_job {
    public static void main(String[] args) throws InterruptedException {
        try {
            SparkConf conf = new SparkConf().setAppName("Spark_streaming_event")
                    .setMaster("yarn")
                    .set("spark.memory.storageFraction", "0.2")
                    .set("spark.sql.catalogImplementation", "hive")
                    .set("hive.exec.dynamic.partition", "true")
                    .set("hive.exec.dynamic.partition.mode", "nonstrict");

            JavaSparkContext sc = new JavaSparkContext(conf);


            SparkSession spark = SparkSession.builder().config(conf).config("spark.hadoop.fs.defaultFS", "hdfs://hadoop-hadoop-hdfs-nn:9000/").enableHiveSupport().getOrCreate();


            StructType schema = new StructType(new StructField[]{
                    DataTypes.createStructField("name", DataTypes.StringType, true),
                    DataTypes.createStructField("year", DataTypes.IntegerType, true),
                    DataTypes.createStructField("age", DataTypes.IntegerType, true)
            });

            List<Row> data = Arrays.asList(
                    RowFactory.create("Alice", 25, 2025),
                    RowFactory.create("Bob", 30, 2024)
            );

            JavaRDD<Row> rowRDD = sc.parallelize(data);

            Dataset<Row> df = spark.createDataFrame(rowRDD, schema);
            df.show();
            df.write()
                    .mode(SaveMode.Append)
                    .format("hive")
                    .partitionBy("age")
                    .saveAsTable("tst");

        } catch (Exception e) {
            System.err.println("Error occurred: " + e.getMessage());
            e.printStackTrace();
        }
    }
}