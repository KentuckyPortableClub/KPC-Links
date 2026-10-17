"""Builds KPC_Kentucky_POTA_2fers_3fers_Guide.pdf from fers.json (same folder).
usage (repo root): python3 .claude/build/fers/guide.py"""
import json,os,datetime
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit, ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
HERE=os.path.dirname(os.path.abspath(__file__)); REPO=os.path.abspath(os.path.join(HERE,'..','..','..'))
FD='/usr/share/fonts/truetype/crosextra/'
for n,f in [('C','Carlito-Regular'),('CB','Carlito-Bold'),('CI','Carlito-Italic'),('S','Caladea-Bold')]: pdfmetrics.registerFont(TTFont(n,FD+f+'.ttf'))
DATA=json.load(open(os.path.join(HERE,'fers.json')))
SP=DATA['spots']
W,H=612,792; M=36; CW=W-2*M
def hx(h): h=h.lstrip('#'); return tuple(int(h[i:i+2],16)/255 for i in (0,2,4))
BG,GOLD,GREEN,DARK,FOOT,INK,MUTED,LINE,SOFT=map(hx,['f6f1e4','d5a63a','1d5a3a','173b2b','5c786c','1b1f1a','5d6358','dcd4bf','f3dfa6'])
QC={'A':hx('1d5a3a'),'B':hx('2f6c9a'),'C':hx('a8431f')}
LOGO=ImageReader(os.path.join(REPO,'KPC-logo.png'))
POTA=lambda r:'https://pota.app/#/park/'+r
GM=lambda la,lo:f'https://www.google.com/maps/search/?api=1&query={la:.5f},{lo:.5f}'
DIR=lambda la,lo:f'https://www.google.com/maps/dir/?api=1&destination={la:.5f},{lo:.5f}&travelmode=driving'
def sec(d):
  if d['type']=='3-fer': return 'three'
  if 'Historic Trail site' in d['how'] or 'auto tour route' in d['how']: return 'hist'
  if 'Water Route bank' in d['how']: return 'water'
  if 'riverbank' in d['how'].lower(): return 'river'
  if 'through the park' in d['how']: return 'trail'
  return 'shared'
SECS=[('three','3-Fers','Three POTA parks at once','Trails through two overlapping parks, overlaps of three parks, and Ohio River banks where Lewis & Clark and the Trail of Tears share the river.'),
 ('hist','Historic Trail Sites','Visitor centers, certified sites & auto tour route','Wickliffe Mounds, Big Bone Lick and Golden Pond Visitor Center are NOT within 100 ft of the river; they are on the NPS Kentucky visitor center list, and the signed Lewis & Clark auto tour route runs along Wickliffe Mounds, Big Bone Lick and Livingston County WMA. Columbus-Belmont has the NPS Benge Route running through it. Each is listed only because a National Park Service page lists it as a trail site, visitor center or certified site; the page is cited on each card. The POTA Activator Guide says historic trails "do not have specific boundaries," so you need a park or site certified by the NPS and official trail signage. Check with POTA before counting them.'),
 ('river','Ohio River Banks','Lewis & Clark on the river','In Kentucky the Lewis & Clark trail is the Ohio River itself. You must be inside the park AND within 100 ft of the water. Riverbank pins are approximate and were not checked against the actual water line; some may be more than 100 ft from the river.'),
 ('water','Trail of Tears Water Route','Tennessee & Mississippi rivers','The Trail of Tears Water Route followed the Tennessee River (now Kentucky Lake) to Paducah, then the Ohio and Mississippi rivers. You must be inside the park AND within 100 ft of the water. On Kentucky Lake the NPS route line follows the old channel out in the lake, so these are a looser fit than the Ohio River banks. Pins are approximate.'),
 ('trail','Trail 2-Fers','A trail park through another park','Set up on public land within 100 ft of the trail, inside the other park.'),
 ('shared','Overlapping Boundaries','Two parks on the same ground','Boundaries overlap on land that belongs to both. National forest spots count only on Forest Service-owned land. Setup pins sit at least 100 ft inside every boundary line in our map data.')]
