#!/bin/bash
set -e

if [ "$1" = "hiveserver2" ]; then
    echo "Starting HiveServer2..."
    exec hive --service hiveserver2
elif [ "$1" = "metastore" ]; then
    echo "Starting Hive Metastore..."
    exec hive --service metastore
else
    exec "$@"
fi
