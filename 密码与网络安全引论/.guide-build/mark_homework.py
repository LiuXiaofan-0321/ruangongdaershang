"""Attach source-traceable homework priorities without altering study content or scores."""
from pathlib import Path
import re, html, json, shutil

ROOT=Path(__file__).resolve().parent.parent
TARGET=ROOT/'密码学_深度学习指南.html'

EXERCISES=[
 dict(id='e2-1',lecture='第二讲',page=50,no=1,title='密码体制的主要组成',
      targets=[('b01',5,'五元组与每一项的含义')],prereqs=[],
      answer=('b01','有人说“我的加密可以百分之百解密'),
      ready='能不看书写出明文空间、密文空间、密钥空间、加密算法族、解密算法族，并说明正确性。'),
 dict(id='e2-2',lecture='第二讲',page=50,no=2,title='KEY 加密 CRYPTOGRAPHY',
      targets=[('b05',2,'循环密钥流与逐位模26公式'),('b05',4,'原题12个位置的计算与复验')],
      prereqs=[('b02',1,'A=0到Z=25的字母编码'),('b02',2,'标准余数与模26运算')],
      answer=('b05',4),ready='能独立写出12位密钥流，逐位加密，并用减法模26解回原文；不要直接背密文。'),
 dict(id='e2-3',lecture='第二讲',page=50,no=3,title='用表1.5解密 VTSEGDT',
      targets=[('b04',2,'题目指定的QWERTY式完整密钥表'),('b04',6,'沿输出行逆查，再正向验证')],
      prereqs=[],answer=('b04',6),ready='能确认使用表1.5，在输出行找密文字母，逆查出7个明文字母，再重新加密检查。'),
 dict(id='e4-1',lecture='第四讲',page=55,no=1,title='AES 第一轮轮密钥',
      targets=[('t06',1,'W字递推及RotWord/SubWord/Rcon'),('t06',2,'AES S盒高4位定行、低4位定列'),('t06',4,'原作业矩阵与完整首轮展开')],
      prereqs=[('t05',1,'状态按列装入，每列是一个32位字'),('t02',1,'逐位异或；十六进制按4位一组计算')],
      answer=('t06','求P55矩阵对应的W₄到W₇'),ready='能按列读出W₀到W₃，依次算出特殊字W₄及W₅、W₆、W₇，并按列写回轮密钥矩阵。'),
 dict(id='e4-2',lecture='第四讲',page=56,no=2,title='SM4 轮密钥对称性与一次请求攻击',
      targets=[('t07',5,'同一结构解密、轮密钥逆序的原因'),('t08',4,'逆序相同推出Enc=Dec，再利用加密接口')],
      prereqs=[('t07',1,'四字窗口、32轮与末尾四字反序')],
      answer=('t08','为什么一次选择明文请求'),ready='能完整写出“轮密钥前后对称 ⇒ 加解密相同 ⇒ 对截获C请求同钥加密得到M”的证明，并说清变体条件。'),
 dict(id='e5-1',lecture='第五讲',page=45,no=1,title='CBC / CTR 计算与密文翻位',
      targets=[('m01',3,'CBC先异或前块，再加密；首块用IV'),('m02',4,'CTR先加密计数器，再与明文异或'),('m03',1,'原题3块CBC与CTR的全部计算'),('m03',2,'仅重点掌握表中的CBC、CTR两行及推导'),('m03',3,'玩具密码与AES的错误传播差别')],
      prereqs=[('t02',1,'异或相同得0、不同得1，以及异或抵消')],
      answer=('m03','先独立完成CBC与CTR的全部中间量'),ready='能列出两模式全部中间量与密文，并分别说明C₂最高位翻转对M₂、M₃的影响；玩具算法须指出精确位。'),
 dict(id='e5-2',lecture='第五讲',page=46,no=2,title='hello 与重复密钥流',
      targets=[('f01',2,'同段密钥流复用时如何抵消和恢复明文'),('f01',5,'ASCII逐字节异或、密文问题与攻击优势')],
      prereqs=[('f01',1,'二元加法流密码的加解密异或式')],
      answer=('f01','hello作业中，攻击者知道第一个字符h'),ready='能算出5个密文字节，解释重复l的泄露、8位周期、256种重复字节候选，以及已知明文如何恢复流。'),
 dict(id='e5-3',lecture='第五讲',page=47,no=3,title='HKDF-SM3 派生600比特密钥',
      targets=[('a02',3,'Extract/Expand参数顺序、递推与单字节计数器'),('a02',4,'向上取整求N，以及末块取位')],
      prereqs=[('a01',2,'Co是HMAC；区分密钥参数、消息参数与输出长度')],
      answer=('a02','写出600位派生的T(1)'),ready='能求N，展开T(1)、T(2)、T(3)，说明计数器01/02/03的字节编码，并算出末块使用多少位。'),
]

