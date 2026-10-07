#!/usr/bin/env python3
"""Apply documented post-route corrections without regenerating placement.

Host Python; preserve UUIDs and project constraints. Always refill and run DRC
afterward. This does not waive any violations.
"""
from collections import Counter
import copy
from pcb_design import DEST, STEM
from pcb_sexpr import Atom, child, children, dumps, loads

filename=DEST/f'{STEM}.kicad_pcb'
board=loads(filename.read_text());changed=Counter()
for track in list(children(board,'segment')):
    if float(child(track,'width')[1])<0.2:
        child(track,'width')[1]=Atom('0.2');changed['narrow tracks restored to 0.20mm']+=1
    if child(track,'net')[1]=='RESET_N':
        for key in ['start','end']:
            xy=child(track,key)
            if float(xy[2])<100.8:xy[2]=Atom('100.8')
    if child(track,'uuid')[1]=='ea7b74a4-d209-4f54-8bed-47423f6ce390':
        board.remove(track);changed['unconnected 0.06mm router stub removed']+=1
for fp in children(board,'footprint'):
    ref=next(x[2] for x in children(fp,'property') if x[1]=='Reference')
    # Local solid connections replace incomplete thermal spokes at these four
    # through-hole grounds. Other pads retain ordinary thermal reliefs.
    direct={'J1':'2','U2':'12','C4':'2','C5':'2'}
    if ref in direct:
        pad=next(x for x in children(fp,'pad') if x[1]==direct[ref])
        value=child(pad,'zone_connect')
        if value is None:pad.append([Atom('zone_connect'),Atom('2')])
        else:value[1]=Atom('2')
    if ref=='U1':
        source=loads((DEST/'libraries/Picolino.pretty/Pico2_Socketed.kicad_mod').read_text())
        fp[:]=[x for x in fp if not(isinstance(x,list) and x[0]=='model')]
        fp.extend(copy.deepcopy(children(source,'model')))
filename.write_text(dumps(board)+'\n')
print(dict(changed))
