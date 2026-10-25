#!/usr/bin/env python3
"""Lab-only backup/restore and controlled restart acceptance test."""
import datetime, json, os, re, subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
out=Path(os.environ.get('EVIDENCE_DIR',str(root.parent/'web-qc-artifacts/evidence'))).resolve()
if out==root or root in out.parents: raise SystemExit('Evidence must stay outside repository')
out.mkdir(parents=True,exist_ok=True)
def run(*args,**kw): return subprocess.run(args,cwd=root,check=True,**kw)
def sql(query,database=None):
    args=['docker','compose','exec','-T','mysql','sh','-c','MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -uroot --batch --skip-column-names'+(' '+database if database else '')]
    return subprocess.check_output(args,cwd=root,input=query,text=True).strip()
def digest(database):
    return sql("SELECT COUNT(*), MD5(GROUP_CONCAT(MD5(CONCAT_WS('|',ID,post_title,post_content,post_status)) ORDER BY ID SEPARATOR ';')) FROM "+database+".wp_posts WHERE post_type='product';")
env=dict(line.split('=',1) for line in (root/'.env').read_text().splitlines() if line and not line.startswith('#'))
database=env.get('MYSQL_DATABASE','wordpress')
assert re.fullmatch(r'[A-Za-z0-9_]+',database)
before=digest(database)
backup=out.parent/'backups'/'after-deploy'
run('python3','scripts/backup.py',str(backup))
dump=max(backup.glob('wordpress-*.sql'),key=lambda p:p.stat().st_mtime)
schema='wordpress_verify_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M%S')
assert re.fullmatch(r'wordpress_verify_[0-9]{14}',schema)
sql('CREATE DATABASE '+schema+' CHARACTER SET utf8mb4;')
try:
    sql(dump.read_text(),schema)
    restored=digest(schema)
    assert restored==before, 'Restored product digest differs'
finally:
    sql('DROP DATABASE '+schema+';')
grants=sql("SHOW GRANTS FOR 'wordpress'@'%';")
assert '`wordpress`.*' in grants and 'ALL PRIVILEGES ON *.*' not in grants
(out/'db-grants.txt').write_text(grants+'\n')
run('docker','compose','restart','wordpress','mysql')
run('docker','compose','up','-d','--wait','--wait-timeout','300')
after=digest(database); assert before==after,'Restart changed product digest'
result={'backup_sql_nonempty':dump.stat().st_size>0,'restore_product_digest_matches':True,'temporary_restore_schema_removed':True,'restart_product_digest_matches':True,'app_database_grants_scoped':True,'product_count':int(before.split()[0])}
(out/'operations.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result),flush=True)
