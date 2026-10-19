from pathlib import Path
import urllib.request,json,concurrent.futures
W=Path(__file__).resolve().parent
ips=['202.120.95.246','101.4.116.61','219.224.103.65','182.61.255.32']
def fetch(ip):
    url='https://rdap.apnic.net/ip/'+ip
    try:
        with urllib.request.urlopen(url,timeout=20) as r:data=json.load(r)
        (W/'logs'/('rdap_'+ip+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
        desc=[x for remark in data.get('remarks',[]) for x in remark.get('description',[])]
        return {'ip':ip,'name':data.get('name'),'start':data.get('startAddress'),'end':data.get('endAddress'),'country':data.get('country'),'description':desc}
    except Exception as e:return {'ip':ip,'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as e:rows=list(e.map(fetch,ips))
(W/'logs'/'rdap_summary.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(rows,ensure_ascii=False,indent=2))
