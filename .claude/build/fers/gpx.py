import json
from xml.sax.saxutils import escape as x
D=json.load(open(__import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)),'fers.json')))['spots']
GUIDE='GPS pins are guides only: they get you to the area of a possible {t}, not to a confirmed spot. Confirm on the ground that you are inside every park'
out=['<?xml version="1.0" encoding="UTF-8"?>','<gpx version="1.1" creator="Kentucky Portable Club" xmlns="http://www.topografix.com/GPX/1/1">',
 '<metadata><name>KPC Kentucky POTA 2-fers and 3-fers (guide pins only, do your own research)</name><desc>GPS pins are guides that get you to the area of a possible 2-fer or 3-fer. They are not confirmed activation spots. Park names match the POTA Kentucky park list.</desc></metadata>']
n=0
for d in D:
  names=' + '.join(f'{r} {nm}' for r,nm in zip(d['refs'],d['names']))
  for p in d['points']:
    park=p['what'].lower().startswith(('parking','drive up'))
    sym='Parking Area' if p['what'].lower().startswith('parking') else ('Flag, Blue' if d['type']=='3-fer' else 'Flag, Green')
    g=GUIDE.format(t=d['type'])+(' and within 100 ft of the trail or water.' if any(r in d['refs'] for r in ['US-11181','US-10102','US-4572','US-3791']) else '.')
    desc=f"{names}. {p['what']}. {p.get('note','')} {d['note']}{(' Source: '+d['site']['url']) if d.get('site') else ''} {g} Planning tool only: do your own research."
    out.append(f'<wpt lat="{p["la"]}" lon="{p["lo"]}"><name>{x(d["type"]+" "+" + ".join(d["refs"]))}</name><cmt>{x("Guide pin: "+p["what"])}</cmt><desc>{x(" ".join(desc.split()))}</desc><sym>{sym}</sym></wpt>')
    n+=1
out.append('</gpx>')
open('/home/claude/kentuckyportableclub/kpc-links/KPC_KY_POTA_2fers_3fers.gpx','w').write('\n'.join(out)+'\n')
print(n,'points')
