from pathlib import Path
import subprocess,sys,json
W=Path(__file__).resolve().parent
mode=sys.argv[1]
if mode=='http':
    file='Lab3_HTTP_target.pcapng'; filt='ip.version == 4'
    columns='"No.","%m","Source","%s","Destination","%d","IP ID","%Cus:ip.id","TTL","%Cus:ip.ttl","IP Length","%Cus:ip.len","DF","%Cus:ip.flags.df","MF","%Cus:ip.flags.mf","Offset","%Cus:ip.frag_offset"'
elif mode in ['path','native']:
    file='Lab3_Path_WLAN.pcapng' if mode=='path' else 'Lab3_Traceroute.pcapng';filt='icmp.type == 8'
    columns='"No.","%m","Source","%s","Destination","%d","TTL","%Cus:ip.ttl:1","ICMP Type","%Cus:icmp.type:1","Sequence","%Cus:icmp.seq:1","Info","%i"'
args=[r'C:\Program Files\Wireshark\Wireshark.exe','-r',str(W/'captures'/file),'-Y',filt,'-o',f'gui.column.format:{columns}','-o','ip.check_checksum:TRUE','-o','tcp.reassemble_out_of_order:TRUE']
p=subprocess.Popen(args)
print(json.dumps({'pid':p.pid,'mode':mode,'file':file}))
