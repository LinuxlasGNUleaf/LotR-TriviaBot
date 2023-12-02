#!/bin/bash

echo "===> RUNNING SCRIPT FROM $(whoami) ($(id))"
if [ ! "$(whoami)" == 'root' ]; then
    echo "Skipping script since I'm NOT root"
else
  IDENT="$(date +%d_%m_%y-%H-%M-%S)"
  FNAME="/backup/$IDENT.sql"
  sleep 2
  pg_dump postgres -U postgres > "$FNAME"
  tar -czf "/backup/$IDENT.tar.gz" --directory=/backup "$IDENT.sql"
  echo "INFO: removing the temp sql file."
  rm "$FNAME"
  echo "INFO: finished backup of database."
fi