CSS=r'''
/* homework-priority-v1: priority annotations, independent from scores */
:root{--hw-ink:#9b2d22;--hw-soft:#fff2ec;--hw-line:#eeb9a5;--hw-pre:#795719;--hw-pre-soft:#fff9e9}
html[data-theme="dark"]{--hw-ink:#ffc4a9;--hw-soft:#362a27;--hw-line:#875548;--hw-pre:#efd194;--hw-pre-soft:#333025}
.hw-entry{margin:20px 0;padding:20px 23px;border:1px solid var(--hw-line);border-radius:10px;background:var(--hw-soft);font-size:14px}.hw-entry strong{display:block;color:var(--hw-ink);font-size:17px;margin-bottom:7px}.hw-entry p{margin:5px 0 13px}.hw-badge{display:inline-block;vertical-align:middle;margin:0 0 3px 9px;padding:3px 8px;border-radius:5px;background:var(--hw-soft);color:var(--hw-ink);border:1px solid var(--hw-line);font:700 12px/1.5 "Microsoft YaHei",sans-serif;white-space:nowrap}.hw-badge.pre{background:var(--hw-pre-soft);color:var(--hw-pre);border-color:var(--line)}.hw-focus-note{font-size:14px;line-height:1.85;border-left:3px solid var(--hw-ink);background:var(--hw-soft);border-radius:0 7px 7px 0;padding:12px 16px;margin:0 0 22px}.hw-focus-note.pre{background:var(--hw-pre-soft);border-left-color:var(--hw-pre)}.hw-focus-note p{margin:4px 0}.hw-focus-note .hw-source-links{font-size:12px}.hw-focus-note a{color:var(--hw-ink)}.hw-focus-note.pre a{color:var(--hw-pre)}.hw-legend{font-size:14px;line-height:1.9;color:var(--muted)}.hw-legend .hw-badge{margin-left:0}.hw-grid{display:grid;grid-template-columns:1fr 1fr;gap:17px;margin:20px 0}.hw-card{border:1px solid var(--line);border-top:3px solid var(--hw-line);border-radius:8px;padding:21px;background:var(--paper);scroll-margin-top:105px}.hw-card h4{font-size:18px;margin:8px 0 13px}.hw-card small{color:var(--hw-ink);font-weight:650}.hw-card ul{padding-left:20px;font-size:14px;margin:10px 0}.hw-card li{margin:5px 0}.hw-card p{font-size:13px;line-height:1.85;margin:10px 0}.hw-card .hw-ready{padding:12px;background:var(--surface);border-radius:6px}.hw-card .btn{font-size:12px}.hw-card details{font-size:13px;margin:12px 0}.hw-card summary{cursor:pointer;color:var(--hw-pre)}.hw-card .hw-prereq-list{font-size:13px}.hw-jumps{display:flex;gap:10px;flex-wrap:wrap;margin:16px 0}.hw-nav-badge{font-size:9px;border-radius:3px;padding:2px 4px;line-height:1.6;color:var(--hw-ink);background:var(--hw-soft);white-space:nowrap;flex:none}.hw-nav-badge.pre{color:var(--hw-pre);background:var(--hw-pre-soft)}#hw-nav-toggle{width:100%;margin-top:9px;font-size:12px;min-height:35px}#hw-nav-toggle[aria-pressed="true"]{border-color:var(--hw-line);background:var(--hw-soft);color:var(--hw-ink)}#hw-nav-status{font-size:11px;line-height:1.65}.hw-homework-details{scroll-margin-top:105px}.hw-homework-details>summary{border-left:3px solid var(--hw-ink)}
@media(max-width:1100px){.hw-grid{grid-template-columns:1fr}.hw-card{padding:18px}}@media(max-width:600px){.hw-entry{padding:16px;font-size:13px}.hw-entry strong{font-size:16px}.hw-focus-note{padding:11px 13px;font-size:13px}.hw-badge{font-size:11px}.hw-nav-badge{font-size:9px}}
@media print{.hw-grid{display:block}.hw-card{break-inside:avoid;margin:15px 0}.hw-focus-note{border:1px solid #999;background:white}.hw-entry{display:none}.hw-badge{border:1px solid #777;background:white;color:black}}
'''

