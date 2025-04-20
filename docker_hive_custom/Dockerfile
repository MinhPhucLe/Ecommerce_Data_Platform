FROM openjdk:8-jdk-alpine

ENV HIVE_VERSION 4.0.0
ENV HIVE_HOME /opt/hive

# Install dependencies
RUN apk update && \
    apk add --no-cache bash curl git && \
    curl -O https://archive.apache.org/dist/hive/hive-${HIVE_VERSION}/apache-hive-${HIVE_VERSION}-bin.tar.gz && \
    tar -xvf apache-hive-${HIVE_VERSION}-bin.tar.gz && \
    mv apache-hive-${HIVE_VERSION}-bin ${HIVE_HOME} && \
    rm apache-hive-${HIVE_VERSION}-bin.tar.gz

# Configure Hive Metastore properties
COPY hive-site.xml /opt/hive/conf/

# Expose Hive Metastore port
EXPOSE 9083

CMD ["/opt/hive/bin/hive", "--service", "metastore"]
