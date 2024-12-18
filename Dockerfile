# Use the official Airflow image as the base
FROM apache/airflow:2.8.4-python3.9

USER root

# Install Java (JDK) dependencies
RUN apt update && apt install -y default-jdk

# Set the environment variables (example)
ENV HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop
ENV SPARK_HOME=/home/airflow/.local/lib/python3.9/site-packages/pyspark
ENV JAVA_HOME=/usr/lib/jvm/java-1.17.0-openjdk-amd64
# Copy your custom Airflow configurations, DAGs, or any other necessary files
#COPY ./spark-config/bin /opt/spark/bin
#COPY ./spark-config/opt/spark /opt/spark

# Ensure correct permissions to access and modify /opt/spark
#RUN chmod -R 755 /opt/spark
#RUN chmod -R 777 /opt/spark/bin
RUN chmod -R 777 /home/airflow/.local/bin
USER airflow
# Install additional dependencies if needed (e.g., Hadoop, Spark, or custom Python packages)
RUN pip install apache-airflow-providers-apache-spark
RUN pip install apache-airflow-providers-trino
RUN pip install pyspark==3.5.1
RUN pip install pytz

# Set the working directory
#WORKDIR /opt/airflow

# Define entrypoint and command (optional)
# ENTRYPOINT ["bash", "-c", "exec airflow webserver"]
