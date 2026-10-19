from pathlib import Path
import zipfile,sys
sys.stdout.reconfigure(encoding='utf-8')
W=Path(__file__).resolve().parent;R=W.parent
out=R/'Lab3_交接材料.zip'
reference=Path(r'C:\Users\18963\.zcode\workspace\default\大二上A\大二上A\02_计算机网络\实验\实验报告及源码\Lab3\10245101445-张荣昊-Lab3.pdf')
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
    z.write(R/'Lab3_交接说明.md','Lab3_交接说明.md')
    for p in sorted(W.rglob('*')):
        if not p.is_file() or p.name.startswith('obs_') or 'qa' in p.relative_to(W).parts:
            continue
        if p.name in ['03_http_capture.png','08_path_ttl_probes_full.png']:continue
        z.write(p,'_lab3_work/'+p.relative_to(W).as_posix())
    for p in [R/'计算机网络实验手册.doc',R/'计算机网络实验报告 Lab XXX.doc',R/'10244602411_刘小凡_Ethernet.docx',reference]:
        z.write(p,'sources/'+p.name)
    for p in (R/'.skills'/'cua-win').rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts:
            z.write(p,'.skills/cua-win/'+p.relative_to(R/'.skills'/'cua-win').as_posix())
    z.writestr('解压说明.txt','先读 Lab3_交接说明.md。原始文件副本在 sources，实测工作在 _lab3_work，本地电脑控制技能在 .skills/cua-win。抓包与主要截图已完成，最终 Word 报告尚未生成。')
with zipfile.ZipFile(out) as z:
    assert z.testzip() is None
    print('ZIP_ENTRIES',len(z.namelist()))
print('SAVED',out,'SIZE_MB',round(out.stat().st_size/1024/1024,2))
