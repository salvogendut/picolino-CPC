#!/usr/bin/env python3
"""Generate Picolino's editable KiCad project from an explicit circuit manifest.

Generation overwrites generated CAD. Preserve/review manual CAD edits first.
Use host Python for --libraries/--schematic; KiCad 10 Python for --pcb.
"""
import argparse
import copy
import csv
import hashlib
import json
import math
from pathlib import Path
import shutil
import uuid
import xml.etree.ElementTree as ET
from pcb_sexpr import Atom, child, children, dumps, loads

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'hardware/kicad'
STEM = 'picolino-cpc'
LIB = 'Picolino'
OUTLINE = (100,100,250,220)
q = lambda x: json.dumps(str(x),ensure_ascii=False)
uid = lambda x: str(uuid.uuid5(uuid.NAMESPACE_URL,'picolino-cpc-reva/'+x))
IFACE = json.loads((ROOT/'hardware/interfaces.json').read_text())
PARTS = {}
SHEETS = {1:('bus-power','CPC bus, address decoding and power'),
          2:('pico-rom','Pico 2 ROM interface and level translation'),
          3:('ethernet-mouse','W5100S Ethernet and PIC PS/2 mouse'),
          4:('rtc','RP5C01 RTC and CR2032 battery backup')}
NOTES = {}
def net(n):
    if n=='VCC':return 'BOARD_5V'
    if n.startswith('/'):return n[1:]+'_N'
    return n.replace('3.3','3V3').replace('USBD+','MOUSE_CLK').replace('USBD-','MOUSE_DATA')
def part(ref,symbol,value,fp,nets,sheet,sch,pcb,note=''):
    PARTS[ref]=dict(symbol=symbol,value=value,footprint=fp,nets={str(k):v for k,v in nets.items()},
        sheet=sheet,sch=[round(round(x/1.27)*1.27,4) for x in sch],pcb=pcb,note=note)
DIP=lambda pins:f'Package_DIP:DIP-{pins}_W7.62mm_Socket_LongPads'
HDR='Connector_PinHeader_2.54mm:'
RES='Resistor_SMD:R_0805_2012Metric'
CAP='Capacitor_SMD:C_0805_2012Metric'
def resistor(i,value,a,b,sheet,sch,pcb,note=''):
    part('R'+str(i),'R',value,RES,{1:a,2:b},sheet,sch,pcb,note)
def capacitor(i,value,a,sheet,sch,pcb,note='',b='GND'):
    part('C'+str(i),'C',value,CAP,{1:a,2:b},sheet,sch,pcb,note)

# Sheet 1: verified expansion contact numbering, full address decode, supply selection.
cpc={p:net(n) for p,n in IFACE['cpc']['pins'].items()};cpc['27']='CPC_5V'
part('J1','CPC_BUS','CPC 50-pin expansion','Connector_IDC:IDC-Header_2x25_P2.54mm_Vertical',cpc,1,(65,108),(143,209,90),
     'CPC/Mother X4 contact numbers; short 50-way cable. Pin 1 marked on silk.')
gal={i+1:f'A{i}' for i in range(10)}
gal.update({11:'A1X',12:'GND',13:'IORQ_N',14:'RD_N',15:'RTCCS_N',16:'W5CS_N',17:'PINT_N',
    18:'RTCAS',19:'RTCWR_N',20:'RTCRD_N',21:'CHLED_N',22:'CHCS_N',23:'WR_N',24:'BOARD_5V'})
part('U2','GAL20V8','GAL20V8B / picolino.jed',DIP(24),gal,1,(185,91),(157,164,0),'Program firmware/gal/picolino.pld before fitting.')
hct={1:'A10',2:'A11',4:'A12',5:'A13',6:'A10_13',7:'GND',8:'A1X',9:'A10_13',10:'A14',12:'A15',13:'A15',14:'BOARD_5V'}
part('U3','HCT21','74HCT21',DIP(14),hct,1,(295,84),(182,184,90))
ch={p:net(n) for p,n in IFACE['ch376']['pins'].items() if n!='NC'};ch['5']='USB_5V'
part('J2','CH376_HEADER','CH376 parallel / short ribbon','Connector_IDC:IDC-Header_2x08_P2.54mm_Vertical',ch,1,(295,157),(113,132,0),
     'CPC_PICOROM J2 pinout. External reference CH376 module; pin 7 unused.')
part('J3','Conn_01x02','EXT regulated 5V',HDR+'PinHeader_1x02_P2.54mm_Vertical',{1:'EXT_5V',2:'GND'},1,(62,220),(114,160,90))
part('JP1','Conn_01x03','POWER: 1 CPC / 2 BOARD / 3 EXT',HDR+'PinHeader_1x03_P2.54mm_Vertical',
     {1:'CPC_5V',2:'BOARD_5V',3:'EXT_5V'},1,(164,209),(125,165,0),'Fit ONE shunt only; use 2-3 for external board power.')
part('F1','Polyfuse','USB 500mA hold','Fuse:Fuse_1206_3216Metric',{1:'BOARD_5V',2:'USB_5V'},1,(245,215),(114,148,0),
     'Example Bourns MF-NSMF050-2; validate inrush and voltage drop with chosen USB drive.')
part('D1','D_Schottky','1N5817','Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal',{1:'PICO_VSYS',2:'BOARD_5V'},1,(340,215),(173,144,0),
     'Cathode/band at Pico VSYS; prevents Pico USB feeding board 5V.')
