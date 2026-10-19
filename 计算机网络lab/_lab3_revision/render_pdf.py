from pathlib import Path
import fitz,sys,json
from PIL import Image,ImageDraw
sys.stdout.reconfigure(encoding='utf-8')
W=Path(__file__).resolve().parent
name=sys.argv[1]
pdf=fitz.open(W/(name+'.pdf')); out=W/(name+'_pages');out.mkdir(exist_ok=True)
texts=[];stats=[]
for i,p in enumerate(pdf):
    p.get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(out/f'page-{i+1}.png')
    texts.append(f'PAGE {i+1}\n{p.get_text()}')
    blocks=p.get_text('blocks');body=[b for b in blocks if 65<b[1]<780 and b[3]<785]
    stats.append({'page':i+1,'last_body_y':max((b[3] for b in body),default=0),'image_count':len(p.get_images()),'words':len(p.get_text().split()),'text_start':p.get_text()[:140]})
(W/(name+'_text.txt')).write_text('\n'.join(texts),encoding='utf-8')
(W/(name+'_stats.json')).write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf-8')
cols=3;thumbw=380;thumbh=570;rows=(len(pdf)+cols-1)//cols
sheet=Image.new('RGB',(cols*thumbw,rows*thumbh),'#dddddd');dr=ImageDraw.Draw(sheet)
for i in range(len(pdf)):
    im=Image.open(out/f'page-{i+1}.png');im.thumbnail((thumbw-12,thumbh-28))
    x=(i%cols)*thumbw+(thumbw-im.width)//2;y=(i//cols)*thumbh+22
    sheet.paste(im,(x,y));dr.text(((i%cols)*thumbw+10,(i//cols)*thumbh+5),str(i+1),fill='black')
sheet.save(W/(name+'_contact.png'))
print('PAGES',len(pdf));print(json.dumps(stats,ensure_ascii=False,indent=2))
