#!/bin/sh
set -eu
case "$EXPORTER_PASSWORD" in
  ''|*[!a-zA-Z0-9_-]*) echo 'Exporter password must be a nonempty URL-safe random string.' >&2; exit 1 ;;
esac
export MYSQL_PWD="$MYSQL_ROOT_PASSWORD"
mysql --protocol=socket -uroot <<SQL
CREATE USER IF NOT EXISTS 'exporter'@'%' IDENTIFIED BY '$EXPORTER_PASSWORD' WITH MAX_USER_CONNECTIONS 3;
ALTER USER 'exporter'@'%' IDENTIFIED BY '$EXPORTER_PASSWORD';
GRANT PROCESS, REPLICATION CLIENT, SELECT ON *.* TO 'exporter'@'%';
SQL
umask 022
printf '[client]\nuser=exporter\npassword=%s\nhost=mysql\nport=3306\n' "$EXPORTER_PASSWORD" > /exporter/exporter.cnf
chmod 644 /exporter/exporter.cnf
echo 'Dedicated metrics account and configuration are ready.'
