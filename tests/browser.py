#!/usr/bin/env python3
"""Lab-only browser acceptance test; creates and deletes one test product."""
import json, os, re, time, urllib.parse
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
root=Path(__file__).resolve().parents[1]
out=Path(os.environ.get('EVIDENCE_DIR',str(root.parent/'web-qc-artifacts/evidence'))).resolve()
if out==root or root in out.parents: raise SystemExit('Evidence must stay outside repository')
out.mkdir(parents=True,exist_ok=True)
env=dict(line.split('=',1) for line in (root/'.env').read_text().splitlines() if line and not line.startswith('#'))
site=env['SITE_URL']; stamp=str(int(time.time())); checks=[]
def passed(name): checks.append(name); print('PASS '+name,flush=True)
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=['--disable-dev-shm-usage'])
    context=browser.new_context(viewport={'width':1440,'height':1000},locale='vi-VN')
    page=context.new_page()
    page.goto(site,wait_until='networkidle'); assert page.locator('.product').count()>=6
    page.screenshot(path=str(out/'01-website.png'),full_page=False); passed('At least six public products')
    page.locator('.product h3 a').first.click(); expect(page.locator('.detail-grid')).to_be_visible()
    page.screenshot(path=str(out/'02-product-detail.png'),full_page=False); passed('Product detail')
    mobile=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,device_scale_factor=1)
    m=mobile.new_page(); m.goto(site,wait_until='networkidle')
    assert m.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    m.screenshot(path=str(out/'03-mobile.png'),full_page=True); mobile.close(); passed('Mobile has no horizontal overflow')
    page.goto(site+'/wp-login.php'); page.locator('#user_login').fill('DTC255180105'); page.locator('#user_pass').fill(env['WP_ADMIN_PASSWORD']); page.locator('#wp-submit').click(); page.wait_for_url('**/wp-admin/**')
    passed('WordPress login')
    page.goto(site+'/wp-admin/edit.php?post_type=product'); page.screenshot(path=str(out/'04-wordpress-admin.png'),full_page=True)
    page.goto(site+'/wp-admin/post-new.php?post_type=product'); page.locator('#title').fill('San pham kiem thu '+stamp)
    if page.locator('#content-html').is_visible(): page.locator('#content-html').click()
    page.locator('#content').fill('Noi dung kiem thu CRUD tu trinh duyet.')
    price=page.locator('[name=phuc_price]'); price.fill('-1'); assert not price.evaluate('(e)=>e.checkValidity()'); price.fill('123000')
    page.locator('#publish').click(); page.wait_for_url('**/post.php?**'); product_id=urllib.parse.parse_qs(urllib.parse.urlparse(page.url).query)['post'][0]
    expect(page.locator('#title')).to_have_value('San pham kiem thu '+stamp); passed('Create product and price validation')
    page.locator('#title').fill('San pham da sua '+stamp); price.fill('456000'); page.locator('#publish').click(); page.wait_for_load_state('networkidle')
    page.reload(); expect(page.locator('#title')).to_have_value('San pham da sua '+stamp); expect(page.locator('[name=phuc_price]')).to_have_value('456000')
    page.screenshot(path=str(out/'05-product-edit.png'),full_page=True); passed('Update persists after reload')
    page.locator('#delete-action a').click(); page.wait_for_load_state('networkidle')
    page.goto(site+'/wp-admin/edit.php?post_type=product&post_status=trash')
    row=page.locator('#post-'+product_id); row.hover(); page.on('dialog',lambda dialog:dialog.accept()); row.locator('a.submitdelete').click(); page.wait_for_load_state('networkidle'); expect(page.locator('#post-'+product_id)).to_have_count(0); passed('Delete test product permanently')
    page.goto(site+'/not-found-demo-'+stamp); passed('Generate real HTTP error log')
    db=context.new_page(); db.goto('http://127.0.0.1:5432',wait_until='networkidle'); db.locator('#input_username').fill('wordpress'); db.locator('#input_password').fill(env['WORDPRESS_DB_PASSWORD']); db.locator('#input_go').click(); db.wait_for_load_state('networkidle'); expect(db.locator('#pma_navigation')).to_be_visible(); db.goto('http://127.0.0.1:5432/index.php?route=/database/structure&db=wordpress',wait_until='networkidle'); expect(db.locator('body')).to_contain_text('wp_posts'); db.screenshot(path=str(out/'06-phpmyadmin.png'),full_page=True); passed('phpMyAdmin authenticated database access')
    prom=context.new_page(); prom.goto('http://127.0.0.1:9091/targets',wait_until='networkidle'); expect(prom.locator('body')).to_contain_text('mysql'); prom.screenshot(path=str(out/'07-prometheus-targets.png'),full_page=True)
    g=context.new_page(); g.goto('http://127.0.0.1:3002/login',wait_until='networkidle'); g.locator('input[name=user]').fill('DTC255180105'); g.locator('input[name=password]').fill(env['GRAFANA_ADMIN_PASSWORD']); g.get_by_role('button',name='Log in',exact=True).click(); g.wait_for_url(re.compile(r'.*(?<!/login)$'))
    g.goto('http://127.0.0.1:3002/d/web-qc-system',wait_until='networkidle'); expect(g.get_by_text('Nginx availability',exact=True)).to_be_visible(); g.wait_for_timeout(5000); g.screenshot(path=str(out/'08-grafana-dashboard.png'),full_page=False); passed('Grafana dashboard rendered')
    queries=['{project="web-qc-sanpham",job="nginx"} | json','{project="web-qc-sanpham",job="nginx"} | json | status >= 400','{project="web-qc-sanpham",job="wordpress"} | json | event=~"login_success|login_failed|product_saved|product_deleted"']
    for i,q in enumerate(queries,1):
        state={'A':{'datasource':'loki','queries':[{'refId':'A','expr':q,'queryType':'range','datasource':{'type':'loki','uid':'loki'}}],'range':{'from':'now-1h','to':'now'}}}
        g.goto('http://127.0.0.1:3002/explore?schemaVersion=1&panes='+urllib.parse.quote(json.dumps(state))+'&orgId=1',wait_until='networkidle'); g.wait_for_timeout(5000)
        expect(g.locator('body')).not_to_contain_text('No logs found')
        g.screenshot(path=str(out/f'09-logql-{i}.png'),full_page=True)
    passed('Three Grafana Explore queries captured')
    browser.close()
(out/'browser-results.json').write_text(json.dumps({'passed':checks,'count':len(checks)},ensure_ascii=False,indent=2))
