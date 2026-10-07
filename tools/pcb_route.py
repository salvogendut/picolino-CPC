#!/usr/bin/env python3
"""KiCad 10 local Specctra export/import, preserving project constraints."""
import argparse
from pathlib import Path
import pcbnew as p
from pcb_design import DEST, STEM, OUTLINE
from pcb_sexpr import Atom, child, children, dumps, loads

parser=argparse.ArgumentParser(description=__doc__)
mode=parser.add_mutually_exclusive_group(required=True)
mode.add_argument('--export',type=Path)
mode.add_argument('--import-session',type=Path)
a=parser.parse_args()
filename=DEST/f'{STEM}.kicad_pcb'
project=filename.with_suffix('.kicad_pro');settings=project.read_bytes()
board=p.LoadBoard(str(filename))
if a.export:
    default=board.GetDesignSettings().m_NetSettings.GetDefaultNetclass()
    default.SetTrackWidth(p.FromMM(0.25));default.SetClearance(p.FromMM(0.25))
    default.SetViaDiameter(p.FromMM(0.7));default.SetViaDrill(p.FromMM(0.35))
    board.SynchronizeNetsAndNetClasses(False)
    if not p.ExportSpecctraDSN(board,str(a.export.resolve())):raise RuntimeError('DSN export failed')
    data=loads(a.export.read_text().replace('(string_quote ")','(string_quote quote_character)'))
    network=child(data,'network')
    power={'BOARD_5V','CPC_5V','EXT_5V','USB_5V','PICO_VSYS','PICO_3V3'}
    for cls in children(network,'class'):
        cls[:]=[x for i,x in enumerate(cls) if i<2 or isinstance(x,list) or x not in power]
        if not any(not isinstance(x,list) for x in cls[2:]):network.remove(cls)
    existing=next(iter(children(network,'class')))
    network.append([Atom('class'),'Power',*sorted(power),child(existing,'circuit')[:],
        [Atom('rule'),[Atom('width'),Atom('800')],[Atom('clearance'),Atom('250')]]])
    a.export.write_text(dumps(data).replace('(string_quote quote_character)','(string_quote ")')+'\n')
    print('Exported 0.25mm signal / 0.80mm power / 0.25mm clearance routing input.')
else:
    if not p.ImportSpecctraSES(board,str(a.import_session.resolve())):raise RuntimeError('SES import failed')
    for layer in [p.F_Cu,p.B_Cu]:
        z=p.ZONE(board);z.SetLayer(layer);z.SetNetCode(board.FindNet('GND').GetNetCode())
        z.SetLocalClearance(p.FromMM(0.25));z.SetThermalReliefGap(p.FromMM(0.25));z.SetThermalReliefSpokeWidth(p.FromMM(0.3))
        z.SetPadConnection(p.ZONE_CONNECTION_THERMAL);z.SetMinThickness(p.FromMM(0.2));poly=z.Outline();poly.NewOutline()
        x0,y0,x1,y1=OUTLINE
        for x,y in [(x0+.5,y0+.5),(x1-.5,y0+.5),(x1-.5,y1-.5),(x0+.5,y1-.5)]:poly.Append(p.FromMM(x),p.FromMM(y))
        board.Add(z)
    p.SaveBoard(str(filename),board);project.write_bytes(settings)
    print('Imported routing and added ground pours. Run DRC with refill and parity.')