BANNER='GPS PINS ARE GUIDES ONLY  •  DO YOUR OWN RESEARCH  •  CONFIRM EVERY BOUNDARY ON THE OFFICIAL MAP  •  THIS WILL GET YOU CLOSE. THE REST IS UP TO YOU.'
c=canvas.Canvas(os.path.join(REPO,'KPC_Kentucky_POTA_2fers_3fers_Guide.pdf'),pagesize=(W,H))
c.setTitle('KPC Kentucky POTA 2-Fers & 3-Fers');c.setAuthor('Kentucky Portable Club');c.setSubject('Multi-park POTA spots in Kentucky with GPS guide pins')
page=[0]
def spaced(x,y,t,font,size,col,sp=1.2,align='l'):
  c.setFont(font,size);c.setFillColorRGB(*col)
  wdt=sum(pdfmetrics.stringWidth(ch,font,size)+sp for ch in t)-sp
  if align=='c': x-=wdt/2
  if align=='r': x-=wdt
  for ch in t: c.drawString(x,y,ch); x+=pdfmetrics.stringWidth(ch,font,size)+sp
  return wdt
def frame(section):
  page[0]+=1
  c.setFillColorRGB(*BG);c.rect(0,0,W,H,stroke=0,fill=1)
  c.setFillColorRGB(*GOLD);c.rect(0,H-7,W,7,stroke=0,fill=1)
  spaced(M,H-36,'KENTUCKY POTA 2-FERS & 3-FERS  •  '+section.upper(),'CB',7,GREEN)
  c.drawImage(LOGO,W-M-30,H-52,30,30,mask='auto'); c.linkRect('',('find'),(W-M-30,H-52,W-M,H-22),relative=0)
  c.setFillColorRGB(*DARK);c.roundRect(M,H-80,CW,17,4,stroke=0,fill=1)
  spaced(W/2,H-74.5,BANNER,'CB',5.1,GOLD,.45,'c')
  c.setFillColorRGB(*FOOT);c.rect(0,0,W,30,stroke=0,fill=1)
  spaced(W/2,12,'KPC KENTUCKY POTA 2-FERS & 3-FERS  •  GPS PINS ARE GUIDES ONLY. VERIFY RULES, ACCESS, MAPS, PERMITS AND SEASONS BEFORE TRAVEL.','CB',5.6,BG,.8,'c')
  c.setFont('CB',7);c.setFillColorRGB(*BG);c.drawRightString(W-M,12,str(page[0]))
  return H-100
def para(x,y,t,font,size,col,width,lead=None,draw=True):
  lead=lead or size*1.3;lines=simpleSplit(t,font,size,width)
  if draw:
    c.setFont(font,size);c.setFillColorRGB(*col)
    for i,l in enumerate(lines): c.drawString(x,y-i*lead,l)
  return len(lines)*lead
def pill(x,y,w,t,fill,txt,stroke=None,url=None,dest=None,h=13):
  c.setFillColorRGB(*fill)
  if stroke: c.setStrokeColorRGB(*stroke);c.setLineWidth(.8)
  c.roundRect(x,y,w,h,h/2,stroke=1 if stroke else 0,fill=1)
  spaced(x+w/2,y+h/2-2.3,t,'CB',6.3,txt,.7,'c')
  if url: c.linkURL(url,(x,y,x+w,y+h),relative=0)
  if dest: c.linkRect('',dest,(x,y,x+w,y+h),relative=0)
