#!/bin/sh
source venv/bin/activate

# waiting for the database to be up
while true; do
  flask deploy
  if [[ "$?" == "0" ]]; then
    break
  fi
  echo Deploy command failed, retrying in 5 secs...
  sleep 5
done

exec gunicorn -b :8000 --access-logfile - --error-logfile - myblog:app