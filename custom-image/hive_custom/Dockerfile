# Use the official Apache Hive 4.0.0 image as the base
FROM apache/hive:4.0.0

# Switch to root user to install packages
USER root

# Install curl, telnet, wget, netcat (nc), and vim
RUN apt-get update && apt-get install -y \
    curl \
    telnet \
    wget \
    netcat \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Copy entrypoint script and set permissions
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
RUN chmod -R 777 /opt/hive/conf/
RUN chmod -R 777 /opt/hive

# Set environment variables
ENV HIVE_HOME=/opt/hive
ENV PATH=$HIVE_HOME/bin:$PATH

# Download and add the PostgreSQL JDBC driver to Hive's lib folder
RUN curl -L -o $HIVE_HOME/lib/postgresql-42.6.0.jar \
    https://jdbc.postgresql.org/download/postgresql-42.6.0.jar

# Set working directory
WORKDIR $HIVE_HOME

# Switch back to hive user
USER hive

# Use entrypoint.sh to run Hive Metastore or HiveServer2
ENTRYPOINT ["/entrypoint.sh"]
CMD []