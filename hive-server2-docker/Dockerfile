# Use the official Apache Hive 4.0.0 image as the base
FROM apache/hive:4.0.0

# Install curl and other required utilities
USER root
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

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

# Start Hive Metastore when the container runs
CMD ["hive", "--service", "hive-server2"]
