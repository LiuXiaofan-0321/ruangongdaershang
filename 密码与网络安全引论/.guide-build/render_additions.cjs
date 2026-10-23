const fs=require('fs'),path=require('path');
const {chromium}=require('playwright');
(async()=>{
 const dir=__dirname,raw=fs.readFileSync(path.join(dir,'additions.raw.html'),'utf8');
 const old=fs.readFileSync(path.join(dir,'original.html'),'utf8'),style=old.match(/<style[^>]*>([\s\S]*?)<\/style>/)[1];
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 page.on('pageerror',e=>console.log('PAGE ERROR',e.message));
 await page.setContent('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><style>'+style+'</style></head><body><main class="main"><div id="render-root">'+raw+'</div></main></body></html>');
 await page.evaluate(()=>{window.MathJax={startup:{typeset:false},tex:{inlineMath:[['\\(','\\)']],displayMath:[['\\[','\\]']]},svg:{fontCache:'none'}};});
 const libraries=[['mathjax','https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-svg.js'],['mermaid','https://cdn.jsdelivr.net/npm/mermaid@11.17.2/dist/mermaid.min.js'],['highlight','https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/highlight.min.js']];
 for(const [name,url] of libraries){await page.addScriptTag({url,timeout:45000});console.log('loaded',name);}
 const result=await page.evaluate(async()=>{
   await MathJax.startup.promise;
   const root=document.getElementById('render-root');
   await MathJax.typesetPromise([root]);
   const mathErrors=[...root.querySelectorAll('[data-mml-node="merror"]')].map(x=>x.textContent);
   mermaid.initialize({startOnLoad:false,theme:'default',securityLevel:'strict',flowchart:{htmlLabels:false}});
   let diagrams=0;
   for(const pre of root.querySelectorAll('.mermaid')){
      const {svg}=await mermaid.render('new-diagram-'+diagrams,pre.textContent);
      const box=pre.closest('.diagram');box.querySelector('.diagram-render').innerHTML=svg;box.classList.add('has-svg');diagrams++;
   }
   root.querySelectorAll('pre code').forEach(x=>hljs.highlightElement(x));
   return {html:root.innerHTML,math:root.querySelectorAll('mjx-container').length,mathErrors,diagrams};
 });
 if(result.mathErrors.length)throw new Error(JSON.stringify(result.mathErrors));
 fs.writeFileSync(path.join(dir,'additions.rendered.html'),result.html,'utf8');
 console.log(JSON.stringify({math:result.math,diagrams:result.diagrams,bytes:Buffer.byteLength(result.html)}));
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1);});
