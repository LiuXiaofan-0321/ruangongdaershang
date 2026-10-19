from pathlib import Path
import subprocess, struct, csv, json, hashlib, zipfile, sys
from docx import Document
from lxml import etree
sys.stdout.reconfigure(encoding='utf-8')
W=Path(__file__).resolve().parent
TS=r'C:\Program Files\Wireshark\tshark.exe'
fields=['frame.number','frame.time_relative','frame.len','ip.src','ip.dst','ip.hdr_len','ip.len','ip.id','ip.ttl','ip.flags.df','ip.flags.mf','ip.frag_offset','ip.checksum','ip.checksum.status','tcp.stream','tcp.srcport','tcp.dstport','tcp.len','icmp.type','icmp.code','icmp.seq','_ws.col.Info']
def extract(name):
    cmd=[TS,'-r',str(W/'captures'/name),'-o','ip.check_checksum:TRUE','-T','fields','-E','header=y','-E','occurrence=f']
    for f in fields:cmd+=['-e',f]
    out=subprocess.check_output(cmd).decode('utf-8')
    (W/'logs'/(Path(name).stem+'.tsv')).write_text(out,encoding='utf-8')
    return list(csv.DictReader(out.splitlines(),delimiter='\t'))
def raw_frames(name):
    data=(W/'captures'/name).read_bytes(); pos=0; packets=[]
    while pos<len(data):
        typ,n=struct.unpack_from('<II',data,pos)
        if n<12 or pos+n>len(data):raise ValueError('Bad pcapng block')
        if typ==6:
            iface,hi,lo,caplen,wirelen=struct.unpack_from('<IIIII',data,pos+8)
            packets.append(data[pos+28:pos+28+caplen])
        pos+=n
    return packets
allrows=extract('Lab3_HTTP.pcapng')
rows=extract('Lab3_HTTP_target.pcapng')
pathrows=extract('Lab3_Path_WLAN.pcapng')
native=extract('Lab3_Traceroute.pcapng')
packets=raw_frames('Lab3_HTTP_target.pcapng')
chosen=packets[4]; ihl=(chosen[14]&15)*4; header=chosen[14:14+ihl]
words=list(struct.unpack('!10H',header)); accum=[]; s=0
for v in words:s+=v;accum.append(s)
fold=lambda n:(n&65535)+(n>>16)
totalfold=s
while totalfold>>16:totalfold=fold(totalfold)
zero_words=words.copy();zero_words[5]=0
sz=sum(zero_words);fz=sz
while fz>>16:fz=fold(fz)
checksum=(~fz)&65535
assert totalfold==65535 and checksum==words[5]
outgoing=[r for r in rows if r['ip.src']=='172.31.165.86']
incoming=[r for r in rows if r['ip.src']=='182.61.200.108']
probes=[r for r in pathrows if r['icmp.type']=='8' and r['ip.src']=='172.31.165.86' and r['ip.dst']=='182.61.200.108']
ttl_counts={str(i):sum(r['ip.ttl']==str(i) for r in probes) for i in range(1,18)}
assert all(n==3 for n in ttl_counts.values()),ttl_counts
facts={'http_raw_count':len(allrows),'http_target_count':len(rows),'http_outgoing_count':len(outgoing),'http_incoming_count':len(incoming),'http_rows':rows,
 'ip_header_hex':header.hex(' '),'words':[f'{v:04x}' for v in words],'accum':[f'{v:x}' for v in accum], 'sum':f'{s:x}','fold':f'{totalfold:04x}', 'zero_sum':f'{sz:x}','zero_fold':f'{fz:04x}','checksum':f'{checksum:04x}',
 'path_count':len(pathrows),'path_probe_count':len(probes),'ttl_counts':ttl_counts,'path_time_exceeded':sum(r['icmp.type']=='11' for r in pathrows),'path_echo_reply':sum(r['icmp.type']=='0' for r in pathrows),
 'native_probe_ttls':sorted({r['ip.ttl'] for r in native if r['icmp.type']=='8'}),
 'first_time_exceeded':next(r for r in pathrows if r['icmp.type']=='11'), 'last_echo_reply':next(r for r in reversed(pathrows) if r['icmp.type']=='0' and r['ip.src']=='182.61.200.108')}
(W/'facts.json').write_text(json.dumps(facts,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in facts.items() if k!='http_rows'},ensure_ascii=False,indent=2))
doc=Document(W/'template.docx')
print('TEMPLATE_DETAIL')
for i,p in enumerate(doc.paragraphs):
    if p.text:
        print(i,p.text,p.style.name,'pPr',etree.tostring(p._p.pPr,encoding='unicode').split('>')[1:] if p._p.pPr is not None else None)
        print([(r.text,r.font.name,r.font.size.pt if r.font.size else None,r.bold) for r in p.runs])
inventory=[]
with zipfile.ZipFile(W/'template.docx') as z:
    for name in z.namelist():
        v=z.read(name);inventory.append({'name':name,'size':len(v),'sha256':hashlib.sha256(v).hexdigest()})
(W/'template_parts.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