resistor(1,'1k','BOARD_5V','CHLED_A',1,(180,151),(135,159,0))
part('D2','LED','USB activity','LED_THT:LED_D3.0mm',{1:'CHLED_N',2:'CHLED_A'},1,(219,151),(132,150,0))
for i,a,sch,pcb in [(1,'BOARD_5V',(116,249),(166,163,0)),(2,'BOARD_5V',(165,249),(180,180,0)),(3,'USB_5V',(214,249),(114,153,0))]:capacitor(i,'100nF',a,1,sch,pcb)
part('C4','C_Polarized','100uF / 10V','Capacitor_THT:CP_Radial_D6.3mm_P2.50mm',{1:'USB_5V',2:'GND'},1,(264,249),(125,151,0))
part('C5','C_Polarized','47uF / 10V','Capacitor_THT:CP_Radial_D5.0mm_P2.00mm',{1:'BOARD_5V',2:'GND'},1,(313,249),(133,169,0))
for i,n in enumerate(['GND','CPC_5V','EXT_5V','BOARD_5V','USB_5V','PICO_VSYS'],1):
    part(f'#FLG{i}','PWR_FLAG','PWR_FLAG',None,{1:n},1,(30+i*53,278),None)
NOTES[1]=[(20,15,'PICOLINO CPC / REV A0 — BUS, DECODE & POWER'),
 (130,35,'FE80/FE81 USB | FD20-FD23 Ethernet | FD10 mouse\nFD14 RTC data (low nibble), FD15 RTC index'),
 (23,166,'J1 pin 40 BUSRESET differs from pin 41 RESET.\nJ2 uses the reference parallel CH376 module on a short cable.\nIts USB host socket is on the module, not this carrier.'),
 (20,187,'JP1 selects the board supply; never bridge all three pins.\nExternal input: regulated 5V only; common CPC ground. Power CPC before external board supply.\nCheck power budget before selecting CPC power; external 5V is preferred for USB-drive bring-up.')]

