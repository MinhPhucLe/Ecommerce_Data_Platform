FROM bitnami/spark:3.5.3

USER root

# Install required packages and download JARs in a single RUN statement
RUN apt-get update && apt-get install -y wget curl netcat-openbsd nano vim less \
    git unzip tar jq htop procps iputils-ping dnsutils lsof && \
    wget -P /opt/bitnami/spark/jars/ https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/1.8.0/iceberg-spark-runtime-3.5_2.12-1.8.0.jar && \
    wget -P /opt/bitnami/spark/jars/ https://repo1.maven.org/maven2/org/projectnessie/nessie-integrations/nessie-spark-extensions-3.5_2.12/0.102.5/nessie-spark-extensions-3.5_2.12-0.102.5.jar

USER 1001
