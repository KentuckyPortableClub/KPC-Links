"""Refreshes the 2-Fers & 3-Fers index pages and every park card's 2-fer line in the two
Kentucky POTA Resource PDFs, from fers.json. Needs poppler (pdftotext) and pypdf + reportlab.
usage (repo root): python3 .claude/build/fers/resource_patch.py"""
import json,os,re,subprocess,io,tempfile,html
import pypdf
from pypdf.generic import NameObject,ArrayObject
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
HERE=os.path.dirname(os.path.abspath(__file__)); REPO=os.path.abspath(os.path.join(HERE,'..','..','..'))
FD='/usr/share/fonts/truetype/crosextra/'
for n,f in [('C','Carlito-Regular'),('CB','Carlito-Bold'),('S','Caladea-Bold')]:
  try: pdfmetrics.getFont(n)
  except KeyError: pdfmetrics.registerFont(TTFont(n,FD+f+'.ttf'))
F=json.load(open(os.path.join(HERE,'fers.json'))); SP=F['spots']
NAMES={r:n for d in SP for r,n in zip(d['refs'],d['names'])}
def hx(h): h=h.lstrip('#'); return tuple(int(h[i:i+2],16)/255 for i in (0,2,4))
BG,GOLD,GREEN,DARK,INK,MUTED,LINE,SOFT=map(hx,['f6f1e4','d5a63a','1d5a3a','173b2b','1b1f1a','5d6358','dcd4bf','f3dfa6'])
W,H=612,792;M=40
GM=lambda la,lo:f'https://www.google.com/maps/search/?api=1&query={la:.5f},{lo:.5f}'
POTA=lambda r:'https://pota.app/#/park/'+r
def sec(d):
  if d['type']=='3-fer': return 0
  if 'Historic Trail site' in d['how'] or 'auto tour route' in d['how']: return 1
  if 'Water Route bank' in d['how']: return 3
  if 'riverbank' in d['how'].lower(): return 2
  if 'through the park' in d['how']: return 4
  return 5
SECN=['3-Fers','Historic trail sites (visitor centers, certified sites, auto tour route)','Ohio River banks (Lewis & Clark)','Trail of Tears Water Route (Kentucky Lake & Mississippi River)','Trail 2-fers','Overlapping boundaries']
def guidept(d):
  return next((p for p in d['points'] if not p['what'].lower().startswith(('parking','drive up'))),d['points'][0])