def heading(y,title,sub,intro,dest):
  c.bookmarkPage(dest,fit='XYZ',top=y+30); c.addOutlineEntry(title,dest,0)
  c.setFont('S',22);c.setFillColorRGB(*INK);c.drawString(M,y-12,title)
  tw=pdfmetrics.stringWidth(title,'S',22)
  c.setFont('S',11);c.setFillColorRGB(*GOLD);c.drawString(M+tw+8,y-12,sub)
  h=para(M,y-28,intro,'C',8.6,MUTED,CW,11.2)
  return y-34-h
def card(y,d,draw=True):
  x=M;pad=12;tx=x+90;tw=CW-90-pad
  title=' + '.join(d['names'])
  tl=simpleSplit(title,'S',12,tw)
  h=52+len(tl)*14.5
  meta=' • '.join(filter(None,[d['county']+' County' if d.get('county') else '',d.get('size',''),d['how']]))
  rows=[]
  for p in d['points']:
    nl=simpleSplit(p.get('note',''),'C',7.6,CW-130-pad-8)
    wl=simpleSplit(p['what'],'CB',8.2,CW-130-pad-8)
    rows.append((p,wl,nl));h+=len(wl)*10+len(nl)*9.4+5
  site=d.get('site')
  if site: h+=12
  nh=para(0,0,'NOTES '+d['note'],'C',7.9,INK,CW-2*pad,10.2,draw=False); h+=nh+12
  if not draw: return h
  c.setFillColorRGB(1,1,1);c.setStrokeColorRGB(*LINE);c.setLineWidth(.8);c.roundRect(x,y-h,CW,h,8,stroke=1,fill=1)
  pill(x+pad,y-24,60,d['type'].upper(),GOLD,INK)
  c.setFont('S',12);c.setFillColorRGB(*INK)
  for i,l in enumerate(tl): c.drawString(tx,y-20-i*14.5,l)
  yy=y-20-len(tl)*14.5-1
  c.setFont('C',7.6);c.setFillColorRGB(*MUTED);c.drawString(tx,yy,meta[:150])
  yy-=19;px=x+pad
  for r in d['refs']:
    w=pdfmetrics.stringWidth(r,'CB',6.3)+.7*len(r)+16;pill(px,yy,w,r,DARK,(1,1,1),url=POTA(r));px+=w+5
  p0=d['points'][0];pill(px,yy,32,'GPS',(1,1,1),INK,stroke=INK,url=GM(p0['la'],p0['lo']));px+=37
  dp=next((p for p in d['points'] if p['what'].lower().startswith(('parking','drive up'))),p0)
  pill(px,yy,62,'DIRECTIONS',SOFT,INK,stroke=GOLD,url=DIR(dp['la'],dp['lo']))
  yy-=12
  for p,wl,nl in rows:
    yy-=4
    c.setFillColorRGB(*QC[p['q']]);c.roundRect(x+pad,yy-6.5,9,9,1.5,stroke=0,fill=1)
    c.setFont('CB',6.5);c.setFillColorRGB(1,1,1);c.drawCentredString(x+pad+4.5,yy-4.4,p['q'])
    ll=f"{p['la']:.5f}, {p['lo']:.5f}";c.setFont('CB',8.2);c.setFillColorRGB(*INK);c.drawString(x+pad+15,yy-4.5,ll)
    c.linkURL(GM(p['la'],p['lo']),(x+pad+15,yy-7,x+pad+105,yy+4),relative=0)
    for i,l in enumerate(wl): c.setFont('CB',8.2);c.setFillColorRGB(*INK);c.drawString(x+130,yy-4.5-i*10,l)
    yy-=len(wl)*10
    c.setFont('C',7.6);c.setFillColorRGB(*MUTED)
    for i,l in enumerate(nl): c.drawString(x+130,yy-4.2-i*9.4,l)
    yy-=len(nl)*9.4+1
  if site:
    yy-=9;c.setFont('CB',7.8);c.setFillColorRGB(*GREEN);t='SOURCE: NATIONAL PARK SERVICE PAGE ›  '+site['url'].replace('https://','')
    c.drawString(x+pad,yy,t);c.linkURL(site['url'],(x+pad,yy-2,x+pad+pdfmetrics.stringWidth(t,'CB',7.8),yy+8),relative=0)
  yy-=12
  c.setFont('CB',7.9);c.setFillColorRGB(*INK)
  lines=simpleSplit('NOTES '+d['note'],'C',7.9,CW-2*pad)
  for i,l in enumerate(lines):
    if i==0:
      c.setFont('CB',7.9);c.drawString(x+pad,yy,'NOTES');c.setFont('C',7.9);c.drawString(x+pad+pdfmetrics.stringWidth('NOTES ','CB',7.9),yy,l[6:])
    else: c.setFont('C',7.9);c.drawString(x+pad,yy-i*10.2,l)
  return h