JS=r'''
(function(){
'use strict';
function init(){
 const toggle=document.getElementById('hw-nav-toggle'),search=document.getElementById('nav-search'),status=document.getElementById('hw-nav-status');
 const links=Array.from(document.querySelectorAll('.nav-link[data-nav]'));
 let onlyHomework=false;
 function filter(){
   if(!onlyHomework){status.textContent='正文中：必会是作业直接要求，前置是补基础。';return;}
   let visible=0;
   for(const a of links){a.hidden=a.hidden||!a.dataset.homeworkLevel;if(!a.hidden)visible++;}
   document.querySelectorAll('.nav-group').forEach(e=>e.hidden=true);
   document.getElementById('nav-no-results').hidden=visible>0;
   status.textContent=visible?'目录显示 '+visible+' 个作业相关章节；正文与成绩保留。':'当前检索没有匹配的作业相关章节。';
 }
 search.addEventListener('input',filter);
 toggle.addEventListener('click',()=>{onlyHomework=!onlyHomework;toggle.setAttribute('aria-pressed',String(onlyHomework));toggle.textContent=onlyHomework?'恢复全部章节目录':'目录只看作业相关';search.dispatchEvent(new Event('input',{bubbles:true}));});
 function openTarget(){
  let id;try{id=decodeURIComponent(location.hash.slice(1));}catch{return;}
  const el=document.getElementById(id);if(!el)return;
  if(el.matches('details.hw-homework-details'))el.open=true;
  for(let p=el.parentElement;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;
 }
 document.querySelectorAll('#homework-priority a[href^="#hw-answer-"]').forEach(a=>a.addEventListener('click',()=>{const e=document.getElementById(a.hash.slice(1));if(e&&e.tagName==='DETAILS')e.open=true;}));
 document.querySelectorAll('a[href^="#homework-"]').forEach(a=>a.addEventListener('click',()=>{if(innerWidth<=900){document.getElementById('sidebar').classList.remove('is-open');document.getElementById('menu-overlay').hidden=true;document.getElementById('menu-btn').setAttribute('aria-expanded','false');}}));
 window.addEventListener('hashchange',openTarget);openTarget();filter();
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
'''

def plain(s):return html.unescape(re.sub('<[^>]*>','',s)).strip()
def esc(s):return html.escape(str(s),quote=True)

