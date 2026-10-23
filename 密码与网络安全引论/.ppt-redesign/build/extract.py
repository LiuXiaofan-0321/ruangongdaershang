import zipfile,xml.etree.ElementTree as E,json,pathlib
src=pathlib.Path('C:/Users/Steven/Desktop/一笔成章 · 中期汇报 v1.1.pptx')
root=pathlib.Path('C:/courses/密码与网络安全引论/.ppt-redesign')
n={'a':'http://schemas.openxmlformats.org/drawingml/2006/main','p':'http://schemas.openxmlformats.org/presentationml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
data=[]
with zipfile.ZipFile(src) as z:
 for f in z.namelist():
  if f.startswith('ppt/media/') and f.endswith('.png'):
   (root/'assets'/pathlib.Path(f).name).write_bytes(z.read(f))
 for i in range(1,14):
  r=E.fromstring(z.read(f'ppt/slides/slide{i}.xml'))
  rels=E.fromstring(z.read(f'ppt/slides/_rels/slide{i}.xml.rels'))
  rm={x.get('Id'):x.get('Target') for x in rels}
  item={'slide':i,'texts':[x.text for x in r.findall('.//a:t',n)],'images':[rm[b.get('{'+n['r']+'}embed')] for b in r.findall('.//a:blip',n)],'tables':[]}
  for table in r.findall('.//a:tbl',n):
   item['tables'].append([[''.join(x.itertext()) for x in []]])
   item['tables'][-1]=[['\n'.join(''.join(t.itertext()) for t in c.findall('.//a:t',n)) for c in row.findall('a:tc',n)] for row in table.findall('a:tr',n)]
  data.append(item)
(root/'source-content.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps([{'slide':s['slide'],'images':s['images']} for s in data],ensure_ascii=True))
