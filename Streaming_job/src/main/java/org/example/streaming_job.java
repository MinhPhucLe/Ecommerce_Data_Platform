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

public class streaming_job {
    public static void main(String[] args) throws InterruptedException {
        try {
            SparkConf conf = new SparkConf().setAppName("Spark_streaming_event")
                    .setMaster("yarn")
                    .set("spark.memory.storageFraction", "0.2")
                    .set("spark.spark.dynamicAllocation.enabled", "true")
                    .set("spark.dynamicAllocation.minExecutors", "1")        // Optional: Set minimum number of executors
                    .set("spark.dynamicAllocation.maxExecutors", "2")       // Optional: Set maximum number of executors
                    .set("spark.dynamicAllocation.initialExecutors", "2");

            JavaSparkContext sc = new JavaSparkContext(conf);
            JavaStreamingContext ssc = new JavaStreamingContext(sc, new Duration(120000));

            // Kafka configuration
            Map<String, Object> kafkaParams = new HashMap<>();
            kafkaParams.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, "kafka-broker-0.kafka-headless.hadoop-cluster:9092,kafka-broker-1.kafka-headless.hadoop-cluster:9092,kafka-broker-2.kafka-headless.hadoop-cluster:9092");
            kafkaParams.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class.getName());
            kafkaParams.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, org.apache.kafka.common.serialization.ByteArrayDeserializer.class.getName());
            kafkaParams.put(ConsumerConfig.GROUP_ID_CONFIG, "kafka-spark-group-event");
            kafkaParams.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "latest");

            String topic = "ecommerce_tst";

            JavaInputDStream<ConsumerRecord<String, byte[]>> stream =
                    KafkaUtils.createDirectStream(
                            ssc,
                            LocationStrategies.PreferConsistent(),
                            ConsumerStrategies.<String, byte[]>Subscribe(Collections.singletonList(topic), kafkaParams)
                    );

            JavaDStream<Message.EventData> messages = stream.map(record -> {
                try {
                    // Parse the Protobuf message from the byte array
                    return Message.EventData.parseFrom(record.value());
                } catch (InvalidProtocolBufferException e) {
                    e.printStackTrace();
                    return null; // Returning null for simplicity, handle this case in production
                }
            }).filter(Objects::nonNull); // Filter out any null messages due to parsing errors

            AtomicInteger fileCounter = new AtomicInteger(1);

            // Process the messages
            messages.foreachRDD(rdd -> {
                rdd.foreach(message -> {
                    System.out.println("Received message: " + message);
                    // Further processing of ExampleMessage
                });
            });

            SparkSession spark = SparkSession.builder().config(conf).config("spark.hadoop.fs.defaultFS", "hdfs://hadoop-hadoop-hdfs-nn:9000/").getOrCreate();

            messages.foreachRDD(rdd -> {
                StructType schema = new StructType(new StructField[]{
                        DataTypes.createStructField("event_date", DataTypes.StringType, false),
                        DataTypes.createStructField("event_time", DataTypes.StringType, false),
                        DataTypes.createStructField("event_type", DataTypes.StringType, false),
                        DataTypes.createStructField("product_id", DataTypes.LongType, false),
                        DataTypes.createStructField("category_id", DataTypes.LongType, false),
                        DataTypes.createStructField("category_code", DataTypes.StringType, false),
                        DataTypes.createStructField("brand", DataTypes.StringType, false),
                        DataTypes.createStructField("price", DataTypes.FloatType, false),
                        DataTypes.createStructField("user_id", DataTypes.LongType, false),
                        DataTypes.createStructField("user_session", DataTypes.StringType, false),
                });

                JavaRDD<Row> rowRDD = rdd.map(message -> {
                    String event_date = message.getEventDate();
                    String event_time = message.getEventTime();
                    String event_type = message.getEventType();
                    Long product_id = message.getProductId();
                    Long category_id = message.getCategoryId();
                    String category_code = message.getCategoryCode();
                    String brand = message.getBrand();
                    Float price = message.getPrice();
                    Long user_id = message.getUserId();
                    String user_session = message.getUserSession();

                    return RowFactory.create(
                            event_date,
                            event_time,
                            event_type,
                            product_id,
                            category_id,
                            category_code,
                            brand,
                            price,
                            user_id,
                            user_session
                    );
                });

                Dataset<Row> df = spark.createDataFrame(rowRDD, schema);
                df = df.withColumn("event_hour", functions.hour(df.col("event_time")));
                df.write().mode(SaveMode.Append)
                        .partitionBy("event_date", "event_hour")
                        .parquet("hdfs://hadoop-hadoop-hdfs-nn:9000/data/event_ecommerce");
            });
            messages.print(); // Print messages for debugging

            ssc.start();
            ssc.awaitTermination();

        } catch (Exception e) {
            System.err.println("Error occurred: " + e.getMessage());
            e.printStackTrace();
        }
    }
}