/* Three self-contained teaching experiments. No cryptographic production API. */
(function(){
'use strict';
const S=[14,4,13,1,2,15,11,8,3,10,6,12,5,9,0,7],P=[1,5,9,13,2,6,10,14,3,7,11,15,4,8,12,16];
const INV=Array(16);S.forEach((v,i)=>INV[v]=i);
const hex=(n,w=4)=>n.toString(16).toUpperCase().padStart(w,'0');
const bits=n=>n.toString(2).padStart(4,'0');
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function grid(head,rows){return '<div class="table-wrap" tabindex="0" role="region" aria-label="可横向滚动的实验计算表"><table><thead><tr>'+head.map(x=>'<th scope="col">'+esc(x)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+r.map(x=>'<td class="mono">'+esc(x)+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';}
function sub(x,box){let y=0;for(let i=0;i<4;i++)y=(y<<4)|box[(x>>>(12-4*i))&15];return y;}
function perm(x){let y=0;P.forEach((d,i)=>y|=((x>>>(15-i))&1)<<(16-d));return y;}
function setupLab(id,title,help,fields,run){const el=document.getElementById(id);if(!el)return;el.innerHTML='<h3>'+title+'</h3><p class="caption">'+help+'</p><div class="lab-fields">'+fields+'</div><button type="button" class="btn btn-primary lab-run">运行并展开计算</button><div class="lab-output" aria-live="polite"></div>';const out=el.querySelector('.lab-output');const execute=()=>{try{run(el,out);}catch(e){out.innerHTML='<p class="lab-error">'+esc(e.message)+'</p>';}};el.querySelector('.lab-run').addEventListener('click',execute);execute();}
function input(name,label,value,maxlength){return '<label>'+label+'<input name="'+name+'" value="'+value+'" maxlength="'+maxlength+'" autocomplete="off" spellcheck="false"></label>';}
function get(el,name){return el.querySelector('[name="'+name+'"]').value.trim();}
function init(){
setupLab('spn-lab','SPN 四轮演算台','输入4位十六进制明文与8位十六进制主密钥，查看完整加密及逆推。仅为课件教学算法。',input('plain','16位明文（4个十六进制位）','26B7',4)+input('key','32位主密钥（8个十六进制位）','3A94D63F',8),(el,out)=>{
 const p=get(el,'plain'),k=get(el,'key');if(!/^[\da-f]{4}$/i.test(p)||!/^[\da-f]{8}$/i.test(k))throw new Error('明文应恰好4个十六进制位，密钥应恰好8位；保留前导0。');
 const keys=Array.from({length:5},(_,i)=>parseInt(k.slice(i,i+4),16));let x=parseInt(p,16);const rows=[];
 for(let i=0;i<4;i++){let u=x^keys[i],v=sub(u,S);x=i<3?perm(v):v^keys[4];rows.push([i+1,hex(keys[i]),hex(u),hex(v),i<3?hex(x):'无P；白化后 '+hex(x)]);}
 const cipher=x;const undo=[];x^=keys[4];undo.push(['撤白化','y ⊕ K5',hex(x)]);x=sub(x,INV)^keys[3];undo.push(['撤第4轮','逆S，再 ⊕ K4',hex(x)]);
 for(let i=2;i>=0;i--){const a=perm(x),b=sub(a,INV);x=b^keys[i];undo.push(['撤第'+(i+1)+'轮',hex(a)+' →逆S '+hex(b)+' →异或 '+hex(keys[i]),hex(x)]);}
 out.innerHTML='<p class="lab-result">密文 <strong class="mono">'+hex(cipher)+'</strong>，逆推恢复 <strong class="mono">'+hex(x)+'</strong>。</p>'+grid(['轮','Kr','ur','vr','wr / 输出'],rows)+grid(['步骤','操作或中间值','结果'],undo);
});
const modeOptions=['ECB','CBC','CFB','OFB','CTR'].map(x=>'<option'+(x==='CBC'?' selected':'')+'>'+x+'</option>').join('');
setupLab('modes-lab','五模式与单比特错误实验','同一个4位玩具密码E(X)=ROL₄(X⊕K,1)。不具备真实密码的扩散；每块恰好4位，最多16块。',
 '<label>模式<select name="mode">'+modeOptions+'</select></label>'+input('message','明文块（空格隔开）','0011 0011 1100',90)+input('key','4位密钥','1010',4)+input('iv','4位IV / CTR起点','0101',4)+'<label>翻转哪一块密文<select name="block"><option value="0">不翻转</option><option value="1">C1</option><option value="2" selected>C2</option><option value="3">C3</option></select></label><label>块内位（从左到右）<select name="bit"><option value="0">第1位（最高位）</option><option value="1">第2位</option><option value="2">第3位</option><option value="3">第4位</option></select></label>',(el,out)=>{
 const parts=get(el,'message').split(/\s+/),key=get(el,'key'),iv=get(el,'iv'),mode=get(el,'mode');
 if(!parts.length||parts.length>16||parts.some(p=>!/^([01]{4})$/.test(p))||!/^([01]{4})$/.test(key)||!/^([01]{4})$/.test(iv))throw new Error('所有块、密钥和IV均应恰好4个0/1；明文块用空格隔开，最多16块。');
 const M=parts.map(p=>parseInt(p,2)),K=parseInt(key,2),IV=parseInt(iv,2),E=x=>{const a=x^K;return ((a<<1)|(a>>>3))&15;},D=x=>(((x>>>1)|(x<<3))&15)^K;
 if(mode==='CTR'&&IV+M.length-1>15)throw new Error('4位计数器将回绕并重复。请减小起点或块数。');
 const C=[],rows=[];let previous=IV,ofb=IV;
 M.forEach((m,i)=>{let input,stream='—',c;if(mode==='ECB'){input=m;c=E(input);}else if(mode==='CBC'){input=m^previous;c=E(input);}else if(mode==='CFB'){input=previous;stream=E(input);c=m^stream;}else if(mode==='OFB'){input=ofb;ofb=E(input);stream=ofb;c=m^stream;}else{input=IV+i;stream=E(input);c=m^stream;}C.push(c);rows.push([i+1,bits(m),bits(input),typeof stream==='number'?bits(stream):stream,bits(c)]);previous=c;});
 const block=Number(get(el,'block')),bit=Number(get(el,'bit')),received=[...C];if(block>M.length)throw new Error('选中的密文块不存在，请选择已有块。');if(block)received[block-1]^=1<<(3-bit);
 const decoded=[];previous=IV;ofb=IV;
 received.forEach((c,i)=>{let m;if(mode==='ECB')m=D(c);else if(mode==='CBC')m=D(c)^previous;else if(mode==='CFB')m=c^E(previous);else if(mode==='OFB'){ofb=E(ofb);m=c^ofb;}else m=c^E(IV+i);decoded.push(m);previous=c;});
 out.innerHTML='<p class="lab-result">原密文：<span class="mono">'+C.map(bits).join(' ')+'</span><br>收到：<span class="mono">'+received.map(bits).join(' ')+'</span><br>解密：<span class="mono">'+decoded.map(bits).join(' ')+'</span></p>'+grid(['i','Mi','送进完整E的块','掩码（流模式）','Ci'],rows)+grid(['i','原Mi','收到Ci','解密Mi','差分：1表示该位变化'],decoded.map((m,i)=>[i+1,bits(M[i]),bits(received[i]),bits(m),bits(m^M[i])]))+'<p class="caption">差分是两明文异或。此玩具E/D只是异或加循环移位，所以CBC/CFB受扰块不会出现真实强密码常见的广泛扩散。</p>';
});
setupLab('zuc-iv-lab','ZUC 机密性参数计算台','只构造EEA3的IV与长度参数，不生成密钥流，也不接收真实密钥。COUNT按十六进制，BEARER按5位二进制，长度按比特。',input('count','COUNT（8位十六进制）','66035492',8)+input('bearer','BEARER（5位二进制）','01111',5)+'<label>DIRECTION<select name="direction"><option value="0">0</option><option value="1">1</option></select></label>'+input('length','LENGTH（非负整数比特）','1000',10),(el,out)=>{
 const count=get(el,'count'),bearer=get(el,'bearer'),direction=Number(get(el,'direction')),len=get(el,'length');
 if(!/^[\da-f]{8}$/i.test(count)||!/^([01]{5})$/.test(bearer)||!/^\d{1,10}$/.test(len))throw new Error('COUNT须8位十六进制，BEARER须5位二进制，LENGTH须非负整数。');
 const length=Number(len);if(length>0xffffffff)throw new Error('该实验长度范围为0到4294967295比特。');
 const bytes=count.match(/../g).map(x=>parseInt(x,16));bytes.push((parseInt(bearer,2)<<3)|(direction<<2),0,0,0);const iv=[...bytes,...bytes],words=Math.ceil(length/32),last=length===0?0:((length-1)%32)+1;
 out.innerHTML='<p class="lab-result">IV：<strong class="mono">'+iv.map(x=>hex(x,2)).join(' ')+'</strong><br>iv4 = '+bearer+' ‖ '+direction+' ‖ 00 = '+hex(bytes[4],2)+'<br>需要 <strong>'+words+'</strong> 个32位字；'+(length?'末字取最高 <strong>'+last+'</strong> 位，丢弃 '+(32-last)+' 位。':'长度为0，不需要输出密钥字。')+'</p>'+grid(['字节序号','十六进制','来源'],iv.map((v,i)=>[i,hex(v,2),i>=8?'复制iv'+(i-8):i<4?'COUNT的字节':i===4?'BEARER‖DIRECTION‖00':'全0']));
});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
