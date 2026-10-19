/* Learning interactions. State stays in memory; JSON export/import is explicit. */
(function(){
'use strict';
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>Array.from(r.querySelectorAll(s));
const concepts=$$('.cloze');
const conceptIds=new Set(concepts.map(x=>x.dataset.concept));
const questionById=new Map(DATA.quizzes.map(q=>[q.id,q]));
let state={version:1,guide:'crypto-lectures-2-3-v1',mastered:[],revealed:[],answers:{},theme:'light'};
let drafts={};
let toastTimer;
function toast(text){const n=$('#toast');n.textContent=text;n.hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>n.hidden=true,4000);}
function node(tag,cls,text){const x=document.createElement(tag);if(cls)x.className=cls;if(text!==undefined)x.textContent=text;return x;}
function button(text,cls,fn){const b=node('button',cls||'btn',text);b.type='button';b.addEventListener('click',fn);return b;}
function setHtml(n,html){n.innerHTML=html;return n;}
function correctSet(q){return q.options.map((o,i)=>o.correct?i:-1).filter(i=>i>=0);}
function sameSet(a,b){return a.length===b.length&&a.every(x=>b.includes(x));}
function makeDraft(q){return {selected:[],touched:[],submitted:false};}
function ensureDraft(q){if(!drafts[q.id]){const a=state.answers[q.id];drafts[q.id]=a?{selected:[...a.selected],touched:[...a.selected],submitted:true}:makeDraft(q);}return drafts[q.id];}
function initConcepts(){concepts.forEach(c=>{const id=c.dataset.concept;c.setAttribute('aria-label','概念回忆：点击显示或隐藏答案');const span=c.querySelector('span');span.setAttribute('aria-hidden','true');const b=button('确认掌握','master-btn',()=>{const has=state.mastered.includes(id);state.mastered=has?state.mastered.filter(x=>x!==id):[...state.mastered,id];renderConcept(c,b);updateStats();});b.dataset.masterFor=id;b.setAttribute('aria-pressed','false');b.hidden=true;c.after(b);c.addEventListener('click',()=>{const revealed=state.revealed.includes(id);state.revealed=revealed?state.revealed.filter(x=>x!==id):[...state.revealed,id];renderConcept(c,b);});renderConcept(c,b);});}
function renderConcept(c,b){const id=c.dataset.concept;const open=state.revealed.includes(id), mastered=state.mastered.includes(id);c.setAttribute('aria-expanded',String(open));c.dataset.mastered=String(mastered);c.querySelector('span').setAttribute('aria-hidden',String(!open));b.hidden=!open;b.setAttribute('aria-pressed',String(mastered));b.textContent=mastered?'已掌握 · 可撤销':'确认掌握';b.setAttribute('aria-label',mastered?'撤销该概念的掌握标记':'我能独立回忆这个概念，标记已掌握');}
function resetConceptUI(){concepts.forEach(c=>renderConcept(c,$(`[data-master-for="${c.dataset.concept}"]`)));}
function renderQuestion(q,card){
 const d=ensureDraft(q),first=state.answers[q.id];card.replaceChildren();card.className='quiz-card';card.id=q.id;card.setAttribute('aria-labelledby',q.id+'-title');
 const local=DATA.quizzes.filter(x=>x.module===q.module).findIndex(x=>x.id===q.id)+1;
 card.append(node('div','quiz-meta',`第 ${local} 题 / 3　${q.type==='multi'?'多选 · 每次点击即反馈，提交后整题计分':'单选 · 点击即反馈并记录首答'}`));
 const title=setHtml(node('div','quiz-question'),q.question);title.id=q.id+'-title';card.append(title);
 const group=node('div','quiz-options');group.setAttribute('role','group');group.setAttribute('aria-label',q.type==='multi'?'请选择所有正确项':'选择一个答案');card.append(group);
 q.options.forEach((o,i)=>{
  const selected=d.selected.includes(i),touched=d.touched.includes(i);
  const b=button('','quiz-option',()=>selectOption(q,i));b.dataset.option=String(i);b.setAttribute('aria-pressed',String(selected));b.disabled=d.submitted;
  const letter=node('span','option-letter',String.fromCharCode(65+i));b.append(letter);const text=setHtml(node('span','option-text'),o.text);b.append(text);
  const show=d.submitted||touched;
  if(show&&o.correct)b.classList.add('correct');else if(show&&selected&&!o.correct)b.classList.add('wrong');
  if(selected)b.classList.add('selected');
  if(show){const label=o.correct?'✓ 正确项':'✗ 错误项';text.append(node('span','option-verdict',label+(selected?' · 已选':'')));}
  group.append(b);
  if(q.type==='multi'&&touched&&!d.submitted){const f=setHtml(node('div','option-feedback'),o.reason);f.setAttribute('role','status');group.append(f);}
 });
 const actions=node('div','quiz-actions');card.append(actions);
 if(q.type==='multi'&&!d.submitted){const submit=button('提交本题','btn btn-primary',()=>submitQuestion(q));submit.disabled=d.selected.length===0;actions.append(submit);actions.append(node('span','quiz-score','仅“全选对且无错选”记为正确；选项反馈是教学提示。'));}
 if(d.submitted){
  const pass=sameSet(d.selected,correctSet(q));const feedback=node('div','quiz-feedback '+(pass?'pass':'fail'));feedback.setAttribute('role','status');feedback.append(node('strong','',pass?'✓ 本次作答正确':'✗ 本次作答尚未正确'));
  feedback.append(setHtml(node('p',''),`正确答案：${correctSet(q).map(i=>String.fromCharCode(65+i)).join('、')}。${q.explanation}`));
  const reasons=node('div','feedback-reasons');q.options.forEach((o,i)=>reasons.append(setHtml(node('p',''),`<strong>${String.fromCharCode(65+i)} ${o.correct?'正确':'错误'}：</strong>${o.reason}`)));feedback.append(reasons);feedback.append(node('p','caption',q.source));card.append(feedback);
  actions.append(button('再练一次（不改首答）','btn',()=>{drafts[q.id]=makeDraft(q);renderQuestion(q,card);toast('已开始练习重做，首答统计保持不变。');}));
 }
 if(first)actions.append(node('span','quiz-score',`首答已记录：${first.correct?'正确':'错误'}。重做不会刷高首答正确率。`));
}
function selectOption(q,i){const d=ensureDraft(q);if(d.submitted)return;if(q.type==='single'){d.selected=[i];d.touched=[i];submitQuestion(q);}else{d.selected=d.selected.includes(i)?d.selected.filter(x=>x!==i):[...d.selected,i];if(!d.touched.includes(i))d.touched.push(i);renderQuestion(q,document.getElementById(q.id));const active=$(`[data-option="${i}"]`,document.getElementById(q.id));if(active)active.focus({preventScroll:true});}}
function submitQuestion(q){const d=ensureDraft(q);if(d.submitted||!d.selected.length)return;d.submitted=true;const pass=sameSet(d.selected,correctSet(q));if(!state.answers[q.id])state.answers[q.id]={selected:[...d.selected],correct:pass};renderQuestion(q,document.getElementById(q.id));updateStats();}
function initQuizzes(){DATA.modules.forEach(m=>{const zone=$(`[data-quiz-module="${m.id}"]`);if(!zone)return;zone.replaceChildren();zone.append(node('h3','','交互式检验区'));zone.append(node('p','caption','先闭卷回忆，再作答。绿色表示正确项，红色表示误选项；每个选项都有排错理由。'));DATA.quizzes.filter(q=>q.module===m.id).forEach(q=>{const card=node('div','quiz-card');zone.append(card);renderQuestion(q,card);});});}
function updateStats(){const answered=Object.keys(state.answers).length;const correct=Object.values(state.answers).filter(x=>x.correct).length;const total=concepts.length;
 $('#master-count').textContent=state.mastered.length;$('#master-total').textContent='/ '+total;$('#accuracy').textContent=answered?Math.round(correct/answered*100)+'%':'—';$('#quiz-count').textContent=`${answered} / ${DATA.quizzes.length} 题已答`;$('#master-meter').style.width=(state.mastered.length/total*100)+'%';$('#quiz-meter').style.width=(answered/DATA.quizzes.length*100)+'%';
 $('#global-progress').setAttribute('aria-valuenow',String(state.mastered.length));$('#global-progress').setAttribute('aria-valuemax',String(total));$('#global-progress').setAttribute('aria-valuetext',`已掌握 ${state.mastered.length} 个概念，共 ${total} 个`);
 DATA.modules.forEach(m=>{const ids=$$('.cloze',document.getElementById(m.id)).map(c=>c.dataset.concept);const done=ids.length&&ids.every(id=>state.mastered.includes(id));const dot=$(`[data-nav="${m.id}"] .nav-dot`);if(dot){dot.classList.toggle('done',Boolean(done));dot.title=done?'本章概念均已确认掌握':'本章尚有未确认掌握的概念';}});
}
function setTheme(t){state.theme=t;document.documentElement.dataset.theme=t;$('#theme-btn').textContent=t==='dark'?'☀':'☾';$('#theme-btn').setAttribute('aria-label',t==='dark'?'切换浅色模式':'切换深色模式');$('#theme-btn').title=t==='dark'?'切换浅色模式':'切换深色模式';}
function toggleMenu(open){$('#sidebar').classList.toggle('is-open',open);$('#menu-overlay').hidden=!open;$('#menu-btn').setAttribute('aria-expanded',String(open));if(open){$('#nav-search').focus();}else{$('#menu-btn').focus({preventScroll:true});}}
function openDialog(id){const d=document.getElementById(id);if(!d.open)d.showModal();}
function overview(){const area=$('#overview-body');area.replaceChildren();area.append(node('p','caption','掌握数来自你的主动确认，不等同于看过答案。首答正确率只统计已提交题目；多选采用即时提示练习，因此不代表闭卷考试成绩。'));
 DATA.modules.forEach(m=>{const count=$$('.cloze',document.getElementById(m.id)).filter(c=>state.mastered.includes(c.dataset.concept)).length;const total=$$('.cloze',document.getElementById(m.id)).length;const qs=DATA.quizzes.filter(q=>q.module===m.id);const done=qs.filter(q=>state.answers[q.id]);const right=done.filter(q=>state.answers[q.id].correct);const row=node('div','overview-item');const a=node('a','',m.title);a.href='#'+m.id;a.addEventListener('click',()=>$('#overview-dialog').close());row.append(a,node('span','',`概念 ${count}/${total}　首答 ${right.length}/${done.length}`));area.append(row);});openDialog('overview-dialog');}
function exportProgress(){const exportData={...state,exportedAt:new Date().toISOString()};const blob=new Blob([JSON.stringify(exportData,null,2)],{type:'application/json'});const a=node('a');const u=URL.createObjectURL(blob);a.href=u;a.download='密码学学习进度-'+new Date().toISOString().slice(0,10)+'.json';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),2000);toast('学习进度已导出；下次打开指南可导入继续。');}
async function importProgress(file){if(!file)return;try{if(file.size>200000)throw new Error('文件过大，请选择本指南导出的进度JSON。');const obj=JSON.parse(await file.text());if(obj.guide!==state.guide||obj.version!==1)throw new Error('这不是本指南对应版本的学习进度。');if(!Array.isArray(obj.mastered)||!Array.isArray(obj.revealed)||!obj.answers||typeof obj.answers!=='object'||Array.isArray(obj.answers))throw new Error('进度字段不完整。');
 const fresh={version:1,guide:state.guide,theme:obj.theme==='dark'?'dark':'light',mastered:[...new Set(obj.mastered.filter(id=>typeof id==='string'&&conceptIds.has(id)))],revealed:[...new Set(obj.revealed.filter(id=>typeof id==='string'&&conceptIds.has(id)))],answers:{}};
 for(const [id,entry] of Object.entries(obj.answers)){const q=questionById.get(id);if(!q)continue;if(!entry||!Array.isArray(entry.selected))throw new Error('题目进度格式不合法。');const selected=[...new Set(entry.selected)];if(selected.length===0||selected.some(i=>!Number.isInteger(i)||i<0||i>=q.options.length)||(q.type==='single'&&selected.length!==1))throw new Error('题目选择范围不合法。');fresh.answers[id]={selected,correct:sameSet(selected,correctSet(q))};}
 state=fresh;drafts={};setTheme(state.theme);resetConceptUI();initQuizzes();updateStats();toast('进度已导入；正确性已按本指南答案重新核验。');$('#settings-dialog').close();
 }catch(e){toast('导入失败：'+e.message);}finally{$('#progress-file').value='';}}