# ---------------- index pages ----------------
def index_pdf(kind):
  buf=io.BytesIO();c=canvas.Canvas(buf,pagesize=(W,H))
  def frame():
    c.setFillColorRGB(*BG);c.rect(0,0,W,H,stroke=0,fill=1);c.setFillColorRGB(*GOLD);c.rect(0,H-6,W,6,stroke=0,fill=1)
    c.setFont('CB',6.8);c.setFillColorRGB(*GREEN);c.drawString(M,H-32,f'KENTUCKY POTA FIELD RESOURCE  •  {kind}  •  2-FERS & 3-FERS INDEX')
    c.setFillColorRGB(*DARK);c.roundRect(M,H-75,W-2*M,18,4,stroke=0,fill=1)
    c.setFont('CB',6.8);c.setFillColorRGB(*GOLD);c.drawCentredString(W/2,H-68.5,'GPS PINS ARE GUIDES ONLY  •  DO YOUR OWN RESEARCH  •  THIS INDEX IS A PLANNING TOOL  •  CONFIRM EVERY BOUNDARY ON THE OFFICIAL MAP')
    c.setFillColorRGB(*DARK);c.rect(0,0,W,26,stroke=0,fill=1);c.setFont('CB',5.8);c.setFillColorRGB(*BG)
    c.drawCentredString(W/2,10,'KPC KENTUCKY POTA RESOURCE  •  GPS PINS ARE GUIDES ONLY. DO YOUR OWN RESEARCH. VERIFY CURRENT RULES, ACCESS, MAPS, PERMITS AND SEASONAL CONDITIONS BEFORE TRAVEL.')
    return H-92
  y=frame()
  c.setFont('S',20);c.setFillColorRGB(*INK);c.drawString(M,y-14,'Kentucky 2-Fers & 3-Fers Index')
  n3=sum(1 for d in SP if d['type']=='3-fer')
  intro=(f'All {len(SP)} places in Kentucky where you may work two or three POTA parks at once ({n3} 3-fers, {len(SP)-n3} 2-fers), checked against the POTA rules by the Kentucky Portable Club. Park names and numbers match the POTA Kentucky park list. '
    'GPS POINTS ARE GUIDE PINS ONLY: they get you to the area of the possible 2-fer or 3-fer, not to a confirmed spot. You and your gear must be on public land inside every park; trail and river parks within 100 ft of the trail or water (riverbank pins are approximate and were not checked against the water line); national forests only on Forest Service-owned land. '
    'Wickliffe Mounds, Big Bone Lick and Golden Pond are NOT within 100 ft of the river or trail; they rely on the NPS Lewis & Clark visitor center list. Tap a GPS point to open it in Google Maps. More detail, parking, NPS sources and walk-in points are in the KPC 2-Fers & 3-Fers Field Guide in the Members Room.')
  ls=simpleSplit(intro,'C',8.2,W-2*M);c.setFont('C',8.2);c.setFillColorRGB(*MUTED)
  for i,l in enumerate(ls): c.drawString(M,y-30-i*10.4,l)
  y=y-30-len(ls)*10.4-4
  rows=sorted(SP,key=lambda d:(sec(d),d['county'],d['refs']))
  cur=None
  for d in rows:
    s=sec(d);nm=' + '.join(d['names'])
    nl=simpleSplit(nm,'C',7.6,W-2*M-200)
    rh=12+len(nl)*9+3
    need=rh+(22 if s!=cur else 0)
    if y-need<36: c.showPage();y=frame()
    if s!=cur:
      cnt=sum(1 for x in SP if sec(x)==s);cur=s
      c.setFont('S',11.5);c.setFillColorRGB(*INK);c.drawString(M,y-15,f'{SECN[s]}  ({cnt})' if s!=0 or True else '');y-=22
    c.setFillColorRGB(1,1,1);c.setStrokeColorRGB(*LINE);c.setLineWidth(.7);c.roundRect(M,y-rh,W-2*M,rh,5,stroke=1,fill=1)
    c.setFillColorRGB(*(GOLD if d['type']=='3-fer' else SOFT));c.roundRect(M+6,y-12.5,32,9.5,4.7,stroke=0,fill=1)
    c.setFont('CB',5.8);c.setFillColorRGB(*INK);c.drawCentredString(M+22,y-9.6,d['type'].upper())
    c.setFont('CB',7.6);c.setFillColorRGB(*GREEN);x=M+46
    for i,r in enumerate(d['refs']):
      t=r+(' + ' if i<len(d['refs'])-1 else '');c.drawString(x,y-10,t);c.linkURL(POTA(r),(x,y-12,x+pdfmetrics.stringWidth(r,'CB',7.6),y-2),relative=0);x+=pdfmetrics.stringWidth(t,'CB',7.6)
    c.setFont('C',7.6);c.setFillColorRGB(*INK)
    for i,l in enumerate(nl): c.drawString(M+46,y-20-i*9,l)
    p=guidept(d);ll=f"{p['la']:.5f}, {p['lo']:.5f}  ›"
    c.setFont('C',7.2);c.setFillColorRGB(*MUTED);c.drawRightString(W-M-108,y-10,d['county']+' Co.')
    c.setFont('CB',7.6);c.setFillColorRGB(*GREEN);c.drawRightString(W-M-8,y-10,ll)
    c.setFont('C',6.4);c.setFillColorRGB(*MUTED);c.drawRightString(W-M-8,y-19,'guide pin: '+('approximate riverbank' if 'riverbank' in p['what'].lower() else p['what'][:34].lower()))
    c.linkURL(GM(p['la'],p['lo']),(W-M-110,y-rh,W-M,y),relative=0)
    y-=rh+4
  if y<120: c.showPage();y=frame()
  y-=6;c.setFont('CB',7.8);c.setFillColorRGB(*INK);c.drawString(M,y,'Not counted here (do your own research):')
  t='; '.join(a+(' (checked: NOT a 2-fer)' if b.startswith('Checked') else '') for a,b in F['unconfirmed'])+'. State parks inside the Daniel Boone outer boundary (Cumberland Falls, Natural Bridge, Buckhorn Lake) are state land, not national forest land.'
  ls=simpleSplit(t,'C',7.6,W-2*M);c.setFont('C',7.6);c.setFillColorRGB(*MUTED)
  for i,l in enumerate(ls): c.drawString(M,y-11-i*9.6,l)
  c.showPage();c.save();buf.seek(0);return pypdf.PdfReader(buf)
