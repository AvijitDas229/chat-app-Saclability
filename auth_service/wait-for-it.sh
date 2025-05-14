#!/bin/bash
# wait-for-it.sh

# Usage: ./wait-for-it.sh host:port -- command args
# Example: ./wait-for-it.sh mongo:27017 -- python app.py

host="$1"
shift
port="$1"
shift
cmd="$@"

until nc -z -v -w30 $host $port
do
  echo "Waiting for $host:$port to be available..."
  sleep 5
done

echo "$host:$port is available, executing command..."
exec $cmd