function resetProgress(){state.mastered=[];state.revealed=[];state.answers={};drafts={};resetConceptUI();initQuizzes();updateStats();$$('details.think[open]').forEach(d=>d.open=false);$('#reset-dialog').close();toast('所有答题、概念显隐与掌握状态已重置。');}
function setupNavigation(){const links=$$('.nav-link[data-nav]');let scheduled=false;function track(){scheduled=false;let current='welcome';for(const m of DATA.modules){const r=document.getElementById(m.id).getBoundingClientRect();if(r.top<190)current=m.id;else break;}links.forEach(a=>{const active=a.dataset.nav===current;a.classList.toggle('active',active);if(active)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current');});const m=DATA.modules.find(x=>x.id===current);$('#current-title').textContent=m?m.title:'从零到会用';}
 window.addEventListener('scroll',()=>{if(!scheduled){requestAnimationFrame(track);scheduled=true;}},{passive:true});track();
 links.forEach(a=>a.addEventListener('click',()=>{if(innerWidth<=900){$('#sidebar').classList.remove('is-open');$('#menu-overlay').hidden=true;$('#menu-btn').setAttribute('aria-expanded','false');}}));
 $('#nav-search').addEventListener('input',e=>{const t=e.target.value.trim().toLowerCase();let hits=0;links.forEach(a=>{const id=a.dataset.nav;const m=DATA.modules.find(x=>x.id===id);const text=m?(m.title+' '+m.summary+' '+m.pages+' '+m.lecture):a.textContent;const show=!t||text.toLowerCase().includes(t);a.hidden=!show;if(show)hits++;});$$('.nav-group').forEach(x=>x.hidden=Boolean(t));$('#nav-no-results').hidden=hits>0;});
}
function setupDialogs(){ $$('[data-close-dialog]').forEach(b=>b.addEventListener('click',()=>document.getElementById(b.dataset.closeDialog).close()));$$('dialog').forEach(d=>d.addEventListener('click',e=>{if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)d.close();}}));}
function init(){initConcepts();initQuizzes();updateStats();setTheme('light');setupNavigation();setupDialogs();
 $('#theme-btn').addEventListener('click',()=>setTheme(state.theme==='light'?'dark':'light'));
 $('#menu-btn').addEventListener('click',()=>toggleMenu(!$('#sidebar').classList.contains('is-open')));$('#menu-close').addEventListener('click',()=>toggleMenu(false));$('#menu-overlay').addEventListener('click',()=>toggleMenu(false));
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&$('#sidebar').classList.contains('is-open'))toggleMenu(false);});
 $('#settings-btn').addEventListener('click',()=>openDialog('settings-dialog'));$('#overview-btn').addEventListener('click',overview);
 $('#export-btn').addEventListener('click',exportProgress);$('#import-btn').addEventListener('click',()=>$('#progress-file').click());$('#progress-file').addEventListener('change',e=>importProgress(e.target.files[0]));
 $('#reset-open-btn').addEventListener('click',()=>{$('#settings-dialog').close();openDialog('reset-dialog');});$('#reset-confirm').addEventListener('click',resetProgress);
 $('#hide-answers').addEventListener('click',()=>{state.revealed=[];resetConceptUI();toast('概念答案已重新遮住，掌握标记和题目成绩保留。');});
 $('#print-btn').addEventListener('click',()=>window.print());
 $$('.table-wrap').forEach(t=>{t.tabIndex=0;t.setAttribute('role','region');t.setAttribute('aria-label','可横向滚动的数据表格');});
 $$('.img-placeholder img').forEach(img=>{function fallback(){if(img.dataset.fallbackDone)return;img.dataset.fallbackDone='true';const n=node('div','missing-image','原图未能显示：'+img.alt);img.hidden=true;img.after(n);}img.addEventListener('error',fallback);if(img.complete&&img.naturalWidth===0)fallback();});
 $$('.diagram pre.mermaid').forEach(pre=>{const box=pre.closest('.diagram');const details=node('details','diagram-source');details.append(node('summary','','查看 Mermaid 重绘源码'));details.append(node('pre','',pre.textContent));box.append(details);});
 window.addEventListener('beforeunload',()=>{});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
