import fs from 'node:fs/promises';
import path from 'node:path';
import {importRuntimeModule} from 'file:///C:/Users/Steven/.codex/plugins/cache/openai-primary-runtime/presentations/26.1015.12040/skills/presentations/container_tools/runtime_helpers.mjs';
const {FileBlob,PresentationFile}=await importRuntimeModule('@oai/artifact-tool');
const ROOT='C:/courses/密码与网络安全引论';
const BUILD=path.join(ROOT,'.ppt-redesign');
const p=await PresentationFile.importPptx(await FileBlob.load('C:/Users/Steven/Desktop/一笔成章 · 中期汇报 v1.1.pptx'));
const source=JSON.parse(await fs.readFile(path.join(BUILD,'source-content.json'),'utf8'));
const C={navy:'#143E5A',teal:'#15545C',ink:'#16394B',body:'#365567',muted:'#66818E',blue:'#DBEAF3',mint:'#DFEEE5',ice:'#E6EFF4',green:'#BDE3B1',white:'#FFFFFF',light:'#D7E7EE',accent:'#087C78'};
const FONT='Microsoft YaHei';
const imgs=p.slides.items.map(s=>s.images.items.slice());
const tables=p.slides.items.map(s=>s.tables.items.slice());
function text(s,value,x,y,w,h,size=22,color=C.ink,bold=false,name='text',align='left'){
 const sh=s.shapes.add({name,geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 sh.text=value;
 sh.text.style={fontSize:size,typeface:FONT,color,bold,alignment:align,verticalAlignment:'top',autoFit:'none',wrap:'square',insets:0,lineSpacing:1.18};
 return sh;
}
function setup(n,bg,title,dark=false){
 const s=p.slides.items[n-1];s.shapes.deleteAll();s.background.fill=bg;
 s.speakerNotes.text='原稿内容留存\n'+source[n-1].texts.join('\n');
 if(title)text(s,title,64,42,1152,64,40,dark?C.white:C.ink,true,'slide-title');
 text(s,'一笔成章  /  中期汇报',64,683,700,22,15,dark?'#9EBFCB':C.muted,false,'footer');
 text(s,`${String(n).padStart(2,'0')} / 13`,1130,681,86,24,16,dark?'#9EBFCB':C.muted,false,'page-number','right');
 return s;
}
function pic(n,k,x,y,w,h){const im=imgs[n-1][k];im.frame={left:x,top:y,width:w,height:h};im.fit='contain';im.geometry='rect';im.crop={left:0,top:0,right:0,bottom:0};return im;}
function label(s,a,b,x,y,w,opts={}){
 const {dark=false,bodySize=22,titleSize=26,bodyHeight=94}=opts;
 text(s,a,x,y,w,40,titleSize,dark?C.green:C.accent,true);
 text(s,b,x,y+48,w,bodyHeight,bodySize,dark?C.light:C.body);
}
function tableStyle(t,x,y,w,heights,widths,values,size=21,highlightRow=-1){
 t.position={left:x,top:y,width:w,height:heights.reduce((a,b)=>a+b,0)};
 t.columnWidths=widths;
 for(let i=0;i<heights.length;i++)t.rows[i].height=heights[i];
 t.styleOptions={headerRow:false,bandedRows:false,firstColumn:false,lastColumn:false};
 t.borders.assign({fill:'#A7C1C7',width:.7,style:'solid'});
 for(let r=0;r<values.length;r++)for(let c=0;c<values[r].length;c++){
  const cell=t.getCell(r,c);cell.value=values[r][c];
  cell.fill=r===0?C.navy:(r===highlightRow?'#C7E4D7':(r%2?'#EDF5F0':'#DFEEE5'));
  cell.text.style={typeface:FONT,fontSize:r===0?20:size,color:r===0?C.white:C.ink,bold:r===0||r===highlightRow,verticalAlignment:'middle',alignment:'left',insets:12,autoFit:'none',wrap:'square',lineSpacing:1.1};
 }
 return t;
}

// 01 Cover
{
 const s=setup(1,C.navy,null,true);
 text(s,'华东师范大学',64,54,650,34,24,C.light,true);
 text(s,'本科生创新训练培育项目（创业训练类）',64,95,750,28,19,C.light);
 text(s,'一笔成章',64,214,650,110,84,C.white,true,'cover-title');
 text(s,'基于视觉模型的全场景\n汉字书法智能反馈系统',68,346,620,106,30,C.white);
 text(s,'中期汇报   2026.10',68,488,620,40,28,C.green,true);
 text(s,'汇报人  刘小凡（软件工程学院）\n指导教师  万成城',68,571,660,74,21,C.light);
 pic(1,0,725,216,510,356);
 text(s,'iPad 端 AI 分析实拍',770,589,400,28,18,C.light,false,'image-caption','center');
}
// 02 Product overview
{
 const s=setup(2,C.mint,'项目简介：核心功能与用户画像');
 text(s,'面向汉字书写与书法练习的\n全场景智能反馈系统',64,143,610,94,34,C.ink,true);
 text(s,'压感笔实时书写，或拍照上传作品。\n每次练习获得量化结构评分与局部修改建议。',64,252,608,76,22,C.body);
 label(s,'实时书写与拍照评估','压感笔书写后即时分析；\n上传练字作品，诊断整体结构。',64,359,605,{bodyHeight:72});
 label(s,'参考结构匹配与课程练习','与名家范字量化对照，结合课程字库，\n给出可解释、定位到局部的修改建议。',64,503,605,{bodyHeight:80});
 pic(2,0,737,128,472,330);
 text(s,'iPad 深度练习  +  Web 规模化覆盖',732,469,480,35,23,C.accent,true);
 const xx=[735,900,1065];
 const vals=['60%','25%','15%'];
 const aa=['6–18 岁','18–25 岁','25 岁以上'];
 const bb=['K12 学生\n考级与课业','大学生\n素养与技能','爱好者 / 职场人\n兴趣与修养'];
 for(let i=0;i<3;i++){
  text(s,'约 '+vals[i],xx[i],526,154,54,36,C.navy,true);
  text(s,aa[i],xx[i],583,155,26,18,C.ink,true);
  text(s,bb[i],xx[i],615,155,50,17,C.body);
 }
}
// 03 Context
{
 const s=setup(3,C.blue,'项目背景：政策、市场与书写方式');
 const x=[64,465,866];
 const titles=['政策支持','家庭投入','无纸化学习'];
 const nums=['01','02','03'];
 for(let i=0;i<3;i++){
  text(s,nums[i],x[i],151,315,70,54,C.accent,true);
  text(s,titles[i],x[i],235,330,43,30,C.ink,true);
 }
 text(s,'《中小学书法教育指导纲要》\n将书法纳入中小学教学体系。\n\n“双减”后的课后服务\n与学校美育建设，持续需要\n优质书法教育内容。',64,299,345,250,22,C.body);
 text(s,'家长重视传统文化、专注力与\n审美素养，并为课程和工具投入\n稳定的学期预算。',465,299,345,104,22,C.body);
 text(s,'41.58%',465,431,345,64,46,C.navy,true);
 text(s,'愿投入 1000–3000 元 / 学期',465,497,355,30,20,C.body);
 text(s,'11.88%',465,546,345,45,34,C.accent,true);
 text(s,'愿投入 5000 元以上 / 学期',465,590,355,30,20,C.body);
 text(s,'平板与手写笔逐步普及，\n高校无纸化学习尤其突出。\n\n书写介质改变后，用户仍需练习\n以适应书写体验；电子纸也有助于\n减少纸张消耗。',866,299,350,250,22,C.body);
 text(s,'政策、家庭需求与书写介质的变化，共同带来智能反馈需求',64,626,1152,42,26,C.ink,true);
}
// 04 Problem and response
{
 const s=setup(4,C.teal,'市场痛点：软件供给跟不上硬件与需求',true);
 text(s,'现有软件多停留在字帖临摹与分享，练习指导不足。\n手写笔已有 4096 级压感，丰富书写数据仍未得到充分利用。',64,148,1152,90,26,C.light);
 const xs=[64,465,866];
 const title=['反馈滞后','评价主观','练习静态'];
 const body=['一对多课堂批改周期长，\n问题笔画难以及时纠正，\n错误写法反复固化。','缺少可量化的结构标准，\n“写得好不好”依赖感觉，\n练习者难以独立判断。','字帖只能临摹对照，\n缺少针对个人问题的修改路径，\n练习效率低、容易放弃。'];
 for(let i=0;i<3;i++)label(s,title[i],body[i],xs[i],300,350,{dark:true,titleSize:31,bodyHeight:126,bodySize:23});
 text(s,'视觉模型带来的练习反馈',64,533,1152,38,24,C.green,true);
 text(s,'即时结构评分，公开量化标准，给出局部修改路径',64,586,1152,50,34,C.white,true);
}
// 05 Iteration table
{
 const s=setup(5,C.mint,'迭代逻辑：以往局限与今年的解决方案');
 const values=[
  ['以往局限','今年的解决方案','验证证据'],
  ['评估口径自定\nU-Net 自定义准确率约 85.2%，\n难以横向比较','统一六通道 schema\n采用 Dice、IoU、关键点 F1、\n边界 F1 标准指标','U-Net 可信基线 0.891\nB2 标准划分\nMacro Dice 0.958'],
  ['数据治理缺失\n标注遗失，划分混入\n错配与重复样本','840 份原始 GT 全量找回校验\n语义 QC 剔除 12 个错配\n与 59 个重复','769 个洁净独立样本\n划分冻结，SHA-256 留档'],
  ['泛化能力未知\n训练与测试出现同字，\n难以判断新字表现','character-disjoint 字符隔离划分\n三模型公平比较','未见字 Dice 0.887\n三模型中下降最小：7.2 pp'],
  ['评分不透明\n整体点评打分，\n难向用户解释依据','受限对齐与公开评分公式\n修改建议逐条对应证据','受控扰动、对齐消融\n人工盲评三重验证']
 ];
 tableStyle(tables[4][0],64,143,1152,[52,110,110,110,110],[360,442,350],values,21);
 text(s,'沿用既有采集链路与标签逻辑，持续完善数据资产和评估体系',64,636,1152,35,24,C.accent,true);
}
// 06 Midterm summary
{
 const s=setup(6,C.navy,'中期总览：主链路已经打通',true);
 text(s,'六个环节均已完成，论文与真实场景验证进入收尾阶段',64,123,1152,40,25,C.light);
 const a=['数据恢复','可信基线','模型冻结','结构评分','点评反馈','双端联调'];
 const b=['840 份 GT 校验\n语义 QC 清洗','U-Net 重测\n统一评测框架','SegFormer-B2\n阈值、模型卡归档','受限对齐\n参考结构匹配度','规则驱动建议\nLLM 润色','Web 与 iPad\n真实调用模型'];
 for(let i=0;i<6;i++){
  const x=64+i*194;
  text(s,String(i+1).padStart(2,'0'),x,207,175,46,35,C.green,true);
  text(s,a[i],x,269,177,40,26,C.white,true);
  text(s,b[i],x,321,177,75,20,C.light);
 }
 text(s,'关键数字   截至 2026 年 10 月',64,436,1152,30,20,C.light);
 const vals=['840','769','0.963','2×100','18'];
 const cap=['份原始 GT\n全量找回校验','个 QC-clean\n洁净独立样本','标准划分最佳 Dice\nDeepLabV3+','欧楷与王羲之行书\n课程字（Beta）','组基准实验\n三模型、两划分、三种子'];
 for(let i=0;i<5;i++){
  const x=64+i*237;
  text(s,vals[i],x,494,220,76,55,C.green,true);
  text(s,cap[i],x,581,225,70,20,C.light);
 }
}
// 07 Segmentation and native comparison table
{
 const s=setup(7,C.ice,'核心进展 ① 数据治理与笔画结构分割');
 label(s,'六通道结构表示','横、竖、左斜、右斜、复合五方向与关键点；\n允许交叉区域重叠激活，保留完整笔画。',64,143,570,{titleSize:25,bodySize:21,bodyHeight:60});
 label(s,'769 个洁净独立样本','840 份 GT 校验后，剔除 12 个错配与 59 个重复；\n数据与划分冻结。',64,263,570,{titleSize:25,bodySize:21,bodyHeight:62});
 text(s,'3 模型 × 2 划分 × 3 随机种子，共 18 组训练',64,385,570,32,21,C.body,true);
 const values=[['模型','标准 Dice','未见字 Dice','下降'],['U-Net','0.920','0.826','9.4 pp'],['DeepLabV3+','0.963','0.866','9.7 pp'],['SegFormer-B2','0.958','0.887','7.2 pp']];
 tableStyle(tables[6][0],64,438,568,[43,49,49,49],[184,124,143,117],values,20,3);
 text(s,'三次种子均值；未见字采用 character-disjoint 字符隔离划分',64,643,585,28,16,C.muted);
 pic(7,0,674,142,542,344);
 text(s,'论文 Fig.4：输入、GT 与三模型输出\n交叉、端点稀疏和未见字场景的分割比较',674,499,542,52,18,C.muted);
 text(s,'SegFormer-B2 的未见字表现最佳',674,574,542,38,26,C.accent,true);
 text(s,'精度下降最小，选为线上冻结模型 segformer-b2-v1。',674,622,542,50,20,C.body);
}
// 08 Structural assessment
{
 const s=setup(8,C.mint,'核心进展 ② 结构评分与可解释反馈');
 pic(8,0,64,133,1152,313);
 text(s,'论文 Fig.1：同字参照、笔画解析、受限对齐、空间与方向证据、可审计输出',64,456,1152,29,18,C.muted);
 text(s,'参考结构匹配度 =',64,505,790,35,25,C.accent,true);
 text(s,'0.55×方向 Dice + 0.25×墨迹 IoU + 0.20×关键点 F1',64,548,805,45,26,C.ink,true);
 text(s,'仅允许平移、0.80–1.20 等比缩放、±3° 旋转。\n规则建议逐条对应证据；DeepSeek 润色语言，不能改分或虚构笔顺。',64,603,805,62,20,C.body);
 pic(8,1,956,500,260,182);
}
// 09 Product delivery, remove empty Web screenshot scaffold
{
 const s=setup(9,C.blue,'核心进展 ③ 双平台产品落地');
 text(s,'Web',64,149,500,65,48,C.navy,true);
 text(s,'onestroke.cn',64,222,500,42,30,C.accent,true);
 label(s,'浏览器即用','免安装，适配学校机房与电子白板，\n降低进校门槛。',64,296,500,{bodySize:22,bodyHeight:74});
 label(s,'两门 100 字 Beta 课程','欧阳询楷书、王羲之行书；\n参考字取自 Calli-Tongji 授权字库。',64,423,500,{bodySize:22,bodyHeight:74});
 text(s,'Java 后端已与 GPU 模型服务完成真实联调。',64,568,500,67,24,C.ink,true);
 text(s,'iPad App',663,149,553,65,48,C.navy,true);
 pic(9,0,648,228,283,198);pic(9,1,946,228,283,198);
 text(s,'100 字课程练习包',663,429,265,26,17,C.muted,false,'caption');
 text(s,'练习统计与打卡',962,429,254,26,17,C.muted,false,'caption');
 text(s,'压感笔书写、参考字对照、AI 分析与点评建议，\n形成完整练习流程。',663,480,553,68,22,C.body);
 text(s,'打卡、练习次数与评分趋势沉淀为个人档案。\n参考字、我的书写、分割叠图、对齐示意四图对照。',663,566,553,68,22,C.body);
 text(s,'双端已具备现场演示条件',663,641,553,32,24,C.accent,true);
}
// 10 Results and evidence
{
 const s=setup(10,C.navy,'成果与学术验证',true);
 text(s,'IJDAR 论文在审',64,146,525,47,32,C.green,true);
 text(s,'International Journal on Document Analysis and Recognition',64,207,525,52,19,C.light);
 text(s,'已完成两轮修订：2026-09-05 / 09-17\n主稿 20 页与补充材料',64,271,525,65,21,C.light);
 text(s,'Reference-Conditioned Multi-Label Stroke Structure Analysis for Low-Resource Chinese Calligraphy Practice',64,351,525,84,18,C.light);
 text(s,'软件著作权申请中',64,460,525,39,28,C.green,true);
 text(s,'“一笔成章”汉字书法智能反馈系统\niPad 端与 Web 平台',64,510,525,64,21,C.light);
 text(s,'18 组基准已审计，104 项自动化测试通过',64,608,525,63,23,C.white,true);
 text(s,'E1  受控扰动实验',663,146,553,40,27,C.green,true);
 text(s,'平移罚分约为 0，对齐吸收无关位移。\n结构破坏越严重，评分越低。',663,198,553,76,22,C.light);
 text(s,'E2  对齐消融',663,305,553,40,27,C.green,true);
 text(s,'无关变换罚分降低 30.1 分，结构敏感性提升。\n95% CI [29.5, 30.7]',663,357,553,76,22,C.light);
 text(s,'E3  人工盲评验证',663,464,553,40,27,C.green,true);
 text(s,'3 位盲评者 × 150 对同字实例。\nSpearman ρ=0.297，coverage-aware 修正后 0.429。\n评价者间 ICC(2,k)=0.709。',663,516,553,112,22,C.light);
}
// 11 Business exploration
{
 const s=setup(11,C.mint,'商业化探索：学校进校与个人订阅');
 text(s,'B 端',64,145,540,67,48,C.navy,true);
 text(s,'学校与机构',64,221,540,41,30,C.accent,true);
 text(s,'Web 免安装，适配书法课堂、课后服务与社团。\n机房与电子白板可直接使用。',64,283,530,78,23,C.body);
 text(s,'课程包按学期 / 按校授权。\n教师端查看班级练习数据。',64,381,530,78,23,C.body);
 text(s,'双课程 Beta 已具备进校演示条件。',64,478,530,40,23,C.ink,true);
 text(s,'C 端',663,145,553,67,48,C.navy,true);
 text(s,'个人练习者',663,221,553,41,30,C.accent,true);
 text(s,'iPad App 支持日常自学、纠错与复盘。\n服务书法爱好者和考级人群。',663,283,553,78,23,C.body);
 text(s,'专业练习订阅与课程包内购，\n持续扩充碑帖课程。',663,381,553,78,23,C.body);
 text(s,'全流程可用，具备小范围用户试点条件。',663,478,553,40,23,C.ink,true);
 text(s,'进校扩大覆盖，积累数据与口碑，支持产品持续改进',64,554,1152,42,27,C.accent,true);
 text(s,'两门 Beta 课程已上线；参考库采用 CC-BY-NC-4.0 数据集，产品内标注来源与 Beta 身份。\n下一步推进学校洽谈与真实用户试点，以留存和付费意愿验证商业假设。',64,610,1152,62,20,C.body);
}
// 12 Plan
{
 const s=setup(12,C.blue,'下一步计划：结题与真实场景试点');
 const x=[64,361,658,955],w=[260,260,260,261];
 const date=['2026.11','2026.11–12','2026.12–2027.01','2027 春'];
 const title=['书写体验','真实数据采集','部署收尾','试点与结题'];
 const body=[
  '软件工程与美术专业协作\n优化 Apple Pencil 支持\n\n发挥 4096 级压感能力\n改善毛笔书写体验',
  '采集新书写者数据\n结合真实使用反馈\n持续迭代模型与产品',
  '模型服务迁移至长期部署\n修复 TLS\n完善稳定运行条件',
  '推进学校与真实用户试点\n如华东师大附属中小学\n与幼儿园\n\n归档软著、结题报告\n和演示材料'
 ];
 for(let i=0;i<4;i++){
  text(s,String(i+1).padStart(2,'0'),x[i],150,w[i],68,52,C.accent,true);
  text(s,date[i],x[i],240,w[i],34,23,C.navy,true);
  text(s,title[i],x[i],303,w[i],44,29,C.ink,true);
  text(s,body[i],x[i],369,w[i],220,22,C.body);
 }
 text(s,'结题目标',64,584,1152,34,24,C.accent,true);
 text(s,'实现数据、模型、产品与验证的完整闭环',64,627,1152,44,30,C.ink,true);
}
// 13 Closing
{
 const s=setup(13,C.teal,null,true);
 text(s,'感谢聆听',64,211,760,112,78,C.white,true);
 text(s,'恳请各位老师批评指正',68,348,760,49,31,C.green);
 text(s,'一笔成章   中期汇报   2026.10',68,452,760,36,25,C.light);
 text(s,'汇报人  刘小凡     指导教师  万成城\n华东师范大学 软件工程学院',68,550,760,76,22,C.light);
 pic(13,0,921,226,270,270);
}
await fs.mkdir(path.join(BUILD,'draft-renders'),{recursive:true});
for(let i=0;i<p.slides.items.length;i++){
 const slide=p.slides.items[i];
 await fs.writeFile(path.join(BUILD,'draft-renders',`slide-${i+1}.png`),new Uint8Array(await (await p.export({slide,format:'png',scale:1})).arrayBuffer()));
 await fs.writeFile(path.join(BUILD,'draft-renders',`slide-${i+1}.layout.json`),await (await slide.export({format:'layout'})).text());
}
await (await PresentationFile.exportPptx(p)).save(path.join(BUILD,'candidate.pptx'));
console.log('Draft exported: 13 slides');
