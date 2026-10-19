const fs=require('fs'),path=require('path'),{pathToFileURL}=require('url'),{chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});const page=await browser.newPage({viewport:{width:1440,height:1000}});await page.route(/^https?:/,r=>r.abort());
 await page.goto(pathToFileURL(path.join(__dirname,'..','密码学_第二三讲_深度学习指南.html')).href);await page.locator('#a02-q3').waitFor();
 await page.addStyleTag({content:'html{scroll-behavior:auto!important}.sidebar{transition:none!important}'});
 const shot=async(id,file)=>{await page.evaluate(id=>document.getElementById(id).scrollIntoView({behavior:'instant',block:'start'}),id);await page.screenshot({path:path.join(__dirname,file),animations:'disabled'});};
 await shot('t08','sm4-table.png');await shot('a02','hkdf-light.png');
 await page.locator('#theme-btn').click();await shot('t08','sm4-dark.png');
 await page.setViewportSize({width:390,height:844});await shot('m01','mobile-cbc-stable.png');
 console.log(await page.evaluate(()=>({width:innerWidth,docWidth:document.documentElement.scrollWidth,sidebarX:document.getElementById('sidebar').getBoundingClientRect().x,sidebarClass:document.getElementById('sidebar').className})));
 await page.locator('#theme-btn').click();await shot('zuc-iv-lab','mobile-iv.png');
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
