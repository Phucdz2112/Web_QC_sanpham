/* Lab-only browser acceptance test. npm install --no-save playwright */
const {chromium}=require('playwright');
const fs=require('fs'),path=require('path'),assert=require('assert');
const root=path.resolve(__dirname,'..');
const localEnv=path.join(root,'.env');
if(fs.existsSync(localEnv)) for(const line of fs.readFileSync(localEnv,'utf8').split(/\r?\n/)){
 const i=line.indexOf('=');if(i>0&&!line.startsWith('#')&&!process.env[line.slice(0,i)])process.env[line.slice(0,i)]=line.slice(i+1);
}
const env=process.env,site=env.SITE_URL;
const out=path.resolve(env.EVIDENCE_DIR||path.join(root,'..','web-qc-artifacts','evidence'));
if(out===root||out.startsWith(root+path.sep))throw Error('Evidence must stay outside repository');
fs.mkdirSync(out,{recursive:true});
const pma=env.PMA_URL||'http://127.0.0.1:5432',grafana=env.GRAFANA_URL||'http://127.0.0.1:3002',prom=env.PROMETHEUS_URL||'http://127.0.0.1:9091';
const passed=[];const pass=s=>{passed.push(s);console.log('PASS '+s)};
let browser,page;
(async()=>{
 browser=await chromium.launch({headless:true,...(env.BROWSER_EXECUTABLE?{executablePath:env.BROWSER_EXECUTABLE}:{}),args:['--disable-dev-shm-usage']});
 const context=await browser.newContext({viewport:{width:1440,height:1000},locale:'vi-VN'});context.setDefaultTimeout(60000);
 page=await context.newPage();
 const shot=async(name,p=page)=>p.screenshot({path:path.join(out,name),fullPage:false});
 await page.goto(site,{waitUntil:'networkidle'});assert((await page.locator('.product').count())>=6);await shot('01-website.png');pass('Public product catalog');
 await page.locator('.product h3 a').first().click();await page.locator('.detail-grid').waitFor();await shot('02-product-detail.png');pass('Product detail');
 const mobile=await browser.newContext({viewport:{width:390,height:844},isMobile:true});const m=await mobile.newPage();await m.goto(site,{waitUntil:'networkidle'});assert(await m.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await m.screenshot({path:path.join(out,'03-mobile.png'),fullPage:true});await mobile.close();pass('Mobile layout');
 await page.goto(site+'/wp-login.php');await page.locator('#user_login').fill('DTC255180105');await page.locator('#user_pass').fill(env.WP_ADMIN_PASSWORD);await page.locator('#wp-submit').click();await page.waitForURL('**/wp-admin/**');pass('WordPress authentication');
 await page.goto(site+'/wp-admin/edit.php?post_type=product');await shot('04-wordpress-admin.png');
 await page.goto(site+'/wp-admin/post-new.php?post_type=product');const stamp=Date.now().toString();await page.locator('#title').fill('San pham kiem thu '+stamp);
 if(await page.locator('#content-html').isVisible())await page.locator('#content-html').click();await page.locator('#content').fill('Noi dung kiem thu CRUD tu trinh duyet.');
 const price=page.locator('[name=phuc_price]');await price.fill('-1');assert(!(await price.evaluate(e=>e.checkValidity())));await price.fill('123000');
 await page.locator('#publish').click();
 try{await page.waitForURL('**/post.php?**',{timeout:15000})}catch(e){if(!page.url().includes('/post-new.php'))throw e;await page.locator('#publish:not([disabled])').click();await page.waitForURL('**/post.php?**')}
 const productId=new URL(page.url()).searchParams.get('post');assert(productId);assert((await page.locator('#title').inputValue())==='San pham kiem thu '+stamp);pass('Create product and validate price');
 await page.locator('#title').fill('San pham da sua '+stamp);await price.fill('456000');await page.locator('#publish').click();await page.waitForLoadState('networkidle');await page.reload();assert((await page.locator('#title').inputValue())==='San pham da sua '+stamp);assert((await page.locator('[name=phuc_price]').inputValue())==='456000');await shot('05-product-edit.png');pass('Update persisted after reload');
 await page.locator('#delete-action a').click();await page.waitForLoadState('networkidle');await page.goto(site+'/wp-admin/edit.php?post_type=product&post_status=trash');const row=page.locator('#post-'+productId);await row.hover();page.on('dialog',d=>d.accept());await row.locator('a.submitdelete').click();await page.waitForLoadState('networkidle');assert((await page.locator('#post-'+productId).count())===0);pass('Delete test product permanently');
 await page.goto(site+'/not-found-demo-'+stamp);pass('Generate real HTTP error event');
 const db=await context.newPage();await db.goto(pma,{waitUntil:'networkidle'});await db.locator('#input_username').fill('wordpress');await db.locator('#input_password').fill(env.WORDPRESS_DB_PASSWORD);await db.locator('#input_go').click();await db.locator('#pma_navigation').waitFor();await db.goto(pma+'/index.php?route=/database/structure&db=wordpress',{waitUntil:'networkidle'});await db.getByText('wp_posts',{exact:true}).first().waitFor();await shot('06-phpmyadmin.png',db);pass('phpMyAdmin authenticated database access');
 const target=await context.newPage();await target.goto(prom+'/targets');await target.getByText('mysql-exporter:9104',{exact:false}).first().waitFor();await shot('07-prometheus-targets.png',target);pass('Prometheus targets rendered');
 const g=await context.newPage();await g.goto(grafana+'/login');await g.locator('input[name=user]').fill('DTC255180105');await g.locator('input[name=password]').fill(env.GRAFANA_ADMIN_PASSWORD);await g.getByRole('button',{name:'Log in',exact:true}).click();await g.waitForURL(u=>!u.pathname.includes('/login'));
 const dashboardResponse=g.waitForResponse(r=>r.url().includes('/api/ds/query')&&r.request().method()==='POST',{timeout:60000});
 await g.goto(grafana+'/d/web-qc-system');await g.getByText('Nginx availability',{exact:true}).waitFor();const dr=await dashboardResponse;assert(dr.ok());await g.waitForTimeout(2000);await shot('08-grafana-dashboard.png',g);pass('Grafana dashboard rendered with query response');
 const queries=['{project="web-qc-sanpham",job="nginx"} | json','{project="web-qc-sanpham",job="nginx"} | json | status >= 400','{project="web-qc-sanpham",job="wordpress"} | json | event=~"login_success|login_failed|product_saved|product_deleted"'];
 for(let i=0;i<queries.length;i++){
  const state={A:{datasource:'loki',queries:[{refId:'A',expr:queries[i],queryType:'range',datasource:{type:'loki',uid:'loki'}}],range:{from:'now-1h',to:'now'}}};
  const response=g.waitForResponse(r=>r.url().includes('/api/ds/query')&&r.request().method()==='POST'&&r.request().postData()?.includes('loki'),{timeout:60000});
  await g.goto(grafana+'/explore?schemaVersion=1&panes='+encodeURIComponent(JSON.stringify(state))+'&orgId=1');
  const r=await response;assert(r.ok());const data=await r.json();assert(Object.values(data.results||{}).some(result=>(result.frames||[]).some(f=>(f.data?.values||[]).some(v=>v.length>0))));
  await g.waitForTimeout(1800);assert(!(await g.locator('body').innerText()).includes('No logs found'));await shot('09-logql-'+(i+1)+'.png',g);pass('LogQL '+(i+1)+' rendered real rows');
 }
 const git=await context.newPage();await git.setViewportSize({width:1440,height:720});await git.goto('https://github.com/Phucdz2112/Web_QC_sanpham/commits/main/',{waitUntil:'domcontentloaded'});await git.getByText('feat: integrate Loki Promtail LogQL and system acceptance checks',{exact:false}).first().waitFor();await shot('10-github.png',git);pass('GitHub commit evidence');
 fs.writeFileSync(path.join(out,'browser-results.json'),JSON.stringify({passed,count:passed.length},null,2));await browser.close();
})().catch(async e=>{console.error(e);if(page)await page.screenshot({path:path.join(out,'browser-failure.png')}).catch(()=>{});if(browser)await browser.close();process.exit(1)});
