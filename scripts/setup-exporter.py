#!/usr/bin/env python3
"""Create a dedicated metrics account without exposing its password in argv."""
import os, subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
env=dict(line.split('=',1) for line in (root/'.env').read_text().splitlines() if line and not line.startswith('#'))
password=env['EXPORTER_PASSWORD']
if not password or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in password):
    raise SystemExit('EXPORTER_PASSWORD must be a nonempty URL-safe random string.')
sql=f"CREATE USER IF NOT EXISTS 'exporter'@'%' IDENTIFIED BY '{password}' WITH MAX_USER_CONNECTIONS 3; ALTER USER 'exporter'@'%' IDENTIFIED BY '{password}'; GRANT PROCESS, REPLICATION CLIENT, SELECT ON *.* TO 'exporter'@'%';"
subprocess.run(['docker','compose','exec','-T','mysql','sh','-c','MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -uroot'],cwd=root,input=sql,text=True,check=True)
secret=root/'secrets'; secret.mkdir(exist_ok=True,mode=0o700)
(secret/'exporter.cnf').write_text(f'[client]\nuser=exporter\npassword={password}\nhost=mysql\nport=3306\n')
os.chmod(secret/'exporter.cnf',0o644) # parent directory 0700; mounted exporter UID reads file
os.chmod(secret,0o700)
print('Dedicated exporter user and private configuration ready.')
