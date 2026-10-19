"""Source-bound IPv4 traceroute using documented Windows ICMP API.
Each TTL has three actual ICMP Echo probes. No route/settings changes.
"""
from pathlib import Path
import ctypes as C, socket, struct, json, sys, subprocess, time
sys.stdout.reconfigure(encoding='utf-8')
W=Path(__file__).resolve().parent
SOURCE='172.31.165.86'; DEST='182.61.200.108'
class Options(C.Structure):
    _fields_=[('Ttl',C.c_ubyte),('Tos',C.c_ubyte),('Flags',C.c_ubyte),('OptionsSize',C.c_ubyte),('OptionsData',C.c_uint32)]
api=C.WinDLL('iphlpapi',use_last_error=True)
api.IcmpCreateFile.restype=C.c_void_p
api.IcmpCloseHandle.argtypes=[C.c_void_p]
api.IcmpSendEcho2Ex.restype=C.c_uint32
api.IcmpSendEcho2Ex.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint32,C.c_uint32,C.c_void_p,C.c_ushort,C.POINTER(Options),C.c_void_p,C.c_uint32,C.c_uint32]
def ipval(ip): return struct.unpack('<I',socket.inet_aton(ip))[0]
def probe(handle,ttl,n):
    payload=C.create_string_buffer(f'LAB3-TTL-{ttl:02d}-PROBE-{n}'.encode().ljust(32,b'.'))
    opts=Options(ttl,0,0,0,0); buf=C.create_string_buffer(2048)
    count=api.IcmpSendEcho2Ex(handle,None,None,None,ipval(SOURCE),ipval(DEST),payload,32,C.byref(opts),buf,2048,900)
    if count:
        addr,status,rtt=struct.unpack('<III',buf.raw[:12])
        return {'address':socket.inet_ntoa(struct.pack('<I',addr)),'status':status,'rtt_ms':rtt,'count':count}
    return {'address':None,'status':C.get_last_error(),'rtt_ms':None,'count':0}
if __name__=='__main__':
    h=api.IcmpCreateFile()
    if h==C.c_void_p(-1).value: raise C.WinError(C.get_last_error())
    maxhop=2 if len(sys.argv)>1 and sys.argv[1]=='test' else 30
    cap=subprocess.Popen([r'C:\Program Files\Wireshark\tshark.exe','-i',r'\Device\NPF_{C59C96C9-17AD-4F4E-ADD7-2E166380D039}','-p','-f','icmp','-a',f'duration:{12 if maxhop==2 else 90}','-w',str(W/'captures'/('Lab3_source_test.pcapng' if maxhop==2 else 'Lab3_Path_WLAN.pcapng'))],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    time.sleep(2)
    rows=[]; lines=[f'IPv4 source-bound traceroute  {SOURCE} -> {DEST}', 'Windows IcmpSendEcho2Ex  |  3 probes per hop  |  timeout 900 ms']
    print('\n'.join(lines),flush=True)
    try:
        for ttl in range(1,maxhop+1):
            probes=[probe(h,ttl,n) for n in range(1,4)]
            rows.append({'hop':ttl,'probes':probes})
            rtts='  '.join('*' if p['rtt_ms'] is None else f"{p['rtt_ms']} ms" for p in probes)
            ips=', '.join(dict.fromkeys(p['address'] for p in probes if p['address'])) or '*'
            line=f'{ttl:2d}  {rtts:25s}  {ips}'
            lines.append(line);print(line,flush=True)
            if any(p['status']==0 and p['address']==DEST for p in probes): break
    finally:
        api.IcmpCloseHandle(h)
        label='source_test' if maxhop==2 else 'source_trace'
        (W/'logs'/f'{label}.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
        (W/'logs'/f'{label}.txt').write_text('\n'.join(lines),encoding='utf-8')
        out,err=cap.communicate(timeout=100)
        (W/'logs'/f'{label}_capture.txt').write_text((out+err).decode('utf-8',errors='replace'),encoding='utf-8')
        print('CAPTURE_EXIT',cap.returncode,flush=True)
