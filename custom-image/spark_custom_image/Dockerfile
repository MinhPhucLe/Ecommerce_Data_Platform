# Start from Bitnami Spark base image
FROM bitnami/spark:3.5.3

USER root

RUN pip install pytz

# Install system dependencies and build tools
RUN apt-get update && apt-get install -y \
    wget curl git unzip tar jq htop procps lsof \
    nano vim less netcat-openbsd \
    build-essential zlib1g-dev libncurses5-dev libgdbm-dev \
    libnss3-dev libssl-dev libreadline-dev libffi-dev \
    libsqlite3-dev libbz2-dev liblzma-dev tk-dev \
    iputils-ping dnsutils && \
    rm -rf /var/lib/apt/lists/*

# Install Python 3.9 from source
RUN cd /usr/src && \
    wget https://www.python.org/ftp/python/3.9.18/Python-3.9.18.tgz && \
    tar xzf Python-3.9.18.tgz && \
    cd Python-3.9.18 && \
    ./configure --enable-optimizations && \
    make -j$(nproc) && make altinstall && \
    ln -s /usr/local/bin/python3.9 /usr/bin/python3.9 && \
    ln -s /usr/local/bin/pip3.9 /usr/bin/pip3.9 && \
    cd .. && rm -rf Python-3.9.18 Python-3.9.18.tgz

# Set PySpark to use Python 3.9
ENV PYSPARK_PYTHON=/usr/bin/python3.9
ENV PYSPARK_DRIVER_PYTHON=/usr/bin/python3.9

# Download Iceberg + Nessie JARs
#RUN wget -P /opt/bitnami/spark/jars/ https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/1.8.0/iceberg-spark-runtime-3.5_2.12-1.8.0.jar && \
#    wget -P /opt/bitnami/spark/jars/ https://repo1.maven.org/maven2/org/projectnessie/nessie-integrations/nessie-spark-extensions-3.5_2.12/0.102.5/nessie-spark-extensions-3.5_2.12-0.102.5.jar

USER 1001
