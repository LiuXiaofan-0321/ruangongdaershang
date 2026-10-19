from pathlib import Path
from docx import Document
from docx.text.paragraph import Paragraph
from docx.table import Table
import fitz,json,sys,zipfile
sys.stdout.reconfigure(encoding='utf-8')
W=Path(__file__).resolve().parent;R=W.parent
d=Document(R/'10244602411_刘小凡_IPv4.docx')
lines=[]
for i,e in enumerate(d.element.body):
    if e.tag.endswith('}p'):
        p=Paragraph(e,d); imgs=p._p.xpath('.//a:blip')
        fmt=p.paragraph_format
        lines.append(f'P{i} [{p.style.name}] {p.text}'+ (' [IMAGE]' if imgs else ''))
        if imgs: lines.append(' IMAGE_WIDTHS '+str([(x.get('cx'),x.get('cy')) for x in e.xpath('.//wp:extent')]))
        if fmt.page_break_before or fmt.keep_with_next:lines.append(f' FLAGS break={fmt.page_break_before} keepnext={fmt.keep_with_next}')
    elif e.tag.endswith('}tbl'):
        t=Table(e,d);lines.append(f'TABLE{i} rows={len(t.rows)} cols={len(t.columns)}')
        lines+=[' | '.join(c.text for c in row.cells) for row in t.rows]
(W/'original_content.txt').write_text('\n'.join(lines),encoding='utf-8')
print('\n'.join(lines))
for s in d.sections: print('PAGE',s.page_width.cm,s.page_height.cm,'MARGINS',s.top_margin.cm,s.bottom_margin.cm,s.left_margin.cm,s.right_margin.cm)
pdfpath=R/'_lab3_work'/'Lab3报告_渲染预览.pdf'
pdf=fitz.open(pdfpath)
pages=W/'original_pages';pages.mkdir(exist_ok=True)
for i,p in enumerate(pdf):
    p.get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(pages/f'page-{i+1}.png')
(W/'original_pdf_text.txt').write_text('\n'.join(f'PAGE {i+1}\n'+p.get_text() for i,p in enumerate(pdf)),encoding='utf-8')
print('ORIGINAL_PDF_PAGES',len(pdf))
with zipfile.ZipFile(R/'10244602411_刘小凡_IPv4.docx') as z:
    for name in z.namelist():
        if name.startswith('word/media/'):
            out=W/'original_media'/Path(name).name;out.parent.mkdir(exist_ok=True);out.write_bytes(z.read(name))