# ---------- cover ----------
page[0]+=1
c.setFillColorRGB(*hx('12291e'));c.rect(0,0,W,H,stroke=0,fill=1)
c.setFillColorRGB(*GOLD);c.rect(0,H-7,W,7,stroke=0,fill=1)
spaced(M,H-38,'KENTUCKY PORTABLE CLUB  •  KPC','CB',7,GOLD);spaced(W-M,H-38,'PROVIDED BY BRANDON WHITE  •  KZ4CP','CB',7,GOLD,1.2,'r')
c.drawImage(LOGO,W/2-62,H-205,124,124,mask='auto')
c.setFont('S',38);c.setFillColorRGB(1,1,1);c.drawCentredString(W/2,H-262,'KENTUCKY POTA')
c.setFont('S',25);c.setFillColorRGB(*GOLD);c.drawCentredString(W/2,H-293,'2-Fers & 3-Fers')
c.setStrokeColorRGB(*GOLD);c.setLineWidth(2);c.line(W/2-28,H-308,W/2+28,H-308)
spaced(W/2,H-326,'MULTI-PARK FIELD GUIDE  •  OCTOBER 2026 (RECHECKED OCT 13)','CB',8,(1,1,1),1.6,'c')
c.setFont('C',8.5);c.setFillColorRGB(*hx('c9d3cc'));c.drawCentredString(W/2,H-342,'Overlapping boundaries  •  Trails  •  Historic trails  •  Ohio River banks  •  Park names match the POTA Kentucky list')
def darkbox(y,title,body,fill=hx('1c3f2e'),tc=GOLD,bc=(1,1,1)):
  h=para(0,0,body,'C',8.4,bc,CW-30,11,draw=False)+30
  c.setFillColorRGB(*fill);c.roundRect(M,y-h,CW,h,6,stroke=0,fill=1);c.setFillColorRGB(*GOLD);c.rect(M,y-h,3,h,stroke=0,fill=1)
  spaced(M+15,y-14,title,'CB',6.5,tc,1.2);para(M+15,y-27,body,'C',8.4,bc,CW-30,11);return y-h-10
