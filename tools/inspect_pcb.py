"""Print footprint courtyard and pad bounds for placement review (KiCad Python)."""
from pathlib import Path
import json
import pcbnew as p
root=Path(__file__).resolve().parents[1]
b=p.LoadBoard(str(root/'hardware/kicad/picolino-cpc.kicad_pcb'))
data={}
for f in b.GetFootprints():
    boxes=[g.GetBoundingBox() for g in f.GraphicalItems() if g.GetLayer()==p.F_CrtYd]
    if not boxes:boxes=[f.GetBoundingBox(False,False)]
    data[f.GetReference()]={'pos':[p.ToMM(f.GetPosition().x),p.ToMM(f.GetPosition().y)],
        'bounds':[p.ToMM(min(x.GetLeft() for x in boxes)),p.ToMM(min(x.GetTop() for x in boxes)),p.ToMM(max(x.GetRight() for x in boxes)),p.ToMM(max(x.GetBottom() for x in boxes))]}
(root/'hardware/kicad/checks/placement-bounds.json').write_text(json.dumps(data,indent=2)+'\n')
print('Wrote placement-bounds.json')
