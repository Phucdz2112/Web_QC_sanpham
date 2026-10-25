#!/usr/bin/env python3
"""Backup MySQL and WordPress files to an explicitly external directory."""
import datetime, os, subprocess, sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
dest=Path(sys.argv[1]).expanduser().resolve() if len(sys.argv)>1 else None
if dest is None or dest==root or root in dest.parents:
    raise SystemExit('Usage: python3 scripts/backup.py /path/OUTSIDE/repository')
dest.mkdir(mode=0o700,parents=True,exist_ok=True); os.chmod(dest,0o700)
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
sql=dest/f'wordpress-{stamp}.sql'
with sql.open('wb') as f:
    os.chmod(sql,0o600)
    subprocess.run(['docker','compose','exec','-T','mysql','sh','-c','MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysqldump -uroot --single-transaction --no-tablespaces --routines --triggers wordpress'],cwd=root,stdout=f,check=True)
container=subprocess.check_output(['docker','compose','ps','-q','wordpress'],cwd=root,text=True).strip()
archive=dest/f'wordpress-files-{stamp}.tar.gz'
with archive.open('wb') as f:
    os.chmod(archive,0o600)
    subprocess.run(['docker','exec',container,'tar','czf','-','-C','/var/www/html','.'],stdout=f,check=True)
print('Created private SQL and WordPress file backup outside repository.')
