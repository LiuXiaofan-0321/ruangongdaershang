from pathlib import Path
import fitz
root=Path(__file__).parent
out=root/'二轮渲染'
out.mkdir(exist_ok=True)
with (root/'页面检查.txt').open('w',encoding='utf-8') as f:
    for name in ['报告','指南']:
        d=fitz.open(root/(name+'检查.pdf'))
        print(name,len(d))
        (out/name).mkdir(exist_ok=True)
        for i,p in enumerate(d):
            p.get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(out/name/f'page-{i+1}.png')
            f.write(name+' PAGE '+str(i+1)+'\n'+p.get_text()+'\n')
