#!/usr/bin/env python3
"""Verify the running stack. Output and evidence must stay outside the repo."""
import base64, datetime, json, os, subprocess, urllib.parse, urllib.request
from pathlib import Path
root=Path(__file__).resolve().parents[1]
out=Path(os.environ.get('EVIDENCE_DIR',str(root.parent/'web-qc-artifacts/evidence'))).resolve()
if out==root or root in out.parents: raise SystemExit('EVIDENCE_DIR must be outside repository')
out.mkdir(parents=True,exist_ok=True)
env=dict(line.split('=',1) for line in (root/'.env').read_text().splitlines() if line and not line.startswith('#'))
results=[]
def check(name,ok,detail=None):
    results.append({'name':name,'passed':bool(ok),'detail':detail})
    print(('PASS ' if ok else 'FAIL ')+name,flush=True)
def request(url,params=None,auth=False):
    if params: url+='?'+urllib.parse.urlencode(params)
    req=urllib.request.Request(url)
    if auth: req.add_header('Authorization','Basic '+base64.b64encode((env.get('GRAFANA_ADMIN_USER','DTC255180105')+':'+env['GRAFANA_ADMIN_PASSWORD']).encode()).decode())
    with urllib.request.urlopen(req,timeout=20) as r:
        return r.status,dict(r.headers),r.read()
def getjson(url,params=None,auth=False): return json.loads(request(url,params,auth)[2])
def local(key,default): return 'http://127.0.0.1:'+env.get(key,str(default))
site='http://'+env.get('BIND_IP','127.0.0.1')+':'+env.get('WEB_PORT','8082')
def prom(expr): return getjson(local('PROMETHEUS_PORT',9091)+'/api/v1/query',{'query':expr})['data']['result']
def dc(*args): return subprocess.check_output(['docker','compose',*args],cwd=root,text=True)
status,headers,body=request(site)
check('Website serves product catalog',status==200 and b'phucstudio' in body.replace(b'<span>',b'').replace(b'</span>',b'') or status==200 and 'Bộ sưu tập'.encode() in body)
for key in ['X-Content-Type-Options','X-Frame-Options','Referrer-Policy','Permissions-Policy']:
    check('Nginx header '+key,any(k.lower()==key.lower() for k in headers))
check('phpMyAdmin HTTP',request(local('PHPMYADMIN_PORT',5432))[0]==200)
targets=getjson(local('PROMETHEUS_PORT',9091)+'/api/v1/targets')['data']['activeTargets']
check('Four scrape targets UP',len(targets)==4 and all(x['health']=='up' for x in targets))
(out/'prometheus-targets.json').write_text(json.dumps(targets,indent=2))
for metric in ['nginx_up','mysql_up']:
    r=prom(metric); check(metric+' is 1',bool(r) and all(float(x['value'][1])==1 for x in r))
r=prom('count(container_last_seen{name!=""})'); check('Container metrics present',bool(r) and float(r[0]['value'][1])>0)
check('Grafana database healthy',getjson(local('GRAFANA_PORT',3002)+'/api/health')['database']=='ok')
dashboard=getjson(local('GRAFANA_PORT',3002)+'/api/dashboards/uid/web-qc-system',auth=True)['dashboard']
check('Grafana provisioned dashboard',len(dashboard['panels'])>=8)
for i,query in enumerate(['{project="web-qc-sanpham",job="nginx"} | json','{project="web-qc-sanpham",job="nginx"} | json | status >= 400','{project="web-qc-sanpham",job="wordpress"} | json | event=~"login_success|login_failed|product_saved|product_deleted"'],1):
    r=getjson(local('LOKI_PORT',3101)+'/loki/api/v1/query_range',{'query':query,'limit':10,'since':'1h'})
    rows=sum(len(s['values']) for s in r.get('data',{}).get('result',[]))
    check('LogQL '+str(i)+' has real rows',r.get('status')=='success' and rows>0,{'rows':rows})
    (out/f'logql-{i}.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
containers=json.loads(subprocess.check_output(['docker','inspect',*dc('ps','-q').split()],text=True))
byservice={c['Config']['Labels']['com.docker.compose.service']:c for c in containers}
for name in ['nginx','grafana','prometheus','loki','nginx-exporter','mysql-exporter']:
    check(name+' configured non-root',byservice[name]['Config']['User'].split(':')[0] not in ('','0','root'))
check('MySQL has no published ports',not any(byservice['mysql']['HostConfig']['PortBindings'].values()))
check('Nginx root filesystem read-only',byservice['nginx']['HostConfig']['ReadonlyRootfs'])
for name in ['grafana','phpmyadmin','prometheus','loki']:
    bindings=byservice[name]['HostConfig']['PortBindings']
    check(name+' host bindings only loopback',all(b['HostIp']=='127.0.0.1' for v in bindings.values() for b in (v or [])))
passwords=[v for k,v in env.items() if 'PASSWORD' in k]
check('Strong unique generated passwords',all(len(v)>=32 for v in passwords) and len(set(passwords))==len(passwords))
check('.env owner-only permissions',os.stat(root/'.env').st_mode & 0o077==0)
networks=json.loads(subprocess.check_output(['docker','network','inspect','project_backend'],text=True))
check('Database network internal',networks[0]['Internal'])
check('Only one Compose file',sorted(p.name for p in root.glob('*compose*.y*ml'))==['docker-compose.yml'])
check('No orchestration wrapper',not (root/'scripts/dc.sh').exists())
bootstrap={}
for job in ['init-logs','database-init','wordpress-init']:
    state=json.loads(subprocess.check_output(['docker','inspect','project-'+job+'-1'],text=True))[0]['State']
    bootstrap[job]={'status':state['Status'],'exit_code':state['ExitCode']}
check('Single Compose bootstraps logs DB and website',all(v['status']=='exited' and v['exit_code']==0 for v in bootstrap.values()),bootstrap)
summary={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':sum(x['passed'] for x in results),'total':len(results),'checks':results}
(out/'checks.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
raise SystemExit(0 if all(x['passed'] for x in results) else 1)