# Sheet 2: all 26 exposed GPIOs, input monitoring independent of ROM enable.
pico={str(p['module_pin']):('P_'+net(p['signal']) if p['signal'] not in ('ROM_LATCH','RESET_PULLDOWN') else p['signal']) for p in IFACE['pico2']['gpio']}
pico.update({str(p):'GND' for p in IFACE['pico2']['ground_pins']});pico.update({'36':'PICO_3V3','39':'PICO_VSYS'})
part('U1','Pico2','Raspberry Pi Pico 2','Local:Pico2_Socketed',pico,2,(327,102),(198,105,0),'Two 1x20 sockets, 17.78mm row spacing; USB faces top edge.')
groups=[[f'A{i}' for i in range(8)],[f'A{i}' for i in range(8,14)]+['A15'],[f'D{i}' for i in range(8)],['ROMEN_N','IORQ_N','WR_N','BUSRESET_N']]
for i,signals in enumerate(groups):
    pins={10:'GND',19:'DATA_OE_N' if i==2 else 'INPUT_OE_N',20:'PICO_3V3'}
    for channel,n in enumerate(signals,1):pins[channel+1]=n;pins[19-channel]='P_'+n
    part('U'+str(4+i),'CB3T3245','SN74CB3T3245DW','Package_SO:SOIC-20W_7.5x12.8mm_P1.27mm',pins,2,
        (73+i%2*116,75+i//2*77),[(174,113,0),(174,135,0),(192,165,0),(214,165,0)][i],
        'Exact CB3T level-translating part at 3.3V; not HC245 or CB3Q.')
    capacitor(6+i,'100nF','PICO_3V3',2,(39+i*70,250),[(174,103,0),(174,125,0),(192,155,0),(214,155,0)][i])
part('JP2','Conn_02x02_Odd_Even','ROM ENABLE: fit BOTH shunts',HDR+'PinHeader_2x02_P2.54mm_Vertical',
     {1:'INPUT_OE_N',2:'DATA_OE_N',3:'BOARD_5V',4:'ROMDIS'},2,(328,181),(232,162,0),
     'Both open: internal CPC ROMs and input-only monitor. Both fitted: RP2350 ROM firmware required.')
part('Q1','2N7002','2N7002','Package_TO_SOT_SMD:SOT-23',{1:'CPC_5V',2:'GND',3:'INPUT_OE_N'},2,(77,205),(190,145,0),
     'CPC power gates all bus switches; Pico USB alone cannot enable them.')
resistor(31,'100k','CPC_5V','GND',2,(21,205),(185,145,90),'Gate discharge when the CPC expansion cable is disconnected.')
resistor(2,'10k','INPUT_OE_N','PICO_3V3',2,(145,199),(190,139,0))
resistor(3,'10k','DATA_OE_N','PICO_3V3',2,(196,199),(230,156,0))
resistor(4,'10k','ROMDIS','GND',2,(247,199),(240,166,0))
for i,a,sch,pcb in [(3,'P_A13',(70,280),(197,181,90)),(4,'P_WR_N',(145,280),(202,181,90)),(5,'P_IORQ_N',(220,280),(207,181,90))]:
    part('D'+str(i),'D_Schottky','BAT43','Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal',{1:'ROM_LATCH',2:a},2,sch,pcb,'Band at ROM_LATCH; active-low capture when all three inputs are low.')
resistor(5,'2.2k','ROM_LATCH','GND',2,(299,250),(211,180,0))
part('D6','D_Schottky','BAT43','Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal',{1:'RESET_PULLDOWN',2:'P_BUSRESET_N'},2,(356,250),(230,178,90),'Band at GPIO28; firmware may only pull reset low or release it.')
resistor(6,'10k','P_ROMEN_N','PICO_3V3',2,(360,211),(227,149,0))
NOTES[2]=[(20,15,'PICO 2 / RP2350 — ROM INTERFACE'),(20,32,'3.3V B-side signals have P_ prefix. All CPC-facing GPIOs use level translation.\nInput switches enable when CPC 5V is present; JP2 separately isolates the data bus and controls ROMDIS.'),
 (284,145,'Native RP2350 monitor: keep JP2 open.\nROM-serving firmware and timing remain to be validated.'),
 (20,234,'U4-U7 each require local 100nF. GPIO0/1 are address inputs: UART stdio must stay disabled.')]

# Sheet 3: original Cyboard parallel Ethernet conditioning and PIC-to-buffer map.
w={p:net(n) for p,n in IFACE['w5100s']['pins'].items() if p not in ['23','24']};w['29']='W5CS_N'
part('U8','W5100S_Module','W5100S reference module','Local:W5100S_Cyboard',w,3,(73,100),(127,125,180),
     'Two 1x16 sockets, 25.4mm row spacing. Reference module has a 3.3V regulator. RJ45 faces top edge.')
for i in range(8):resistor(7+i,'470',f'D{i}',f'W51D{i}',3,(155+(i%2)*58,54+(i//2)*28),(147,107+i*4,0))
for i,n,sch,pcb in [(7,'RD',(169,176),(148,148,90)),(8,'WR',(229,176),(153,148,90))]:
    part('D'+str(i),'D','1N4148','Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal',{1:n+'_N',2:'W51'+n+'_N'},3,sch,pcb,'Cyboard read/write conditioning; cathode at CPC strobe.')
pic={p:net(n) for p,n in IFACE['mouse_pic']['pins'].items()}
buf={p:net(n) for p,n in IFACE['mouse_buffer']['pins'].items()}
part('U9','PIC16F84A','PIC16F84A / Cyboard HEX',DIP(18),pic,3,(323,81),(223,107,0),'Retain original PIC firmware, config fuses and CPC PHI clock.')
part('U10','HCT244','74HCT244',DIP(20),buf,3,(322,180),(223,133,0))
part('J4','USB_Mouse','PS/2 MOUSE only','Connector_USB:USB_A_TE_292303-7_Horizontal',
    {1:'BOARD_5V',2:'MOUSE_DATA',3:'MOUSE_CLK',4:'GND',5:'GND'},3,(76,221),(240,108,0),
    'USB-shaped socket carries PS/2 protocol; only a PS/2-capable mouse works.')
resistor(15,'10k','MOUSE_CLK','BOARD_5V',3,(176,222),(238,124,0))
resistor(16,'10k','MOUSE_DATA','BOARD_5V',3,(237,222),(243,124,0))
for i,sch,pcb in [(10,(153,268),(137,153,0)),(11,(214,268),(220,104,90)),(12,(275,268),(221,158,0))]:capacitor(i,'100nF','BOARD_5V',3,sch,pcb)
NOTES[3]=[(20,15,'ETHERNET & MOUSE — CYBOARD-COMPATIBLE INTERFACES'),
 (20,32,'W5100S parallel registers: FD20-FD23. PIC mouse read: FD10.\nW5100S module pins 23/24 are its 3.3V outputs and are left unconnected.'),
 (20,157,'U8 pin numbering and geometry copied from Cyboard module footprint.\nDo not fit a SPI-only WIZ810Sio module.'),
 (286,245,'PIC RA0 = mouse clock; RA1 = mouse data.\nPIC RA2 carries response D0; retain buffer mapping.\nThis is not a USB-HID mouse host.')]

# Sheet 4: original (non-A) RP5C01 circuit, stable index latch and backup inhibit.
rtc={p:net(n) for p,n in IFACE['rp5c01']['proposed_connections'].items()}
part('U11','RP5C01','RP5C01 (original, DIP-18)',DIP(18),rtc,4,(194,88),(138,171,0))
latch={1:'GND',2:'RTC_A0',3:'D0',4:'D1',5:'RTC_A1',6:'RTC_A2',7:'D2',8:'D3',9:'RTC_A3',10:'GND',
       11:'RTCAS',13:'GND',14:'GND',17:'GND',18:'GND',20:'BOARD_5V'}
part('U12','HCT373','74HCT373',DIP(20),latch,4,(68,85),(117,180,0),'LE high only on FD15 write; closes at end of write. Unused data inputs grounded.')
part('U13','MAX690A','MAX690AESA+','Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',
    {1:'RTC_BACKUP_VCC',2:'BOARD_5V',3:'GND',4:'GND',7:'RTC_POWER_GOOD',8:'VBAT'},4,(313,75),(151,189,0),
    'Pin 7 /RESET is HIGH when main power is valid, directly enabling RTC CS. WDI left open to disable watchdog.')
part('BT1','Battery_Cell','CR2032 / Keystone 103','Battery:BatteryHolder_Keystone_103_1x20mm',
    {1:'VBAT',2:'GND'},4,(334,131),(112,205,90),'Single CR2032, positive face up. No charging circuit.')
part('#FLG7','PWR_FLAG','PWR_FLAG',None,{1:'VBAT'},4,(383,132),None)
resistor(17,'100k','RTC_POWER_GOOD','GND',4,(270,128),(151,198,0),'Defines disabled state below supervisor operating voltage.')
part('Y1','Crystal','32.768kHz / AB38T','Crystal:Crystal_C38-LF_D3.0mm_L8.0mm_Vertical',
    {1:'RTC_OSCIN',2:'RTC_XOUT'},4,(155,181),(149,167,0),'AB38T-32.768KHZ, 12.5pF load; gently form leads from 0.8mm to 1.9mm pitch. Local pads enlarged to 0.7mm drill. Calibrate on PCB.')
resistor(18,'100k','RTC_XOUT','RTC_OSCOUT',4,(217,181),(146,174,90))
part('CV1','C_Trim','30pF trim / KKT330TR','Capacitor_SMD:C_Trimmer_Murata_TZC3',
    {1:'RTC_OSCIN',2:'GND'},4,(88,181),(151,161,0),'Kingtronics KKT330TR: minimum setting <=8pF, maximum >=28.5pF; TZC3-compatible geometry. Calibrate from ALARM output; verify trim range.')
capacitor(13,'30pF C0G','RTC_XOUT',4,(155,224),(151,174,0))
capacitor(14,'56pF C0G','RTC_OSCOUT',4,(217,224),(144,180,0))
capacitor(15,'100nF','RTC_BACKUP_VCC',4,(282,181),(145,191,0))
capacitor(16,'100nF','BOARD_5V',4,(337,181),(121,179,0))
capacitor(17,'100nF','BOARD_5V',4,(337,224),(154,184,0))
resistor(19,'10k','RTC_ALARM_TEST','BOARD_5V',4,(282,224),(137,196,0))
part('TP1','TestPoint','RTC ALARM / calibration','TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm',
    {1:'RTC_ALARM_TEST'},4,(382,222),(139,201,0))
# Ground bias on RTC inputs/data avoids floating CMOS inputs in backup.
for i,n in enumerate(['RTCCS_N','RTCRD_N','RTCWR_N',*[f'RTC_A{j}' for j in range(4)],*[f'D{j}' for j in range(4)]]):
    resistor(20+i,'220k',n,'GND',4,(28+i*33,264),(160+(i%6)*5,196+(i//6)*6,90),'RTC backup input bias; no pull-up to battery supply.')
NOTES[4]=[(20,15,'RP5C01 RTC — 4-BIT REGISTERS, CR2032 BACKUP'),
 (20,33,'U11 pin 1 /CS: GAL decode. Pin 2 CS: main-power-good (LOW in backup).\nFD15 selects an index; FD14 reads/writes the low nibble. This differs from DS12887 software.'),
 (20,132,'Oscillator follows original Ricoh RP5C01 databook page 3-6, including 56pF on OSCOUT.\nCrystal load and trimmer require calibration. Keep oscillator components together, away from digital clocks.\nMAX690A powers only U11 from CR2032. WDI is intentionally open; PFI grounded; PFO unused.'),
 (20,239,'R20-R30 bias RTC inputs during backup. Measure battery current, time retention and supply switching on the prototype.')]

for i,xy in enumerate([(104,104),(246,104),(104,216),(246,216)],1):
    part(f'H{i}','MountingHole','M3 NPTH','MountingHole:MountingHole_3.2mm_M3',{},1,(20+i*80,294),(*xy,0))

# Reviewed placements use the full courtyard, not just the pad origin.
for ref,position in {
 'J1':(148,213,90),'J2':(108,153,0),'J3':(108,183,90),'J4':(231,108,180),
 'JP1':(132,180,0),'JP2':(234,190,0),'BT1':(112,206,0),
 'U2':(168,164,0),'U9':(230,126,0),'U10':(233,153,0),'U12':(119,169,0),
 'F1':(108,191,0),'C1':(180,163,90),'C2':(184,172,0),'C3':(110,179,0),
 'C5':(132,161,0),'C9':(211,175,0),'C10':(107,120,90),'C11':(245,136,0),
 'C12':(246,153,90),'C13':(156,178,0),'C14':(151,182,0),'C15':(150,166,0),
 'C16':(132,167,0),'C17':(158,188,0),'CV1':(160,172,0),'Y1':(151,173,0),
 'R1':(141,158,0),'R3':(237,184,0),'R4':(243,190,0),'R5':(213,192,0),'R6':(226,155,0),'R15':(222,121,0),
 'R16':(227,121,0),'R18':(151,178,0),'R19':(141,198,0),'R31':(184,137,0),
 'D1':(173,149,0),'D3':(198,195,90),'D4':(203,195,90),'D5':(208,195,90),'D6':(226,180,90),
 'TP1':(144,202,0),
}.items(): PARTS[ref]['pcb']=position
for i in range(1,7):PARTS[f'#FLG{i}']['sch']=(381,80+i*25.4)
for i in range(1,5):PARTS[f'H{i}']['sch']=(40+(i-1)*60,271.78)
for i in range(11):PARTS[f'R{20+i}']['sch']=(27.94+i*25.4,264.16)
PARTS['C5']['sch']=(313,240)
PARTS['TP1']['sch']=(364,222)
NOTES[2]=[(x,228 if 'U4-U7' in message else y,message) for x,y,message in NOTES[2]]
# Match the selected TE connector's SH-numbered shield mounting tabs.
PARTS['J4']['nets']['SH']=PARTS['J4']['nets'].pop('5')
for p in PARTS.values():p['sch']=[round(round(x/1.27)*1.27,4) for x in p['sch']]

def custom_symbol(name,pins,width=35.56):
    n=math.ceil(len(pins)/2);height=(n+1)*2.54
    out=[f'(symbol {q(name)} (pin_names (offset 0.8)) (in_bom yes) (on_board yes)',
         f'(property "Reference" "U" (at 0 {height/2+5.08} 0) (effects (font (size 1.27 1.27))))',
         f'(property "Value" {q(name)} (at 0 {height/2+2.54} 0) (effects (font (size 1.27 1.27))))',
         '(property "Footprint" "" (at 0 0 0) (hide yes) (effects (font (size 1.27 1.27))))',
         f'(symbol "{name}_0_1" (rectangle (start {-width/2} {height/2}) (end {width/2} {-height/2}) (stroke (width 0.254) (type default)) (fill (type background))))',f'(symbol "{name}_1_1"']
    for i,(number,label,kind) in enumerate(pins):
        left=i<n;row=i if left else i-n;x=-width/2-5.08 if left else width/2+5.08;y=height/2-(row+1)*2.54
        out.append(f'(pin {kind} line (at {x} {y:.4f} {0 if left else 180}) (length 5.08) (name {q(label)} (effects (font (size 1.1 1.1)))) (number {q(number)} (effects (font (size 1.1 1.1)))))')
    return loads('\n'.join(out)+'))')

def device_pins(count,names,inputs=(),outputs=(),bidir=(),power_in=(),power_out=(),nc=(),tri=()):
    types={str(p):kind for kind,seq in [('input',inputs),('output',outputs),('bidirectional',bidir),('power_in',power_in),('power_out',power_out),('no_connect',nc),('tri_state',tri)] for p in seq}
    return [(i,names.get(str(i),names.get(i,'NC')),types.get(str(i),'passive')) for i in range(1,count+1)]

def libraries(source):
    folder=DEST/'libraries';folder.mkdir(parents=True,exist_ok=True);pretty=folder/f'{LIB}.pretty';pretty.mkdir(exist_ok=True)
    models=folder/'3dmodels';models.mkdir(exist_ok=True)
    requests={'Device':['R','C','C_Polarized','C_Trim','Crystal','D','D_Schottky','LED','Battery_Cell','Polyfuse'],
      'Connector_Generic':['Conn_01x02','Conn_01x03','Conn_02x02_Odd_Even'],
      'Mechanical':['MountingHole'], 'Connector':['TestPoint'],'power':['PWR_FLAG']}
    symbols=[];provenance=[]
    for lib,names in requests.items():
        all_symbols=children(loads((source/'symbols'/f'{lib}.kicad_sym').read_text()),'symbol')
        for name in names:
            symbol=copy.deepcopy(next(x for x in all_symbols if x[1]==name))
            assert child(symbol,'extends') is None,name
            symbols.append(symbol)
    pico_names={str(p['module_pin']):f'GPIO{p["gpio"]}' for p in IFACE['pico2']['gpio']}
    pico_names.update({str(p):'GND' for p in IFACE['pico2']['ground_pins']});pico_names.update({'30':'RUN','35':'ADC_VREF','36':'3V3_OUT','37':'3V3_EN','39':'VSYS','40':'VBUS'})
    definitions={
      'CPC_BUS':device_pins(50,{str(i):cpc.get(str(i),'UNUSED') for i in range(1,51)}),
      'CH376_HEADER':device_pins(16,{str(i):ch.get(str(i),'NC') for i in range(1,17)}),
      'GAL20V8':device_pins(24,gal,inputs=[*range(1,12),13,14,23],outputs=range(15,23),power_in=[12,24]),
      'HCT21':device_pins(14,hct,inputs=[1,2,4,5,9,10,12,13],outputs=[6,8],power_in=[7,14],nc=[3,11]),
      'Pico2':device_pins(40,pico_names,bidir=[int(p['module_pin']) for p in IFACE['pico2']['gpio']],inputs=[30,37],power_in=[39,40],power_out=[36]),
      'CB3T3245':device_pins(20,{1:'NC',10:'GND',19:'OE_N',20:'VCC',**{i+1:f'A{i}' for i in range(1,9)},**{19-i:f'B{i}' for i in range(1,9)}},inputs=[19],bidir=[*range(2,10),*range(11,19)],power_in=[10,20],nc=[1]),
      'W5100S_Module':device_pins(32,{**w,'23':'3V3_OUT_2','24':'3V3_OUT_1'},inputs=[1,2,12,28,29,30,31,32],bidir=range(3,11),power_in=[21,22,25,26,27],power_out=[23,24]),
      'PIC16F84A':device_pins(18,{**{str(i):f'RA{i-17}' for i in [17,18]},1:'RA2',2:'RA3',3:'RA4',4:'MCLR_N',5:'VSS',**{i:f'RB{i-6}' for i in range(6,14)},14:'VDD',15:'OSC2',16:'OSC1'},inputs=[4,16],outputs=[15],bidir=[1,2,3,17,18,*range(6,14)],power_in=[5,14]),
      'HCT244':device_pins(20,buf,inputs=[1,2,4,6,8,11,13,15,17,19],tri=[3,5,7,9,12,14,16,18],power_in=[10,20]),
      'USB_Mouse':[(1,'VBUS','passive'),(2,'D- / PS2 DATA','passive'),(3,'D+ / PS2 CLK','passive'),(4,'GND','passive'),('SH','SHIELD','passive')],
      'HCT373':device_pins(20,{1:'OE_N',2:'Q0',3:'D0',4:'D1',5:'Q1',6:'Q2',7:'D2',8:'D3',9:'Q3',10:'GND',11:'LE',12:'Q4',13:'D4',14:'D5',15:'Q5',16:'Q6',17:'D6',18:'D7',19:'Q7',20:'VCC'},inputs=[1,3,4,7,8,11,13,14,17,18],tri=[2,5,6,9,12,15,16,19],power_in=[10,20]),
      'RP5C01':device_pins(18,IFACE['rp5c01']['pins'],inputs=[1,2,3,4,5,6,7,8,10,16],outputs=[15,17],bidir=range(11,15),power_in=[9,18]),
      'MAX690A':device_pins(8,{1:'VOUT',2:'VCC',3:'GND',4:'PFI',5:'PFO_N',6:'WDI',7:'RESET_N',8:'VBATT'},inputs=[4,6],outputs=[5,7],power_in=[2,3,8],power_out=[1]),
      '2N7002':device_pins(3,{1:'G',2:'S',3:'D'},inputs=[1])}
    symbols += [custom_symbol(n,p) for n,p in definitions.items()]
    (folder/f'{LIB}.kicad_sym').write_text('(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor")\n'+'\n'.join(dumps(s) for s in symbols)+'\n)\n')
    for fp in sorted({p['footprint'] for p in PARTS.values() if p['footprint']}):
        lib,name=fp.split(':')
        if name=='W5100S_Cyboard':continue
        if name=='Pico2_Socketed':lib='Module';original='RaspberryPi_Pico_Common_THT'
        else:original=name
        path=source/'footprints'/f'{lib}.pretty'/f'{original}.kicad_mod'
        footprint=loads(path.read_text());footprint[1]=name
        if name=='C_Trimmer_Murata_TZC3':
            for pad in children(footprint,'pad'):
                child(pad,'at')[1:]=[Atom('-1.925' if pad[1]=='1' else '1.925'),Atom('0')]
                child(pad,'size')[1:]=[Atom('1.3'),Atom('1.4')]
            child(footprint,'descr')[1]+='; modified pads for Kingtronics KKT330TR manufacturer land pattern.'
        if name=='Crystal_C38-LF_D3.0mm_L8.0mm_Vertical':
            for pad in children(footprint,'pad'):
                child(pad,'size')[1:]=[Atom('1.2'),Atom('1.2')]
                child(pad,'drill')[1:]=[Atom('0.7')]
            child(footprint,'descr')[1]+='; modified: 0.7mm drills, 1.2mm pads for AB38T formed leads; model envelope approximate.'
        if name=='Pico2_Socketed':
            footprint[:]=[n for n in footprint if not(isinstance(n,list) and (n[0] in ['model','group'] or n[0]=='zone' or n[0]=='fp_text' and n[2] in ['Possible Antenna','Keep Out']))]
            footprint.append(loads('(model "${KIPRJMOD}/libraries/3dmodels/rpi_pico2.step" (offset (xyz 8.89 -24.13 11.0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))'))
            socket=source/'3dmodels/Module.3dshapes/RaspberryPi_Pico_PinSockets_H8.50mm.step'
            shutil.copy2(socket,models/socket.name)
            footprint.append(loads(f'(model "${{KIPRJMOD}}/libraries/3dmodels/{socket.name}" (offset (xyz 8.89 -24.13 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))'))
            header=source/'3dmodels/Connector_PinHeader_2.54mm.3dshapes/PinHeader_1x20_P2.54mm_Vertical.step'
            shutil.copy2(header,models/header.name)
            for x in [0,17.78]:
                footprint.append(loads(f'(model "${{KIPRJMOD}}/libraries/3dmodels/{header.name}" (offset (xyz {x} 0 11)) (scale (xyz 1 1 1)) (rotate (xyz 0 180 0)))'))
            child(footprint,'descr')[1]='Pico 2, two 1x20 sockets, 17.78mm row spacing; official RP2350 module model.'
        else:
            for m in children(footprint,'model'):
                relative=m[1].split('}/')[-1];original_model=source/'3dmodels'/relative
                if original_model.exists():
                    local=relative.replace('/','_');shutil.copy2(original_model,models/local);m[1]='${KIPRJMOD}/libraries/3dmodels/'+local
            if name.startswith('DIP-') and '_Socket_' in name:
                chip=name.split('_Socket_')[0]+'.step'
                shutil.copy2(source/'3dmodels/Package_DIP.3dshapes'/chip,models/chip)
                footprint.append(loads(f'(model "${{KIPRJMOD}}/libraries/3dmodels/{chip}" (offset (xyz 0 0 3.5)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))'))
        (pretty/f'{name}.kicad_mod').write_text(dumps(footprint)+'\n')
        provenance.append(dict(local=name,source=f'{lib}:{original}',sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    # Geometry is translated directly from the selected Cyboard EAGLE package.
    package=ET.parse(ROOT/'hardware/w5100-reference.xml').getroot()
    lines=['(footprint "W5100S_Cyboard" (version 20241229) (generator "pcbnew") (layer "F.Cu") (attr through_hole)',
      '(property "Reference" "REF**" (at 0 -22 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
      '(property "Value" "W5100S" (at 0 25 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))']
    for pad in package.findall('pad'):
        num=pad.get('name');x=float(pad.get('x'));y=-float(pad.get('y'))
        lines.append(f'(pad {q(num)} thru_hole {"rect" if num=="1" else "circle"} (at {x} {y}) (size 1.9 1.9) (drill 1.016) (layers "*.Cu" "*.Mask"))')
    for layer,width,x0,y0,x1,y1 in [('F.CrtYd',0.05,-14.5,-20.8,14.5,23.6),('F.SilkS',0.12,-13.9,-20.2,13.9,22.9),('F.Fab',0.1,-13.808,-20.158,13.808,22.86)]:
        lines.append(f'(fp_rect (start {x0} {y0}) (end {x1} {y1}) (stroke (width {width}) (type solid)) (fill none) (layer {q(layer)}))')
    lines += ['(fp_text user "1" (at -11 -18.9) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
      '(fp_text user "RJ45" (at 0 20) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))',
      '(model "${KIPRJMOD}/libraries/3dmodels/w5100s-envelope.wrl" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))',')']
    (pretty/'W5100S_Cyboard.kicad_mod').write_text('\n'.join(lines)+'\n')
    provenance.append(dict(local='W5100S_Cyboard',source='Cyboard EAGLE W5100S-NETWORK-MODULE',sha256=hashlib.sha256((ROOT/'hardware/w5100-reference.xml').read_bytes()).hexdigest()))
    (folder/'footprint-sources.json').write_text(json.dumps(provenance,indent=2)+'\n')
    for table,kind,suffix in [('sym','KiCad','kicad_sym'),('fp','KiCad','pretty')]:
        (DEST/f'{table}-lib-table').write_text(f'({table}_lib_table (version 7) (lib (name "{LIB}") (type "{kind}") (uri "${{KIPRJMOD}}/libraries/{LIB}.{suffix}") (options "") (descr "Picolino local library")))\n')

def schematic():
    symbols=children(loads((DEST/'libraries'/f'{LIB}.kicad_sym').read_text()),'symbol')
    for page,(slug,title) in SHEETS.items():
        used={p['symbol'] for p in PARTS.values() if p['sheet']==page};cache=[]
        for symbol in symbols:
            if symbol[1] in used:s=copy.deepcopy(symbol);s[1]=LIB+':'+s[1];cache.append(dumps(s))
        out=[f'(kicad_sch (version 20250114) (generator "eeschema") (uuid {q(uid(slug))}) (paper "A3")',
          f'(title_block (title {q("Picolino CPC / "+slug)}) (date "2026-10-07") (rev "A0") (comment 1 "Prototype: verify timing and power on hardware"))',
          '(lib_symbols\n'+'\n'.join(cache)+')']
        for ref,p in PARTS.items():
            if p['sheet']!=page:continue
            x,y=p['sch'];symbol=next(s for s in symbols if s[1]==p['symbol']);bom='no' if ref.startswith(('#','H')) else 'yes'
            instance=[f'(symbol (lib_id {q(LIB+":"+p["symbol"])}) (at {x} {y} 0) (unit 1) (in_bom {bom}) (on_board {"yes" if p["footprint"] else "no"}) (dnp no) (uuid {q(uid(ref))})']
            props={z[1]:z for z in children(symbol,'property')}
            for name,val in [('Reference',ref),('Value',p['value']),('Footprint',LIB+':'+p['footprint'].split(':')[1] if p['footprint'] else '')]:
                at=child(props[name],'at') if name in props else [None,0,0,0];px=x+float(at[1]);py=y-float(at[2])
                if p['symbol'] in ['R','C','C_Trim','C_Polarized','Polyfuse','Battery_Cell'] and name in ['Reference','Value']:
                    px=x+2.54;py=y+(-1.27 if name=='Reference' else 1.27)
                instance.append(f'(property {q(name)} {q(val)} (at {px:.4f} {py:.4f} 0) {"(hide yes)" if name=="Footprint" else ""} (effects (font (size 1.1 1.1)) (justify left)))')
            handled=set()
            for unit in children(symbol,'symbol'):
                for pin in children(unit,'pin'):
                    num=child(pin,'number')[1];instance.append(f'(pin {q(num)} (uuid {q(uid(ref+"."+num))}))')
                    px,py,angle=map(float,child(pin,'at')[1:]);px=round(x+px,5);py=round(y-py,5)
                    if (px,py) in handled:continue
                    handled.add((px,py));n=p['nets'].get(num)
                    if n:
                        ex=round(px-math.cos(math.radians(angle))*5.08,5);ey=round(py+math.sin(math.radians(angle))*5.08,5)
                        out.append(f'(wire (pts (xy {px} {py}) (xy {ex} {ey})) (stroke (width 0) (type default)) (uuid {q(uid(ref+num+"wire"))}))')
                        # Global labels bridge the four functional sheets.
                        la=0 if angle==0 else 180 if angle==180 else angle
                        out.append(f'(global_label {q(n)} (shape bidirectional) (at {ex} {ey} {la}) (effects (font (size 1 1)) (justify {"right" if angle==0 else "left"})) (uuid {q(uid(ref+num+"label"))}))')
                    else:out.append(f'(no_connect (at {px} {py}) (uuid {q(uid(ref+num+"nc"))}))')
            instance.append(f'(instances (project {q(STEM)} (path {q("/"+uid("root")+"/"+uid("sheet-"+slug))} (reference {q(ref)}) (unit 1)))))');out.extend(instance)
        for i,(x,y,message) in enumerate(NOTES[page]):out.append(f'(text {q(message)} (at {x} {y} 0) (effects (font (size {1.5 if i==0 else 1.2} {1.5 if i==0 else 1.2})) (justify left top)) (uuid {q(uid(slug+"note"+str(i)))}))')
        out.append('(embedded_fonts no))');(DEST/f'{slug}.kicad_sch').write_text('\n'.join(out)+'\n')
    root=[f'(kicad_sch (version 20250114) (generator "eeschema") (uuid {q(uid("root"))}) (paper "A4")',
      '(title_block (title "Picolino CPC — Pico 2 multifunction expansion") (date "2026-10-07") (rev "A0")) (lib_symbols)']
    for i,(slug,title) in SHEETS.items():
        x=30+(i-1)%2*130;y=50+(i-1)//2*65
        root.append(f'(sheet (at {x} {y}) (size 105 40) (stroke (width 0.1524) (type default)) (fill (color 0 0 0 0)) (uuid {q(uid("sheet-"+slug))}) (property "Sheetname" {q(title)} (at {x} {y-2} 0) (effects (font (size 1.27 1.27)) (justify left bottom))) (property "Sheetfile" {q(slug+".kicad_sch")} (at {x} {y+42} 0) (effects (font (size 1.27 1.27)) (justify left top))) (instances (project {q(STEM)} (path {q("/"+uid("root"))} (page {q(i+1)})))))')
    cover="PICOLINO CPC / REV A0\nPico 2 ROM / CH376 USB / W5100S Ethernet / PIC mouse / RP5C01 RTC\nPrototype design — bench validation and RP2350 ROM firmware required"
    root.append(f'(text {q(cover)} (at 30 22 0) (effects (font (size 1.5 1.5)) (justify left top)) (uuid {q(uid("cover-note"))})) (embedded_fonts no))')
    (DEST/f'{STEM}.kicad_sch').write_text('\n'.join(root)+'\n')
    rules=dict(min_clearance=0.2,min_track_width=0.2,min_via_diameter=0.6,min_through_hole_diameter=0.3,min_via_annular_width=0.15,min_hole_clearance=0.25,min_copper_edge_clearance=0.5,min_silk_clearance=0.15,min_text_height=0.8,min_text_thickness=0.12)
    default=dict(name='Default',clearance=0.2,track_width=0.25,via_diameter=0.7,via_drill=0.35,microvia_diameter=0.3,microvia_drill=0.1,diff_pair_width=0.25,diff_pair_gap=0.25,diff_pair_via_gap=0.25)
    project={'meta':{'filename':f'{STEM}.kicad_pro','version':3},'board':{'design_settings':{'meta':{'version':2},'rules':rules,'track_widths':[0,0.25,0.4,0.6,1.0],'via_dimensions':[{'diameter':0.7,'drill':0.35}]}},
      'net_settings':{'meta':{'version':5},'classes':[default,dict(default,name='Power',track_width=0.8)],'netclass_patterns':[{'netclass':'Power','pattern':n} for n in ['BOARD_5V','CPC_5V','EXT_5V','USB_5V','PICO_VSYS','PICO_3V3']]}}
    (DEST/f'{STEM}.kicad_pro').write_text(json.dumps(project,indent=2)+'\n')
    (DEST/'circuit-manifest.json').write_text(json.dumps(PARTS,indent=2)+'\n')
    with (DEST/'bom.csv').open('w') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(['Reference','Value','Footprint','Assembly note'])
        for ref,p in PARTS.items():
            if p['footprint']:w.writerow([ref,p['value'],LIB+':'+p['footprint'].split(':')[1],p['note']])

def pcb():
    import pcbnew as p
    project=DEST/f'{STEM}.kicad_pro';saved=project.read_bytes();board=p.BOARD();board.SetCopperLayerCount(2);board.GetDesignSettings().SetBoardThickness(p.FromMM(1.6))
    board.GetTitleBlock().SetTitle('Picolino CPC / Pico 2 combined expansion');board.GetTitleBlock().SetRevision('A0')
    point=lambda x,y:p.VECTOR2I(p.FromMM(x),p.FromMM(y));nets={};padnets={}
    for node in ET.parse(DEST/'checks/netlist.xml').getroot().findall('./nets/net'):
        name=node.get('name');n=p.NETINFO_ITEM(board,name);board.Add(n);nets[name]=n
        for pad in node.findall('node'):padnets[(pad.get('ref'),pad.get('pin'))]=name
    for ref,part in PARTS.items():
        if not part['footprint']:continue
        name=part['footprint'].split(':')[1];fp=p.FootprintLoad(str(DEST/'libraries'/f'{LIB}.pretty'),name);assert fp is not None,name
        fp.SetFPID(p.LIB_ID(LIB,name));fp.SetReference(ref);fp.SetValue(part['value']);slug=SHEETS[part['sheet']][0]
        fp.SetPath(p.KIID_PATH('/'+uid('root')+'/'+uid('sheet-'+slug)+'/'+uid(ref)));board.Add(fp)
        x,y,angle=part['pcb'];fp.SetPosition(point(x,y));fp.SetOrientationDegrees(angle);fp.Value().SetVisible(False)
        fp.Reference().SetTextSize(point(0.8,0.8));fp.Reference().SetTextThickness(p.FromMM(0.12))
        ref_positions={'U8':(109,111),'U11':(134,170)}
        if ref in ref_positions:
            fp.Reference().SetPosition(point(*ref_positions[ref]));fp.Reference().SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))
        if ref.startswith('H'):fp.Reference().SetVisible(False);fp.SetAttributes(fp.GetAttributes()|p.FP_EXCLUDE_FROM_POS_FILES)
        if ref=='TP1':fp.SetAttributes(fp.GetAttributes() & ~p.FP_EXCLUDE_FROM_BOM)
        for pad in fp.Pads():
            n=padnets.get((ref,pad.GetNumber()))
            if n:pad.SetNet(nets[n])
    x0,y0,x1,y1=OUTLINE
    for a,b in [((x0,y0),(x1,y0)),((x1,y0),(x1,y1)),((x1,y1),(x0,y1)),((x0,y1),(x0,y0))]:
        e=p.PCB_SHAPE();e.SetShape(p.SHAPE_T_SEGMENT);e.SetStart(point(*a));e.SetEnd(point(*b));e.SetLayer(p.Edge_Cuts);e.SetWidth(p.FromMM(0.05));board.Add(e)
    def label(text,x,y,size=1,layer=p.F_SilkS):
        t=p.PCB_TEXT(board);t.SetText(text);t.SetPosition(point(x,y));t.SetTextSize(point(size,size));t.SetTextThickness(p.FromMM(0.15));t.SetLayer(layer)
        if layer==p.B_SilkS:t.SetMirrored(True)
        board.Add(t)
    for t,x,y,s in [('PICOLINO CPC',228,205,1.6),('PICO 2 / REV A0',229,209,0.9),('CPC EXPANSION',176,218.3,0.8),('CH376',121,157,1),('EXT 5V',108,187,0.8),('+',104.5,183,1),('GND',115,183,0.8),('POWER',132,190,0.8),('ROM ENABLE',235,198,0.9),('BOTH SHUNTS',235,201,0.8),('PS/2 MOUSE',236,121,0.8),('CR2032',128,219,0.8),('RP5C01',142,166,0.9)]:label(t,x,y,s)
    label('PICOLINO CPC / Rev A0\nPico 2 expansion prototype\n150 x 120mm / 2 layers\nJP1: select ONE power source\nJP2: BOTH shunts enable ROM\nSee README before power-on',174,124,1,layer=p.B_SilkS)
    for i in range(1,5):
        x,y,_=PARTS[f'H{i}']['pcb'];z=p.ZONE(board);z.SetIsRuleArea(True);z.SetLayerSet(p.LSET.AllCuMask(2));z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(True);z.SetDoNotAllowZoneFills(True);z.SetDoNotAllowPads(False);z.SetZoneName(f'H{i} screw clearance');poly=z.Outline();poly.NewOutline()
        for dx,dy in [(-3.5,-3.5),(3.5,-3.5),(3.5,3.5),(-3.5,3.5)]:poly.Append(p.FromMM(x+dx),p.FromMM(y+dy))
        board.Add(z)
    p.SaveBoard(str(DEST/f'{STEM}.kicad_pcb'),board);project.write_bytes(saved)
    print('Generated PCB placement; routing and independent DRC are required.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--libraries',type=Path);parser.add_argument('--schematic',action='store_true');parser.add_argument('--pcb',action='store_true');args=parser.parse_args()
    DEST.mkdir(parents=True,exist_ok=True);(DEST/'checks').mkdir(exist_ok=True)
    if args.libraries:libraries(args.libraries)
    if args.schematic:schematic()
    if args.pcb:pcb()