# ---------------- per-park 2-fer lines ----------------
def partner_text(ref):
  items=[]
  for d in SP:
    if ref not in d['refs']: continue
    others=[r for r in d['refs'] if r!=ref]
    tag=''
    if sec(d)==1 and 'US-1252' not in d['refs']: tag=' (NOT within 100 ft of the river; NPS-listed site)'
    elif sec(d)==3: tag=' (Water Route shore, within 100 ft of the water)'
    elif sec(d)==2: tag=' (riverbank, within 100 ft of the water)'
    items.append((d['type'],others,tag))
  return items
def render_items(items,full=True):
  out=[]
  for t,others,tag in items:
    s=' + '.join((f'{r} {NAMES[r]}' if full else r) for r in others)
    out.append(('3-fer with ' if t=='3-fer' else '')+s+(tag if full else ''))
  return out
LABEL=re.compile(r'^(TRAIL 2-FER PARKS|TRAIL 2-FER|2-FER)\b')
def lines_of(pdf,pg):
  out=subprocess.run(['pdftotext','-bbox-layout','-f',str(pg),'-l',str(pg),pdf,'-'],capture_output=True,text=True).stdout
  L=[]
  for m in re.finditer(r'<line xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</line>',out,re.S):
    L.append((float(m[1]),float(m[2]),float(m[3]),float(m[4]),html.unescape(' '.join(re.findall(r'>([^<]*)</word>',m[5])))))
  return L
def blocks(L):
  res=[];cur_ref=None;i=0
  while i<len(L):
    x0,y0,x1,y1,t=L[i]
    if re.fullmatch(r'US-\d+',t) and x0<120: cur_ref=t
    if abs(x0-50)<1 and LABEL.match(t):
      blk=[L[i]];j=i+1
      while j<len(L) and abs(L[j][0]-50)<1 and L[j][1]-blk[-1][1]<13.5: blk.append(L[j]);j+=1
      res.append((cur_ref,blk));i=j;continue
    i+=1
  return res
def wrap_rich(label,text,size,width):
  # returns list of lines; each line list of (str,font)
  toks=[(label+' ','CB')]+[(w+' ','CB' if re.fullmatch(r'US-\d+,?',w) else 'C') for w in text.split()]
  lines=[[]];wd=0
  for s,f in toks:
    sw=pdfmetrics.stringWidth(s,f,size)
    if wd+sw-pdfmetrics.stringWidth(' ',f,size)>width and lines[-1]: lines.append([]);wd=0
    lines[-1].append((s,f));wd+=sw
  return lines