y=H-365
y=darkbox(y,'GPS PINS ARE GUIDES ONLY','Every GPS point in this guide gets you to the AREA of a possible 2-fer or 3-fer. It is not a confirmed activation spot. When you get there, check that you and your gear are inside every park, and for trail and river parks within 100 ft of the trail or the water. Riverbank pins have not been checked against the actual water line. The four historic trail sites are not on the river or trail at all; they rely on National Park Service listings (cited on each card).')
y=darkbox(y,'DO YOUR OWN RESEARCH','This guide is a planning tool put together by the Kentucky Portable Club from public map data. It has not been field-checked at every spot. This will get you close; the rest is up to you. Boundaries can be out of date or slightly off and do not show private land, closures or hunting seasons. Confirm each boundary on the official agency map, and make sure the land is public and open. You are responsible for making sure your activation is valid and legal.')
y=darkbox(y,'WHAT COUNTS AS A 2-FER','2-fer means two POTA parks only (KFF and SOTA are not 2-fers). You and all your gear must be on public land inside every park you log. Parks that only touch at a border do not count; the parks must overlap. Trails and rivers that are their own park: within 100 ft of the trail or the river\'s edge. National forests count only on Forest Service-owned land. One log per park.')
c.setFillColorRGB(*GOLD);c.roundRect(M,y-78,CW,78,6,stroke=0,fill=1)
c.setFont('S',12);c.setFillColorRGB(*hx('12291e'));c.drawString(M+15,y-20,'GPS GRADES ON EVERY SPOT')
for i,(q,t) in enumerate([('A','Drive up: parking or entrance on file is inside every park.'),('B','Short walk, or a trail crossing you can reach from a road.'),('C','No close parking on file, or a riverbank pin not checked against the water: check satellite view.')]):
  yy=y-36-i*13;c.setFillColorRGB(*QC[q]);c.roundRect(M+15,yy-2,9,9,1.5,stroke=0,fill=1);c.setFont('CB',6.5);c.setFillColorRGB(1,1,1);c.drawCentredString(M+19.5,yy+.3,q)
  c.setFont('CB',8);c.setFillColorRGB(*hx('12291e'));c.drawString(M+30,yy,t)