def annotate(source):
    if 'id="homework-priority"' in source:return source
    # Collect only precise, homework-supported headings. A chapter badge means it CONTAINS required material.
    marks={}
    for ex in EXERCISES:
        for level,items in [('direct',ex['targets']),('pre',ex['prereqs'])]:
            for module,n,label in items:
                key=(module,n);item=marks.setdefault(key,dict(level=level,exercises=[],labels=[]))
                if level=='direct':item['level']='direct'
                if ex not in item['exercises']:item['exercises'].append(ex)
                if label not in item['labels']:item['labels'].append(label)
    heading_ids={};chapter_levels={}
    for (module,n),item in marks.items():
        previous=chapter_levels.get(module)
        chapter_levels[module]='direct' if 'direct' in [previous,item['level']] else 'pre'
    for module in chapter_levels:
        pat=rf'(<section\b[^>]*\bid="{module}"[^>]*>)([\s\S]*?)(</section>)'
        def chapter(m):
            counter=0
            def heading(h):
                nonlocal counter
                counter+=1;key=(module,counter)
                if key not in marks:return h[0]
                item=marks[key];attrs,content=h[1],h[2]
                idmatch=re.search(r'\bid="([^"]+)"',attrs)
                hid=idmatch[1] if idmatch else f'hw-{module}-h{counter}'
                if not idmatch:attrs+=' id="'+hid+'"'
                heading_ids[key]=hid
                pre=item['level']=='pre';level='前置' if pre else '必会';cls=' pre' if pre else ''
                refs='、'.join(f'<a href="#homework-{e["id"]}">{e["lecture"]} P{e["page"]} · 作业{e["no"]}</a>' for e in item['exercises'])
                badge=f'<span class="hw-badge{cls}">{level}</span>'
                note=f'<div class="hw-focus-note{cls}"><div class="hw-source-links">{refs}</div><p><strong>{"先补这项基础" if pre else "这部分必须会"}：</strong>{esc("；".join(item["labels"]))}。</p></div>'
                return f'<h3{attrs}>{content}{badge}</h3>'+note
            body=re.sub(r'<h3\b([^>]*)>([\s\S]*?)</h3>',heading,m[2])
            return m[1]+body+m[3]
        source,count=re.subn(pat,chapter,source,count=1)
        assert count==1,module
    assert set(heading_ids)==set(marks),'a required heading was not found'
    # Stable answer anchors on existing explanation panels. No new answers or scoring state.
    for ex in EXERCISES:
        module,selector=ex['answer']
        if isinstance(selector,int):ex['answer_id']=heading_ids[(module,selector)];continue
        aid='hw-answer-'+ex['id'];pat=rf'(<section\b[^>]*\bid="{module}"[^>]*>)([\s\S]*?)(</section>)'
        def answer(m):
            hits=0
            def details(d):
                nonlocal hits
                if selector not in plain(d[2]):return d[0]
                hits+=1;attrs=d[1]
                assert not re.search(r'\bid=',attrs),'existing details ID must be preserved'
                attrs+=' id="'+aid+'"'
                if 'class="' in attrs:attrs=attrs.replace('class="','class="hw-homework-details ',1)
                else:attrs+=' class="hw-homework-details"'
                return '<details'+attrs+'><summary>'+d[2]+'</summary>'
            body=re.sub(r'<details\b([^>]*)>\s*<summary[^>]*>([\s\S]*?)</summary>',details,m[2])
            assert hits==1,(ex['id'],hits)
            return m[1]+body+m[3]
        source,count=re.subn(pat,answer,source,count=1);assert count==1
        ex['answer_id']=aid
    cards=[]
    for ex in EXERCISES:
        tasks=''.join(f'<li><a href="#{heading_ids[(mid,n)]}">{esc(label)}</a></li>' for mid,n,label in ex['targets'])
        prereqs=''
        if ex['prereqs']:
            prereqs='<details><summary>零基础先补（'+str(len(ex['prereqs']))+'项）</summary><ul class="hw-prereq-list">'+''.join(f'<li><a href="#{heading_ids[(mid,n)]}">{esc(label)}</a></li>' for mid,n,label in ex['prereqs'])+'</ul></details>'
        cards.append(f'<article class="hw-card" id="homework-{ex["id"]}"><small>{ex["lecture"]} P{ex["page"]} · 课后作业{ex["no"]}</small><h4>{esc(ex["title"])}</h4><ul>{tasks}</ul>{prereqs}<p class="hw-ready"><strong>过关标准：</strong>{esc(ex["ready"])}</p><a class="btn" href="#{ex["answer_id"]}">定位原题与标准解答</a></article>')
    groups=[]
    for lec,ids in [('第二讲',['e2-1','e2-2','e2-3']),('第四讲',['e4-1','e4-2']),('第五讲',['e5-1','e5-2','e5-3'])]:
        selected=[c for ex,c in zip(EXERCISES,cards) if ex['id'] in ids]
        groups.append(f'<h3 id="homework-lecture-{lec}">{lec} · {len(ids)}道课后作业</h3><div class="hw-grid">'+''.join(selected)+'</div>')
    panel='''<section class="appendix" id="homework-priority"><span class="source-tag">按原PPT课后作业定位 · 第二讲P50、第四讲P55–56、第五讲P45–47</span><h2>课后作业必会清单</h2><p>先选一道作业，按链接看直接相关的知识，再独立解题。能达到“过关标准”，就完成这一题要求的学习任务。</p><p class="hw-legend"><span class="hw-badge">必会</span> 作业直接涉及的定义、公式、计算或证明。<span class="hw-badge pre">前置</span> 为完成题目需先补的基础。目录的“含必会”表示该章有必会段落，具体范围以正文标签为准。标注依据是课后作业，不等同于教师划定的全部考试范围。</p><div class="hw-jumps"><a class="btn" href="#homework-lecture-第二讲">第二讲 · 3题</a><a class="btn" href="#homework-lecture-第四讲">第四讲 · 2题</a><a class="btn" href="#homework-lecture-第五讲">第五讲 · 3题</a></div>'''+''.join(groups)+'''<p class="caption">第三讲原课件未发现单列“课后作业/课程作业”的页面，本次不凭空追加必会范围。课堂小测、完整算法推导与其他内容仍保留在原章节中。</p></section>'''
    source,count=re.subn(r'(<section\b[^>]*\bid="b01"[^>]*>)',lambda m:panel+'\n'+m[0],source,count=1);assert count==1
    entry='''<div class="hw-entry"><strong>按课后作业抓重点 · 8道作业已逐项标注</strong><p>正文橙红色“必会”标出直接相关知识，黄色“前置”帮助补基础。先从这张清单定位，不必逐章寻找作业。</p><div class="button-row"><a class="btn btn-primary" href="#homework-priority">打开作业必会清单</a><a class="btn" href="#homework-lecture-第四讲">第四讲重点</a><a class="btn" href="#homework-lecture-第五讲">第五讲重点</a></div></div>'''
    source,count=re.subn(r'(<p class="hero-intro">[\s\S]*?</p>)',lambda m:m[0]+entry,source,count=1);assert count==1
    nav='<a class="nav-link" href="#homework-priority"><span class="nav-number" aria-hidden="true">★</span><span class="nav-label">课后作业必会清单 · 8题</span></a>'
    source,count=re.subn(r'(<nav\b[^>]*class="nav-list"[^>]*>)',lambda m:m[0]+nav,source,count=1);assert count==1
    for module,level in chapter_levels.items():
        pat=rf'(<a\b[^>]*\bdata-nav="{module}"[^>]*>)([\s\S]*?)(</a>)'
        def badge(m):
            return m[1][:-1]+' data-homework-level="'+level+'">'+m[2]+f'<span class="hw-nav-badge{" pre" if level=="pre" else ""}">{"前置" if level=="pre" else "含必会"}</span>'+m[3]
        source,count=re.subn(pat,badge,source,count=1);assert count==1,module
    controls='<button type="button" class="btn" id="hw-nav-toggle" aria-pressed="false">目录只看作业相关</button><p id="hw-nav-status">正文中：必会是作业直接要求，前置是补基础。</p>'
    source,count=re.subn(r'(<div class="nav-search">[\s\S]*?)(</div>)',lambda m:m[1]+controls+m[2],source,count=1);assert count==1
    source=source.replace('</head>','<style id="homework-priority-style">'+CSS+'</style></head>',1)
    source=source.replace('</body>','<script id="homework-priority-script">'+JS+'</script></body>',1)
    manifest=dict(exercises=EXERCISES,headings=[dict(module=m,number=n,id=heading_ids[(m,n)],level=v['level']) for (m,n),v in marks.items()],chapterLevels=chapter_levels)
    (ROOT/'.guide-build/homework-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    return source

if __name__=='__main__':
    before=TARGET.read_text(encoding='utf-8')
    backup=ROOT/'.guide-build/pre-homework-priority.html'
    if not backup.exists():shutil.copy2(TARGET,backup)
    result=annotate(before)
    TARGET.write_text(result,encoding='utf-8')
    print('Homework priority annotations added.' if result!=before else 'Already annotated; no change.')
