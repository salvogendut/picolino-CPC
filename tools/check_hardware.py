#!/usr/bin/env python3
"""Independent netlist/pad checks against firmware and imported source pin maps."""
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
from pcb_sexpr import loads, child, children
from galasm_source import parse

ROOT=Path(__file__).resolve().parents[1]
CAD=ROOT/'hardware/kicad'
interface=json.loads((ROOT/'hardware/interfaces.json').read_text())
nets={}
for n in ET.parse(CAD/'checks/netlist.xml').findall('./nets/net'):
    for node in n.findall('node'):nets[(node.get('ref'),node.get('pin'))]=n.get('name')

def normalize(name):
    if name=='VCC':return 'BOARD_5V'
    if name.startswith('/'):return name[1:]+'_N'
    return name.replace('USBD+','MOUSE_CLK').replace('USBD-','MOUSE_DATA')
def expect(ref,pin,name):
    assert nets[(ref,str(pin))]==name,(ref,pin,nets.get((ref,str(pin))),name)
def unused(ref,pin):
    assert nets[(ref,str(pin))].startswith('unconnected-'),(ref,pin,nets[(ref,str(pin))])

for pin,n in interface['cpc']['pins'].items():expect('J1',pin,'CPC_5V' if pin=='27' else normalize(n))
for block,ref in [('mouse_pic','U9'),('mouse_buffer','U10')]:
    for pin,n in interface[block]['pins'].items():expect(ref,pin,normalize(n))
for pin,n in interface['w5100s']['pins'].items():
    if pin in ('23','24'):unused('U8',pin)
    else:expect('U8',pin,'W5CS_N' if pin=='29' else normalize(n))
for pin,n in interface['ch376']['pins'].items():
    if n=='NC':unused('J2',pin)
    else:expect('J2',pin,'USB_5V' if pin=='5' else normalize(n))
for p in interface['pico2']['gpio']:
    n=p['signal'];expect('U1',p['module_pin'],n if n in ('ROM_LATCH','RESET_PULLDOWN') else 'P_'+normalize(n))
for pin in interface['pico2']['ground_pins']:expect('U1',pin,'GND')
expect('U1',36,'PICO_3V3');expect('U1',39,'PICO_VSYS');unused('U1',40)
pins,_=parse(ROOT/'firmware/gal/picolino.pld')
for pin,(n,inverted) in pins.items():
    expect('U2',pin,('IORQ' if n=='IOREQ' else n)+('_N' if inverted else ''))
expect('U2',12,'GND');expect('U2',24,'BOARD_5V')
for pin,n in interface['rp5c01']['proposed_connections'].items():expect('U11',pin,normalize(n))
for pin,n in {1:'RTC_BACKUP_VCC',2:'BOARD_5V',3:'GND',4:'GND',7:'RTC_POWER_GOOD',8:'VBAT'}.items():expect('U13',pin,n)
unused('U13',5);unused('U13',6)
expect('BT1',1,'VBAT');expect('BT1',2,'GND')
for pin,n in {1:'GND',2:'RTC_A0',3:'D0',4:'D1',5:'RTC_A1',6:'RTC_A2',7:'D2',8:'D3',9:'RTC_A3',10:'GND',11:'RTCAS',13:'GND',14:'GND',17:'GND',18:'GND',20:'BOARD_5V'}.items():expect('U12',pin,n)
for pin in [12,15,16,19]:unused('U12',pin)
for ref,connections in {
 'Q1':{1:'CPC_5V',2:'GND',3:'INPUT_OE_N'},
 'JP1':{1:'CPC_5V',2:'BOARD_5V',3:'EXT_5V'},
 'JP2':{1:'INPUT_OE_N',2:'DATA_OE_N',3:'BOARD_5V',4:'ROMDIS'},
 'D1':{1:'PICO_VSYS',2:'BOARD_5V'},'D6':{1:'RESET_PULLDOWN',2:'P_BUSRESET_N'},
 'J4':{1:'BOARD_5V',2:'MOUSE_DATA',3:'MOUSE_CLK',4:'GND','SH':'GND'},
 'Y1':{1:'RTC_OSCIN',2:'RTC_XOUT'},'R18':{1:'RTC_XOUT',2:'RTC_OSCOUT'},
 'CV1':{1:'RTC_OSCIN',2:'GND'},'C13':{1:'RTC_XOUT',2:'GND'},'C14':{1:'RTC_OSCOUT',2:'GND'},
}.items():
    for pin,n in connections.items():expect(ref,pin,n)
for ref,group in [('U4',[f'A{i}' for i in range(8)]),('U5',[f'A{i}' for i in range(8,14)]+['A15']),('U6',[f'D{i}' for i in range(8)]),('U7',['ROMEN_N','IORQ_N','WR_N','BUSRESET_N'])]:
    for c,n in enumerate(group,1):expect(ref,c+1,n);expect(ref,19-c,'P_'+n)
    expect(ref,10,'GND');expect(ref,20,'PICO_3V3');expect(ref,19,'DATA_OE_N' if ref=='U6' else 'INPUT_OE_N')
fp=loads((CAD/'libraries/Picolino.pretty/W5100S_Cyboard.kicad_mod').read_text())
pad_positions={p[1]:tuple(map(float,child(p,'at')[1:3])) for p in children(fp,'pad')}
for p in ET.parse(ROOT/'hardware/w5100-reference.xml').getroot().findall('pad'):
    assert pad_positions[p.get('name')]==(float(p.get('x')),-float(p.get('y')))
fp=loads((CAD/'libraries/Picolino.pretty/Pico2_Socketed.kicad_mod').read_text())
pad_positions={p[1]:tuple(map(float,child(p,'at')[1:3])) for p in children(fp,'pad')}
for pin,xy in {'1':(0,0),'20':(0,48.26),'21':(17.78,48.26),'40':(17.78,0)}.items():assert pad_positions[pin]==xy
print('PASS: CPC/Pico/PIC/W5100S/CH376 pin maps, GAL firmware pins, RTC/supervisor/oscillator topology, reset polarity and module pad geometry')
