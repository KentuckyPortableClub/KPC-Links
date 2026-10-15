import urllib.request,re,html
def get(u): return urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 KPC'}),timeout=40).read().decode('utf8','replace')
for n,i in [('Boone Forestlands',9003),('Elk Forest',9124),('Martins Fork',9118),('Fortner-Davis',9204),('Blackford Oaks',9719),('Robinson Forest',9120)]:
  T=re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',re.sub(r'(?s)<script.*?</script>|<style.*?</style>','',get('https://app.fw.ky.gov/Public_Lands_Search/detail.aspx?Kdfwr_id=%d'%i)))))
  hits=[T[max(0,m.start()-200):m.end()+200] for m in re.finditer(r'[Oo]wned|[Ll]ease|[Ee]asement|[Pp]rivate|[Pp]urchase|[Aa]cquir|[Pp]artner|agreement',T)]
  d=T.find('Directions & Description')
  print('##',n,'| HITS:',' || '.join(hits[:4]) or '(none)','| DESC:',T[d:d+900],flush=True)
