#!/usr/bin/env python3
"""Write a simplified W5100S reference-module envelope, not a vendor fit model."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
out=['#VRML V2.0 utf8','# Picolino W5100S envelope: pad spacing/outline from Cyboard; heights indicative.']
def box(x,y,z,dx,dy,dz,color):
    out.append('Transform { translation %s children [ Shape { appearance Appearance { material Material { diffuseColor %s } } geometry Box { size %s } } ] }' %
        (' '.join(str(v/2.54) for v in (x,y,z)),' '.join(map(str,color)),' '.join(str(v/2.54) for v in (dx,dy,dz))))
# Model coordinates use positive Y opposite the footprint coordinate system.
box(0,-1.25,10.5,27.616,42.856,1.6,(0.04,0.28,0.11))
for x in [-12.7,12.7]:
    box(x,0,4.2,2.5,40.64,8.4,(0.09,0.09,0.09))
    for i in range(16):box(x,-19.05+i*2.54,8.4,0.64,0.64,4.8,(0.75,0.65,0.32))
box(0.635,-15.24,17.4,13.97,15.24,12.2,(0.68,0.7,0.72))
box(0.635,-22.89,17.4,10.5,0.2,7,(0.055,0.055,0.055))
box(-1.27,3.81,12.0,8,8,1.4,(0.08,0.08,0.08))
folder=ROOT/'hardware/kicad/libraries/3dmodels';folder.mkdir(parents=True,exist_ok=True)
(folder/'w5100s-envelope.wrl').write_text('\n'.join(out)+'\n')
