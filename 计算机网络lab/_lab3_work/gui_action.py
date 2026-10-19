"""One observed GUI action, then a focused real screenshot, via cua-win."""
from pathlib import Path
import sys, argparse, json, time
W=Path(__file__).resolve().parent
sys.path.insert(0,str(W.parent/'.skills'/'cua-win'/'scripts'))
import cua
p=argparse.ArgumentParser()
p.add_argument('action',choices=['observe','click','type','key','drag','resize'])
p.add_argument('--hwnd',type=int,default=6361670)
p.add_argument('--x',type=int);p.add_argument('--y',type=int)
p.add_argument('--to-x',type=int);p.add_argument('--to-y',type=int)
p.add_argument('--double',action='store_true')
p.add_argument('--text');p.add_argument('--keys',nargs='+')
p.add_argument('--out',default='obs.png');p.add_argument('--crop')
p.add_argument('--width',type=int,default=2000)
a=p.parse_args()
if not cua.focus(a.hwnd): raise RuntimeError('Target focus failed; no action taken')
assert cua.user32.GetForegroundWindow()==a.hwnd
if a.action=='click': cua.cmd_click(argparse.Namespace(hwnd=a.hwnd,x=a.x,y=a.y,button='left',double=a.double))
elif a.action=='type': cua.cmd_type(argparse.Namespace(hwnd=a.hwnd,text=a.text,method='clipboard',clear=True,interval=.012))
elif a.action=='key': cua.cmd_key(argparse.Namespace(hwnd=a.hwnd,keys=a.keys))
elif a.action=='drag':
    cua.user32.SetCursorPos(a.x,a.y)
    cua.user32.mouse_event(0x0002,0,0,0,0)
    for step in range(1,16):
        cua.user32.SetCursorPos(round(a.x+(a.to_x-a.x)*step/15),round(a.y+(a.to_y-a.y)*step/15))
        time.sleep(.02)
    cua.user32.mouse_event(0x0004,0,0,0,0)
    print(json.dumps({'drag':[a.x,a.y,a.to_x,a.to_y]}))
elif a.action=='resize':
    cua.user32.ShowWindow(a.hwnd,9)
    if not cua.user32.SetWindowPos(a.hwnd,0,a.x,a.y,a.to_x,a.to_y,0x0040):
        raise RuntimeError('Window resize failed')
    print(json.dumps({'window_rect':cua.window_rect(a.hwnd)}))
time.sleep(.35)
fg=int(cua.user32.GetForegroundWindow())
if fg != a.hwnd:
    print(json.dumps({'focus_changed_to':fg,'title':cua.window_title(fg)}))
    # A newly opened modal belongs to the observed app; do not redirect inputs.
    target=fg
else: target=a.hwnd
if a.crop:
    cua.cmd_shot(argparse.Namespace(hwnd=None,crop=a.crop,out=str(W/'evidence'/a.out),max_width=a.width))
else:
    cua.cmd_shot(argparse.Namespace(hwnd=target,crop=None,out=str(W/'evidence'/a.out),max_width=a.width))
