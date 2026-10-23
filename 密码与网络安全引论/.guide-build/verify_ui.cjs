const path=require('path'),{pathToFileURL}=require('url'),{chromium}=require('playwright');
const assert=(v,m)=>{if(!v)throw new Error(m)};
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const page=await browser.newPage({viewport:{width:1440,height:1050}});const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.route(/^https?:/,r=>r.abort());
 await page.goto(pathToFileURL(path.join(__dirname,'..','密码学_深度学习指南.html')).href);await page.locator('#a02-q3').waitFor();
 await page.addStyleTag({content:'html{scroll-behavior:auto!important}.sidebar{transition:none!important}'});
 const shot=async(id,name)=>{await page.evaluate(id=>document.getElementById(id).scrollIntoView({behavior:'instant',block:'start'}),id);await page.screenshot({path:path.join(__dirname,'ui-'+name+'.png'),animations:'disabled'});};
 await shot('welcome','desktop-welcome');
 assert(await page.locator('.lecture-route').count()===4,'4 lecture entries');
 assert(await page.locator('#overview-btn').isVisible(),'overview above fold within hero');
 await page.locator('#overview-btn').click();assert(await page.locator('#overview-body .overview-item').count()===34,'overview');await page.locator('#overview-dialog [data-close-dialog]').click();
 await page.locator('.welcome-more > summary').click();assert(await page.locator('.welcome-more').evaluate(e=>e.open),'extended route opens');await page.locator('.welcome-more > summary').click();
 await shot('homework-priority','desktop-homework');await shot('hw-t06-h1','desktop-reading');
 await page.locator('#theme-btn').click();await shot('welcome','dark-welcome');await shot('hw-t06-h1','dark-reading');
 await page.locator('#t06-q1 [data-option="0"]').click();assert(await page.locator('#t06-q1 .quiz-option.wrong').count()===1,'wrong still red');assert(await page.locator('#t06-q1 .quiz-option.correct').count()===1,'correct still green');await shot('t06-q1','dark-quiz');
 const widths=[1440,1024,768,390,360];
 for(const width of widths){await page.setViewportSize({width,height:width<600?844:1000});await page.evaluate(()=>document.getElementById('welcome').scrollIntoView({behavior:'instant'}));assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'no page overflow at '+width);const top=await page.locator('.topbar').evaluate(el=>({scroll:el.scrollWidth,client:el.clientWidth}));assert(top.scroll<=top.client+1,'topbar fit '+width);}
 await page.setViewportSize({width:390,height:844});await shot('welcome','mobile-welcome');await shot('hw-t06-h1','mobile-reading');await page.locator('#theme-btn').click();await shot('homework-e4-1','mobile-homework');
 await page.locator('#menu-btn').click();await page.screenshot({path:path.join(__dirname,'ui-mobile-menu.png'),animations:'disabled'});await page.locator('#hw-nav-toggle').click();assert(await page.locator('.nav-link[data-nav]:visible').count()===15,'mobile filtered navigation');await page.locator('#menu-close').click();
 assert(!errors.length,'browser errors '+JSON.stringify(errors));
 console.log(JSON.stringify({offline:true,widths,overflow:'none',lectures:4,originalModules:34,overview:'passed',homeworkFilter:'passed',quizFeedback:'passed',errors},null,2));await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
