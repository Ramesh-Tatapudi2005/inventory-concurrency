#!/bin/bash

# Configuration - update these if your docker-compose differs
DB_CONTAINER_NAME=$(docker ps --filter "name=db" --format "{{.Names}}")
PG_USER="user"
PG_DB="inventory_db"

if [ -z "$DB_CONTAINER_NAME" ]; then
  echo "Error: Database container not found. Is docker-compose running?"
  exit 1
fi

echo "Monitoring active locks on 'products' table... (Press Ctrl+C to stop)"
echo "--------------------------------------------------------------------"

# Loop indefinitely to show real-time lock status
while true; do
  # Clear the screen for a cleaner view
  clear
  echo "--- Active Database Locks at $(date +%H:%M:%S) ---"
  
  # Query pg_locks and join with pg_class to see table names
  docker exec -it "$DB_CONTAINER_NAME" psql -U "$PG_USER" -d "$PG_DB" -c "
    SELECT 
      a.pid, 
      t.relname AS table_name, 
      l.mode, 
      l.locktype, 
      l.granted, 
      SUBSTRING(a.query FROM 1 FOR 40) AS current_query
    FROM pg_locks l
    JOIN pg_class t ON l.relation = t.oid
    JOIN pg_stat_activity a ON l.pid = a.pid
    WHERE t.relname = 'products' 
      AND a.datname = '$PG_DB';
  "
  
  # Refresh every 1 second
  sleep 1
done