c.setFillColorRGB(*FOOT);c.rect(0,0,W,30,stroke=0,fill=1);spaced(W/2,12,'KPC KENTUCKY POTA 2-FERS & 3-FERS  •  GPS PINS ARE GUIDES ONLY  •  DO YOUR OWN RESEARCH BEFORE TRAVEL.','CB',5.8,BG,.8,'c')
c.showPage()
# ---------- find a spot ----------
y=frame('Find a spot');c.bookmarkPage('find',fit='XYZ',top=H);c.addOutlineEntry('Find a Spot','find',0)
c.setFont('S',22);c.setFillColorRGB(*INK);c.drawString(M,y-12,'Find a Spot')
para(M,y-28,'Tap a section to jump to it. Tap the KPC logo on any page to come back here. Every GPS button opens Google Maps; every US-#### button opens the POTA park page. GPS pins are guides that get you to the area only.','C',8.6,MUTED,CW,11.2)
cnt={k:sum(1 for d in SP if sec(d)==k) for k,*_ in SECS}
boxes=[('plan','Plan a Trip','Routes, checklist, Google Maps')]+[(k,t,s) for k,t,s,_ in SECS]+[('unc','Unconfirmed','Pairs to research yourself')]
bw=(CW-20)/3;bh=62
for i,(k,t,s) in enumerate(boxes):
  bx=M+(i%3)*(bw+10);by=y-60-(i//3)*(bh+10)-bh
  dark=k in('unc','plan');c.setFillColorRGB(*(DARK if dark else (1,1,1)));c.setStrokeColorRGB(*LINE);c.roundRect(bx,by,bw,bh,6,stroke=0 if dark else 1,fill=1)
  c.setFillColorRGB(*GOLD);c.rect(bx+10,by+bh-4,bw-20,2,stroke=0,fill=1)
  c.setFont('S',12);c.setFillColorRGB(*(GOLD if dark else INK));c.drawString(bx+10,by+bh-20,t)
  c.setFont('C',7.4);c.setFillColorRGB(*((1,1,1) if dark else MUTED));c.drawString(bx+10,by+bh-31,s)
  if k not in('unc','plan'): c.setFont('S',16);c.setFillColorRGB(*INK);c.drawString(bx+10,by+10,str(cnt[k]));spaced(bx+10+pdfmetrics.stringWidth(str(cnt[k]),'S',16)+4,by+11,'SPOTS','CB',5.5,MUTED,.8)
  spaced(bx+bw-10,by+11,'JUMP ›','CB',6,GOLD if dark else INK,.8,'r')
  c.linkRect('',k,(bx,by,bx+bw,by+bh),relative=0)
yy=y-60-((len(boxes)+2)//3)*(bh+10)-4
c.setFillColorRGB(1,1,1);c.setStrokeColorRGB(*LINE);c.roundRect(M,yy-150,CW,150,6,stroke=1,fill=1)
pill(M+12,yy-20,90,'HOW TO READ A CARD',SOFT,INK,stroke=GOLD)
for i,(a,b) in enumerate([('3-FER / 2-FER','How many POTA parks the spot gives you.'),('US-####','Opens that park\'s POTA page. Names are the official POTA names.'),('GPS','Opens the first point in Google Maps (a guide pin, not a confirmed spot).'),('DIRECTIONS','Driving directions to the parking or drive-up point if there is one.'),('A  B  C','GPS grade: drive up, short walk, or check satellite view.'),('PARKING','Parking only. Never the setup spot; it can be outside the park line.'),('NOTES','What to check before you go.')]):
  c.setFont('CB',8);c.setFillColorRGB(*INK);c.drawString(M+16,yy-38-i*15,a);c.setFont('C',8);c.setFillColorRGB(*MUTED);c.drawString(M+130,yy-38-i*15,b)
para(M,yy-168,'These spots also show in KY Park Commander and the KY Trip Planner when you turn on Park Overlaps, and in the Members Room multi-park map and GPX file.','C',8.4,MUTED,CW)
c.showPage()
# ---------- plan a trip ----------
y=frame('Plan a trip');y=heading(y,'Plan a Trip','Routes & checklist','Six ready-made day routes built from the spots in this guide, plus a checklist. Tap OPEN ROUTE to load every stop in Google Maps; miles are straight-line between stops, so driving is longer. GPS points are guide pins only.','plan')
for i,(t,b) in enumerate(DATA['planning']):
  lines=simpleSplit(b,'C',8.2,CW-150);h=max(1,len(lines))*10.4+8
  if y-h<44: c.showPage();y=frame('Plan a trip')
  c.setFillColorRGB(*GOLD);c.circle(M+8,y-6,7,stroke=0,fill=1);c.setFont('CB',8);c.setFillColorRGB(*INK);c.drawCentredString(M+8,y-8.8,str(i+1))
  c.setFont('CB',8.6);c.drawString(M+22,y-9,t)
  c.setFont('C',8.2);c.setFillColorRGB(*MUTED)
  for j,l in enumerate(lines): c.drawString(M+150,y-9-j*10.4,l)
  y-=h
y-=8
for t in DATA['trips']:
  bl=simpleSplit(t['blurb'],'C',8,CW-24)
  rows=[(s,simpleSplit(s['label'],'CB',8.2,CW-200)) for s in t['stops']]
  h=46+len(bl)*10+sum(len(r[1])*10+5 for r in rows)+22
  if y-h<44: c.showPage();y=frame('Plan a trip')
  c.setFillColorRGB(1,1,1);c.setStrokeColorRGB(*LINE);c.setLineWidth(.8);c.roundRect(M,y-h,CW,h,8,stroke=1,fill=1)
  c.setFont('S',12.5);c.setFillColorRGB(*INK);c.drawString(M+12,y-18,t['title'])
  spaced(M+12,y-30,t['tag'].upper(),'CB',6.3,GREEN,.8)
  pill(W-M-12-96,y-24,96,'OPEN ROUTE ›',DARK,(1,1,1),url=t['url'])
  yy=y-44
  c.setFont('C',8);c.setFillColorRGB(*MUTED)
  for l in bl: c.drawString(M+12,yy,l);yy-=10
  yy-=4
  for n,(s,ls) in enumerate(rows):
    c.setFillColorRGB(*(GOLD if s['type']=='3-fer' else SOFT));c.roundRect(M+12,yy-7,30,10,5,stroke=0,fill=1)
    c.setFont('CB',5.8);c.setFillColorRGB(*INK);c.drawCentredString(M+27,yy-4.3,s['type'].upper())
    c.setFont('CB',8.2);c.setFillColorRGB(*INK)
    for j,l in enumerate(ls): c.drawString(M+50,yy-4-j*10,f"{n+1}. "+l if j==0 else '    '+l)
    c.setFont('CB',7.4);c.setFillColorRGB(*GREEN);rt=' + '.join(s['refs']);c.drawRightString(W-M-110,yy-4,rt)
    c.setFont('C',7.4);c.setFillColorRGB(*MUTED);c.drawRightString(W-M-12,yy-4,(f"{s['legmi']} mi from last" if s.get('legmi') else 'start') )
    c.linkURL(GM(s['la'],s['lo']),(M+50,yy-7,W-M-12,yy+5),relative=0)
    yy-=len(ls)*10+5
  c.setFont('C',7.2);c.setFillColorRGB(*MUTED);c.drawString(M+12,yy-6,'Tap a stop to open its guide pin in Google Maps. Check each spot card in this guide before you go.')
  y-=h+10
c.showPage()
# ---------- sections ----------
for k,t,s,intro in SECS:
  y=frame(t);y=heading(y,t,s,intro,k)
  for d in [d for d in SP if sec(d)==k]:
    h=card(y,d,draw=False)
    if y-h<44: c.showPage();y=frame(t)
    card(y,d);y-=h+10
  c.showPage()
# ---------- unconfirmed ----------
y=frame('Unconfirmed');y=heading(y,'Unconfirmed','Not counted in this guide','These pairs might work but could not be confirmed from map data, so they are not in the 62 spots and are not shown as 2-fers on the KPC map tools. Do your own research before you count on any of them.','unc')
for a,b in DATA['unconfirmed']:
  al=simpleSplit(a,'CB',8.4,220);bl=simpleSplit(b,'C',8.2,CW-260);h=max(len(al),len(bl))*10.5+12
  c.setFillColorRGB(1,1,1);c.setStrokeColorRGB(*LINE);c.roundRect(M,y-h,CW,h,5,stroke=1,fill=1)
  for i,l in enumerate(al): c.setFont('CB',8.4);c.setFillColorRGB(*INK);c.drawString(M+10,y-13-i*10.5,l)
  for i,l in enumerate(bl): c.setFont('C',8.2);c.setFillColorRGB(*MUTED);c.drawString(M+245,y-13-i*10.5,l)
  y-=h+6
c.showPage()
# ---------- sources & changes ----------
y=frame('Sources');c.bookmarkPage('src',fit='XYZ',top=H);c.addOutlineEntry('Sources & changes','src',0)
c.setFont('S',22);c.setFillColorRGB(*INK);c.drawString(M,y-12,'Sources & How This Was Built');y-=32
for t,s,u in DATA['sources']:
  c.setFont('CB',9);c.setFillColorRGB(*GREEN);c.drawString(M,y,t+' ›');c.linkURL(u,(M,y-2,M+pdfmetrics.stringWidth(t+' ›','CB',9),y+9),relative=0)
  c.setFont('C',8);c.setFillColorRGB(*MUTED);c.drawString(M,y-11,s);y-=26
y-=4;c.setFont('S',13);c.setFillColorRGB(*INK);c.drawString(M,y,'What changed in the October 13 recheck');y-=14
for l in DATA['changes']:
  h=para(M+10,y,'•  '+l,'C',8,INK,CW-10,10.2);y-=h+2
y-=6;para(M,y,'Compiled by the Kentucky Portable Club, October 13, 2026. Spots have not all been field-checked. Before you go, check the park\'s official map, the Forest Service ownership map for any national forest spot, hunting seasons on WMAs (wear blaze orange during gun seasons), and any closures. Report a wrong spot to the Kentucky Portable Club so it can be fixed.','C',8.2,MUTED,CW,10.8)
c.showPage();c.save();print('pages',page[0])
