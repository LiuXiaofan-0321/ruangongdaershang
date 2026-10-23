from pathlib import Path
import re,shutil

ROOT=Path(__file__).resolve().parent.parent
TARGET=ROOT/'密码学_深度学习指南.html'
BUILD=ROOT/'.guide-build'

def refresh(source):
    source=source.replace('<tspan style="font-size:9px">K</tspan>','<sub style="font-size:9px">K</sub>')
    if 'id="editorial-ui-style"' in source:
        return re.sub(r'<style id="editorial-ui-style">[\s\S]*?</style>',lambda m:'<style id="editorial-ui-style">'+(BUILD/'visual-refresh.css').read_text(encoding='utf-8')+'</style>',source,count=1)
    match=re.search(r'<section class="welcome" id="welcome">[\s\S]*?</section>',source)
    assert match,'welcome section missing'
    old=match[0]
    def snippet(pattern):
        m=re.search(pattern,old);assert m,pattern;return m[0]
    intro=snippet(r'<p class="hero-intro">[\s\S]*?</p>')
    hw=snippet(r'<div class="hw-entry">[\s\S]*?</div></div>')
    cipher=snippet(r'<div aria-label="三种不同对象[\s\S]*?</div></div>')
    caption=snippet(r'<p class="caption">加密可由持钥者[\s\S]*?</p>')
    method=snippet(r'<div class="intro-grid">[\s\S]*?</div></div>')
    paths=snippet(r'<div class="path-grid">[\s\S]*?</div>')
    usage=snippet(r'<details class="think"><summary>使用说明[\s\S]*?</details>')
    fourth=snippet(r'<div class="callout intuition"><strong>已续入[\s\S]*?</div></div>')
    fourth=fourth.replace('已续入第四讲与第五讲 · 新增16章、48道选择题','第四、第五讲 · 算法演算与应用')
    routes='''<nav class="lecture-routes" aria-label="按讲次开始学习"><a class="lecture-route" href="#b01"><span class="route-index">02</span><strong>古典密码与安全观</strong><small>第1—9章 · 建立共同语言</small></a><a class="lecture-route" href="#r01"><span class="route-index">03</span><strong>随机数与杂凑</strong><small>第10—18章 · 走通SM3</small></a><a class="lecture-route" href="#t01"><span class="route-index">04</span><strong>对称加密与分组算法</strong><small>第19—26章 · DES / AES / SM4</small></a><a class="lecture-route" href="#m01"><span class="route-index">05</span><strong>模式、流密码与认证</strong><small>第27—34章 · 串起完整应用</small></a></nav>'''
    hero='''<section class="welcome" id="welcome"><div class="hero-masthead"><div class="hero-copy"><div class="hero-kicker">密码与网络安全引论 · 第二讲至第五讲</div><h1>密码学，<br><em>从零到会用。</em></h1>'''+intro+'''<div class="button-row"><a class="btn btn-primary" href="#homework-priority">先看作业必会清单 ↗</a><a class="btn" href="#b01">从基础开始</a><button class="btn" id="overview-btn" type="button">学习概况</button></div><div class="hero-meta"><span>34 个知识模块</span><span>102 道互动自测</span><span>8 道作业重点</span></div></div><div class="hero-art" aria-hidden="true"><div class="cipher-orbit"><div class="orbit-core">κ</div><span class="orbit-chip a">0101 1010</span><span class="orbit-chip b">E<sub style="font-size:9px">K</sub>(M)</span><span class="orbit-chip c">⊕</span><span class="orbit-chip d">理解每一次变换</span></div><span class="art-caption">CRYPTOGRAPHY · FIELD NOTES</span></div></div><div class="welcome-body">'''+hw+cipher+caption+routes+'''<details class="welcome-more"><summary>学习方法、完整路线与使用说明</summary>'''+method+paths+fourth+usage+'</details></div></section>'
    source=source[:match.start()]+hero+source[match.end():]
    source=source.replace('</head>','<style id="editorial-ui-style">'+(BUILD/'visual-refresh.css').read_text(encoding='utf-8')+'</style></head>',1)
    return source

if __name__=='__main__':
    original=TARGET.read_text(encoding='utf-8');backup=BUILD/'pre-visual-refresh.html'
    if not backup.exists():shutil.copy2(TARGET,backup)
    TARGET.write_text(refresh(original),encoding='utf-8')
    print('Updated',TARGET.name,TARGET.stat().st_size,'bytes')
