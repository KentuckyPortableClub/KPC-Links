"""Puts the member / scene hero pictures on their pages (Oct 14 2026).
Adds one <style id="kpc-hero-pic"> block at the end of <head> (so it wins over older hero rules)
and, for member pictures, a name + call sign badge in the hero. Safe to run again (replaces its own block)."""
import re
BADGE_CSS=('.kpc-who{position:absolute;right:14px;bottom:12px;z-index:3;background:rgba(7,7,7,.74);border:1px solid rgba(213,166,58,.7);'
           'color:#fff;font:800 13px/1.2 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;letter-spacing:.6px;padding:7px 12px;border-radius:999px;white-space:nowrap}'
           '.kpc-who b{color:#e8c46a}')
P={
 'kpc-cw.html':      ('hero-k4zsr',     'center 42%','0px', ('Zach','K4ZSR')),
 'kpc-cw-info.html': ('hero-k4zsr',     'center 42%','0px', ('Zach','K4ZSR')),
 'kpc-weather.html': ('hero-n4bdw',     'center 30%','calc(-29vw)',    ('Brent','N4BDW')),
 'kpc-community.html':('hero-kq4hzk',   'center 45%','calc(-34vw)',    ('Aaron','KQ4HZK')),
 'members.html':     ('hero-ky-flag',   'center 45%','center 40%', None),
 'kpc-campgrounds.html':('hero-campsite','center 58%','center 60%', None),
 'kpc-park-notes.html':('hero-river-camp','center 58%','center 55%', None),
}
for f,(img,pd,pm,who) in P.items():
    s=open(f,encoding='utf-8').read()
    s=re.sub(r'<style id="kpc-hero-pic">.*?</style>\n?','',s,flags=re.S)
    s=re.sub(r'<span class="kpc-who">.*?</span>','',s)
    desk=('.hero{position:relative;background:linear-gradient(90deg,rgba(7,7,7,.9) 0%%,rgba(7,7,7,.66) 42%%,rgba(7,7,7,.18) 72%%,rgba(7,7,7,0) 100%%),url("%s.jpg") %s/cover no-repeat #070707}'%(img,pd))
    if who:   # computers: the whole picture on the right with a soft fade, so the person is never cut off
        desk=('@media(min-width:761px){.hero{position:relative;background:#070707;min-height:520px;overflow:hidden}'
              '.hero:before{content:"";display:block;position:absolute;top:0;bottom:0;right:0;left:auto;width:auto;height:auto;aspect-ratio:1672/941;max-width:100%%;border:0;border-radius:0;box-shadow:none;'
              'background:url("%s.jpg") right center/cover no-repeat;-webkit-mask-image:linear-gradient(90deg,transparent 0,rgba(0,0,0,.55) 22%%,#000 45%%);mask-image:linear-gradient(90deg,transparent 0,rgba(0,0,0,.55) 22%%,#000 45%%);z-index:0}'
              '.hero .hero-inner,.hero .wrap{position:relative;z-index:2}header.hero{display:flex;align-items:center}header.hero .wrap{width:100%%}.hero h1,.hero .hero-copy,.hero .eyebrow{text-shadow:0 2px 12px rgba(0,0,0,.85)}}'%img)
    if who:   # phone: the picture sits on top (face showing), the words go underneath it
        mob=('@media(max-width:760px){.hero{position:relative;display:block;min-height:0;padding-top:104vw;background:linear-gradient(180deg,rgba(7,7,7,0) 0,rgba(7,7,7,0) calc(104vw - 150px),#070707 104vw),'
             'url("%s-mobile.jpg") center %s/100%% auto no-repeat #070707}.hero:before,.hero:after{display:none}.hero .hero-inner,.hero .wrap{margin:0 auto;padding-top:4px;padding-bottom:38px}.kpc-who{top:12px;bottom:auto}}'%(img,pm))
    else:
        mob=('@media(max-width:760px){.hero{min-height:460px;background:linear-gradient(180deg,rgba(7,7,7,.35) 0%%,rgba(7,7,7,.55) 45%%,rgba(7,7,7,.88) 100%%),url("%s-mobile.jpg") %s/cover no-repeat #070707}}'%(img,pm))
    css=(BADGE_CSS if who else '')+desk+mob
    blk='<style id="kpc-hero-pic">'+css+'</style>\n'
    if '</head>' in s: s=s.replace('</head>',blk+'</head>',1)
    else:   # pages rebuilt by assemble.py have no </head>: put it just before the hero
        m=re.search(r'<(section|header) class="hero">',s); s=s[:m.start()]+blk+s[m.start():]
    if who:
        m=re.search(r'<(section|header) class="hero">',s)
        s=s[:m.end()]+'<span class="kpc-who">%s · <b>%s</b></span>'%who+s[m.end():]
    open(f,'w',encoding='utf-8').write(s);print(f,img,'badge' if who else '')
