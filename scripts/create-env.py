#!/usr/bin/env python3
"""Create unique local credentials. Refuse to overwrite existing configuration."""
import os
from pathlib import Path
import secrets
root = Path(__file__).resolve().parents[1]
path = root / '.env'
if path.exists():
    raise SystemExit('.env already exists; preserve it when using existing volumes.')
values = {'BIND_IP': '192.168.74.141', 'SITE_URL': 'http://192.168.74.141:8082'}
for key in ['MYSQL_ROOT_PASSWORD','WORDPRESS_DB_PASSWORD','EXPORTER_PASSWORD','WP_ADMIN_PASSWORD','GRAFANA_ADMIN_PASSWORD']:
    values[key] = secrets.token_urlsafe(32)
fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, 'w') as f:
    f.write(''.join(f'{k}={v}\n' for k,v in values.items()))
print('Created private .env; passwords were not printed.')
