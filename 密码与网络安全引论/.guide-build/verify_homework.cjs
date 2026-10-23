const fs=require('fs'),path=require('path'),{pathToFileURL}=require('url'),{chromium}=require('playwright');
const assert=(v,m)=>{if(!v)throw new Error(m);};
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route(/^https?:/,r=>r.abort());
 await page.goto(pathToFileURL(path.join(__dirname,'..','密码学_深度学习指南.html')).href);await page.locator('#a02-q3').waitFor();
 await page.addStyleTag({content:'html{scroll-behavior:auto!important}.sidebar{transition:none!important}'});
 assert(await page.locator('#homework-priority .hw-card').count()===8,'8 homework cards');
 assert(await page.locator('.hw-focus-note:not(.pre)').count()===19,'19 exact required sections');
 assert(await page.locator('.hw-focus-note.pre').count()===7,'7 prerequisites');
 assert(await page.locator('.quiz-card').count()===102,'original quizzes retained');
 assert(await page.locator('.cloze').count()===125,'original progress total retained');
 assert(await page.locator('.nav-link[data-homework-level="direct"]').count()===11,'chapter required badges');
 const manifest=JSON.parse(fs.readFileSync(path.join(__dirname,'homework-manifest.json'),'utf8'));
 for(const ex of manifest.exercises){
   const link=page.locator('#homework-'+ex.id+' a.btn');await link.click();
   const target=page.locator('#'+ex.answer_id);assert(await target.count()===1,'answer target '+ex.id);
   if(await target.evaluate(e=>e.tagName)==='DETAILS')assert(await target.evaluate(e=>e.open),'answer autoopens '+ex.id);
 }
 await page.evaluate(()=>scrollTo(0,0));
 await page.locator('#hw-nav-toggle').click();assert(await page.locator('.nav-link[data-nav]:visible').count()===15,'relevant chapters filter');
 await page.locator('#nav-search').fill('HKDF');assert(await page.locator('.nav-link[data-nav]:visible').count()===1,'filter plus search');
 await page.locator('#nav-search').fill('ZUC');assert(await page.locator('.nav-link[data-nav]:visible').count()===0,'out-of-homework search empty');assert(await page.locator('#nav-no-results').isVisible(),'no results accessible');
 await page.locator('#hw-nav-toggle').click();assert(await page.locator('.nav-link[data-nav]:visible').count()>0,'restore respects current search');await page.locator('#nav-search').fill('');assert(await page.locator('.nav-link[data-nav]:visible').count()===35,'all chapters and welcome restored');
 await page.locator('#t06-q1 [data-option="1"]').click();assert(await page.locator('#accuracy').innerText()==='100%','quiz still works');
 await page.locator('#t06 .cloze').first().click();await page.locator('#t06 .master-btn').first().click();assert(await page.locator('#master-count').innerText()==='1','mastery still works');
 await page.evaluate(()=>document.getElementById('homework-priority').scrollIntoView({behavior:'instant'}));await page.screenshot({path:path.join(__dirname,'homework-desktop.png'),animations:'disabled'});
 await page.locator('#theme-btn').click();await page.evaluate(()=>document.getElementById('hw-t06-h1').scrollIntoView({behavior:'instant'}));await page.screenshot({path:path.join(__dirname,'homework-dark-note.png'),animations:'disabled'});
 await page.setViewportSize({width:390,height:844});await page.evaluate(()=>document.getElementById('homework-e4-1').scrollIntoView({behavior:'instant'}));assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'mobile no horizontal page overflow');await page.screenshot({path:path.join(__dirname,'homework-mobile.png'),animations:'disabled'});
 await page.locator('#menu-btn').click();await page.locator('.nav-list > a[href="#homework-priority"]').click();assert(!(await page.locator('#sidebar').evaluate(e=>e.classList.contains('is-open'))),'custom mobile navigation closes drawer');
 assert(errors.length===0,'no JS errors '+JSON.stringify(errors));
 console.log(JSON.stringify({cards:8,requiredSections:19,prerequisites:7,links:'all 8 answer jumps passed',filter:'15 relevant chapters, combined search and restore passed',originalQuizAndMastery:'passed',mobile:'390px passed',errors},null,2));
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1);});
