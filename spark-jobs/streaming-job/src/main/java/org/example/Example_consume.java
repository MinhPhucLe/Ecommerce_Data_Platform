package org.example;

import java.time.Instant;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

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

import java.util.Objects;
import static org.apache.spark.sql.functions.from_unixtime;
import org.apache.spark.sql.types.DataTypes;
import org.apache.spark.sql.types.StructField;
import org.apache.spark.sql.types.StructType;
import org.example.proto.Event;

import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.atomic.AtomicReference;

public class Example_consume {
    public static void main(String[] args) throws InterruptedException {
        try {
            SparkConf conf = new SparkConf().setAppName("KafkaSparkStreamingAppOnNet")
//                    .setMaster("yarn")
                    .set("spark.memory.storageFraction", "0.2")
                    .set("spark.sql.catalogImplementation", "hive")
                    .set("hive.exec.dynamic.partition", "true")
                    .set("hive.exec.dynamic.partition.mode", "nonstrict");

            JavaSparkContext sc = new JavaSparkContext(conf);
            JavaStreamingContext ssc = new JavaStreamingContext(sc, new Duration(120000));
            ssc.checkpoint("hdfs://hadoop-hadoop-hdfs-nn:9000/spark-checkpoints/example_consume");

            // Kafka configuration
            Map<String, Object> kafkaParams = new HashMap<>();
            kafkaParams.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, "kafka-broker-0.kafka-headless.hadoop-cluster:9092,kafka-broker-1.kafka-headless.hadoop-cluster:9092,kafka-broker-2.kafka-headless.hadoop-cluster:9092");
            kafkaParams.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class.getName());
            kafkaParams.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, org.apache.kafka.common.serialization.ByteArrayDeserializer.class.getName());
            kafkaParams.put(ConsumerConfig.GROUP_ID_CONFIG, "kafka-spark-group-onNet");
            kafkaParams.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "latest");

            AtomicReference<OffsetRange[]> offsetRangesRef = new AtomicReference<>();

            String topic = "ecommerce_event";
            JavaInputDStream<ConsumerRecord<String, byte[]>> stream =
                    KafkaUtils.createDirectStream(
                            ssc,
                            LocationStrategies.PreferConsistent(),
                            ConsumerStrategies.<String, byte[]>Subscribe(Collections.singletonList(topic), kafkaParams)
                    );

            JavaDStream<Event.EventData> messages = stream.transform(rdd -> {
                OffsetRange[] offsetRanges = ((HasOffsetRanges) rdd.rdd()).offsetRanges();
                offsetRangesRef.set(offsetRanges);
                return rdd;
            }).map(record -> {
                try {
                    return Event.EventData.parseFrom(record.value());
                } catch (InvalidProtocolBufferException e) {
                    e.printStackTrace();
                    return null;
                }
            }).filter(Objects::nonNull);

            // Process the messages
            messages.foreachRDD(rdd -> {
                rdd.foreach(message -> {
                    System.out.println("Received message: " + message);
                    // Further processing of ExampleMessage
                });
            });

            SparkSession spark = SparkSession.builder().config(conf).config("spark.hadoop.fs.defaultFS", "hdfs://hadoop-hadoop-hdfs-nn:9000").enableHiveSupport().getOrCreate();

            StructType schema = new StructType(new StructField[]{
                    DataTypes.createStructField("event_time", DataTypes.StringType, true),
                    DataTypes.createStructField("event_date", DataTypes.StringType, true),
                    DataTypes.createStructField("event_time_only", DataTypes.StringType, true),
                    DataTypes.createStructField("event_type", DataTypes.StringType, true),
                    DataTypes.createStructField("product_id", DataTypes.LongType, true),
                    DataTypes.createStructField("category_id", DataTypes.StringType, true),
                    DataTypes.createStructField("category_code", DataTypes.StringType, true),
                    DataTypes.createStructField("brand", DataTypes.StringType, true),
                    DataTypes.createStructField("price", DataTypes.FloatType, true),
                    DataTypes.createStructField("user_id", DataTypes.LongType, true),
                    DataTypes.createStructField("user_session", DataTypes.StringType, true),
                    DataTypes.createStructField("imported_time", DataTypes.StringType, true),
                    DataTypes.createStructField("day", DataTypes.StringType, true),
                    DataTypes.createStructField("hour", DataTypes.StringType, true),
            });

            messages.foreachRDD(rdd -> {
                if (!rdd.isEmpty()) {

                    long unixTime = System.currentTimeMillis() / 1000L;
                    JavaRDD<Row> rowRDD = rdd.map(message -> {
                        String event_time = message.getEventTime();
                        String event_date = message.getEventDate();
                        String event_time_only = message.getEventTimeOnly();
                        if (event_time.isEmpty()) System.out.println("Empty Time, may be wrong: ");
                        long epochMilli = Instant.now().toEpochMilli();

                        // Convert to GMT+7 timezone
                        ZonedDateTime dateTime = Instant.ofEpochMilli(epochMilli)
                                .atZone(ZoneId.of("GMT+7"));

                        // Format as YYYY:MM:DD HH:MM:ss
                        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy:MM:dd HH:mm:ss");

                        String formatted = dateTime.format(formatter);

                        String[] dateParts = event_date.split("-");         // [yyyy, MM, dd]
                        String[] timeParts = event_time_only.split(":");

                        String date = dateParts[0] + dateParts[1] + dateParts[2];
                        String hour = timeParts[0];

                        return RowFactory.create(
                                event_time,
                                event_date, // for called number
                                event_time_only,
                                message.getEventType(),
                                message.getProductId(),
                                message.getCategoryId(),
                                message.getCategoryCode(),
                                message.getBrand(),
                                message.getPrice(),
                                message.getUserId(),
                                message.getUserSession(),
                                formatted,
                                date,
                                hour
                        );
                    });


                    // Format the current date and hour in GMT+7
///                DateTimeFormatter dateFormatter = DateTimeFormatter.ofPattern("yyyyMMdd");
///                DateTimeFormatter hourFormatter = DateTimeFormatter.ofPattern("HH");

                    Dataset<Row> df = spark.createDataFrame(rowRDD, schema);
                    df.limit(5).show();

                    df.write()
                            .mode(SaveMode.Append)
                            .format("hive")
                            .partitionBy("day", "hour")
                            .saveAsTable("tst_staging");
                    ((CanCommitOffsets) stream.inputDStream()).commitAsync(offsetRangesRef.get());
                }
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

