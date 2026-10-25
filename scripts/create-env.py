#!/usr/bin/env python3
"""Create unique local credentials. Refuse to overwrite existing configuration."""
import os
from pathlib import Path
import secrets
root = Path(__file__).resolve().parents[1]
path = root / '.env'
if path.exists():
    raise SystemExit('.env already exists; preserve it when using existing volumes.')
values = {'BIND_IP':'192.168.74.141','WEB_PORT':'8082','PHPMYADMIN_PORT':'5432','GRAFANA_PORT':'3002','PROMETHEUS_PORT':'9091','LOKI_PORT':'3101','MYSQL_DATABASE':'wordpress','MYSQL_USER':'wordpress','WP_ADMIN_USER':'DTC255180105','GRAFANA_ADMIN_USER':'DTC255180105'}
for key in ['MYSQL_ROOT_PASSWORD','WORDPRESS_DB_PASSWORD','EXPORTER_PASSWORD','WP_ADMIN_PASSWORD','GRAFANA_ADMIN_PASSWORD']:
    values[key] = secrets.token_urlsafe(32)
fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, 'w') as f:
    f.write(''.join(f'{k}={v}\n' for k,v in values.items()))
print('Created private .env; passwords were not printed.')