def patch_parks(pdf,writer,offset):
  done=set();log=[];pending={}
  r=pypdf.PdfReader(pdf)
  for pg in range(6,len(r.pages)+1):
    L=lines_of(pdf,pg);B=blocks(L)
    if not B: continue
    buf=io.BytesIO();c=canvas.Canvas(buf,pagesize=(W,H));rects=[]
    for ref,blk in B:
      top=blk[0][1];bot=blk[-1][3];nlines=len(blk)
      x0=49;x1=566
      c.setFillColorRGB(1,1,1);c.rect(x0-1,H-bot-2.5,x1-x0+1,bot-top+4,stroke=0,fill=1);rects.append((x0-1,H-bot-2.5,x1,H-top+1.5))
      items=partner_text(ref) if ref else []
      if ref in done and pending.get(ref): label,text='2-FER (CONTINUED)',pending.pop(ref)
      elif ref in done: label,text='2-FER','See the 2-fer line above for this park.'
      elif items:
        label='3-FER / 2-FER' if any(t=='3-fer' for t,_,_ in items) else '2-FER'
        text=None
      else:
        label,text='2-FER','None confirmed in the KPC 2-Fers & 3-Fers Index. Earlier listed pairs here could not be confirmed from map data; do your own research.'
      cands=[]
      if text: cands=[text]
      else:
        full=' • '.join(render_items(items,True))+' — GPS guide pins in the 2-Fers & 3-Fers Index; do your own research.'
        short=' • '.join(render_items(items,False))+' — names and GPS guide pins in the 2-Fers & 3-Fers Index.'
        cands=[full,short]
      chosen=None
      for t in cands:
        for size in (8.6,8.2,7.8,7.4,7.0):
          ls=wrap_rich(label,t,size,x1-x0-4)
          if len(ls)<=nlines: chosen=(ls,size,11.6);break
        if chosen: break
      if not chosen:
        ls=wrap_rich(label,cands[-1],7.0,x1-x0-4)
        if len(ls)>nlines:
          rest=' '.join(t.strip() for l in ls[nlines:] for t,_ in l)
          more=sum(1 for b in B if b[0]==ref)>1 and ref not in done
          ls=ls[:nlines]
          if more: pending[ref]=rest
          else: ls[-1]=ls[-1][:-3]+[('… (full list in the index)','C')]
        chosen=(ls,7.0,11.6)
      ls,size,lead=chosen
      y=H-top-size*0.95
      for k,l in enumerate(ls):
        x=50
        for s,f in l:
          c.setFont(f,size);c.setFillColorRGB(*(GREEN if f=='CB' and s.startswith('US-') else INK));c.drawString(x,y-k*lead,s);x+=pdfmetrics.stringWidth(s,f,size)
      if ref: done.add(ref)
      log.append((pg,ref,len(blk),len(ls),size))
    c.save();buf.seek(0)
    page=writer.pages[pg-1+offset]
    ov=pypdf.PdfReader(buf).pages[0];page.merge_page(ov)
    ann=page.get('/Annots')
    if ann:
      keep=ArrayObject()
      for a in ann:
        rr=[float(v) for v in a.get_object().get('/Rect',[0,0,0,0])]
        hit=any(not(rr[2]<R[0] or rr[0]>R[2] or rr[3]<R[1] or rr[1]>R[3]) for R in rects)
        if not hit: keep.append(a)
      page[NameObject('/Annots')]=keep
  return log
for fn,kind in [('KPC_Kentucky_POTA_Resource_Alphabetical_v2_261005_092105.pdf','ALPHABETICAL'),('KPC_Kentucky_POTA_Resource_Numerical_v2_261005_092033.pdf','NUMERICAL')]:
  src=os.path.join(REPO,fn);orig=pypdf.PdfReader(src)
  idx_pages=[i for i,p in enumerate(orig.pages) if '2-FERS & 3-FERS INDEX' in (p.extract_text() or '')]
  assert idx_pages==[2,3,4],idx_pages
  w=pypdf.PdfWriter(clone_from=src)
  log=patch_parks(src,w,0)   # park pages are numbered against the original file
  for i in reversed(idx_pages): w.remove_page(i)
  new=index_pdf(kind)
  for k,p in enumerate(new.pages): w.insert_page(p,2+k)
  w.add_outline_item('2-Fers & 3-Fers Index',2)
  tmp=src+'.tmp';w.write(tmp);os.replace(tmp,src)
  print(fn,'index pages',len(new.pages),'park blocks',len(log))
  for l in log: print('  ',l)
