"""Builds the four 'room' pages (Map Room, POTA Room, WWFF/KFF Room, SOTA Room) from the content below.
Run from the repo root:  python3 .claude/build/rooms/make_rooms.py   (writes the main files and calls assemble.py)
Look comes from kpc-boards.css (main.kb) + kpc-rooms.css. Rules were checked Oct 16 2026 against parksontheair.com/rules,
the WWFF Global Rules v5.10 PDF and SOTA activator material; re-check them if the programs change their rules."""
import os, subprocess, html
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
e = html.escape

def card(href, icon, title, what, when, tag='', ext=False):
    t = f'<span class="rm-tag">{e(tag)}</span>' if tag else ''
    tgt = ' target="_blank" rel="noopener"' if ext else ''
    return (f'<a class="kb-card rm-card" href="{href}"{tgt}><div class="rm-top"><span class="rm-ic" aria-hidden="true">{icon}</span>{t}</div>'
            f'<h3>{title}</h3><p>{what}</p>' + (f'<p class="rm-when"><b>Use it when:</b> {when}</p>' if when else '') +
            f'<span class="rm-go">{"OPEN ↗" if ext else "OPEN →"}</span></a>')

def section(kicker, title, lead, cards, alt=False, sid=''):
    return (f'<section class="kb-sec"{" style=\"background:#ebe3d1\"" if alt else ""}{f" id={chr(34)}{sid}{chr(34)}" if sid else ""}><div class="kb-in">'
            f'<p class="kb-k">{kicker}</p><h2>{title}</h2>' + (f'<p class="kb-lead">{lead}</p>' if lead else '') +
            '<div class="kb-grid">' + ''.join(cards) + '</div></div></section>')

def hero(pic, eyebrow, h1a, h1b, copy, chips, jumps):
    return (f'<section class="kb-hero" style="--pic:url(\'{pic}.jpg\');--picm:url(\'{pic}-mobile.jpg\')"><div class="kb-hero-in">'
            f'<p class="kb-eyebrow">{eyebrow}</p><h1>{h1a} <span>{h1b}</span></h1><p class="kb-copy">{copy}</p>'
            '<div class="kb-chips">' + ''.join(f'<span>{c}</span>' for c in chips) + '</div>'
            '<div class="kb-actions">' + ''.join(f'<a class="kb-btn {"gold" if i == 0 else "ghost"}" href="{h}">{t}</a>' for i, (t, h) in enumerate(jumps)) +
            '</div></div></section>')

def nums(items):
    return '<div class="rm-nums">' + ''.join(f'<div class="rm-num"><b>{n}</b><span>{t}</span></div>' for n, t in items) + '</div>'

def rules(kicker, title, lead, items, src):
    return (f'<section class="kb-sec" id="rules"><div class="kb-in"><p class="kb-k">{kicker}</p><h2>{title}</h2><p class="kb-lead">{lead}</p>'
            + '<ul class="rm-rules">' + ''.join(f'<li>{x}</li>' for x in items) + '</ul>'
            + f'<p class="kb-small rm-src">{src}</p></div></section>')

def steps(kicker, title, cols):
    out = f'<section class="kb-sec" id="how" style="background:#ebe3d1"><div class="kb-in"><p class="kb-k">{kicker}</p><h2>{title}</h2><div class="rm-two">'
    for h, items in cols:
        out += f'<div class="kb-how"><h3 class="rm-h3">{h}</h3><ol class="rm-steps">' + ''.join(f'<li>{x}</li>' for x in items) + '</ol></div>'
    return out + '</div></div></section>'

def other_rooms(skip):
    R = [('kpc-map-room.html', '🗺', 'Map Room', 'Every KPC map tool in one place.'),
         ('kpc-pota-room.html', '🌲', 'POTA Room', 'Parks on the Air: rules, guides and tools.'),
         ('kpc-wwff-room.html', '🦌', 'WWFF / KFF Room', 'World Wide Flora & Fauna: rules, guides and tools.'),
         ('kpc-sota-room.html', '⛰', 'SOTA Room', 'Summits on the Air: rules, guides and tools.')]
    return ('<section class="kb-sec"><div class="kb-in"><p class="kb-k">MORE ROOMS</p><h2>Keep Exploring</h2><div class="kb-grid">'
            + ''.join(card(h, i, t, d, '') for h, i, t, d in R if h != skip) + '</div></div></section>')

DISCLAIM = ('<p class="kb-small rm-note">These are short, plain-language summaries to get you started. The program\'s own rules always win: '
            'read the official pages linked here before you go, because rules can change.</p>')

FILES = [('KPC_Kentucky_POTA_Parks', '🌲 Kentucky POTA parks'), ('KPC_Kentucky_KFF_References', '🦌 Kentucky KFF references'),
         ('KPC_Kentucky_SOTA_W4K_Summits', '⛰ Kentucky SOTA summits (W4K)')]
def files_box(only=None):
    rows = ''.join(f'<div class="rm-file"><b>{t}</b><span><a class="kb-btn line sm" href="{f}.kml" download>KML · GOOGLE EARTH / MAP APPS</a>'
                   f'<a class="kb-btn line sm" href="{f}.gpx" download>GPX · GARMIN / GPS UNITS</a></span></div>'
                   for f, t in FILES if not only or only in f)
    return (f'<div class="rm-files">{rows}</div><details class="rm-which"><summary>WHICH FILE DO I NEED?</summary><ul>'
            '<li><b>iPhone or Android:</b> KML. Open it in Google Earth, Gaia GPS, onX or Avenza. On a phone the button opens the share menu: pick the app or Save to Files.</li>'
            '<li><b>Garmin handheld or car GPS:</b> GPX. Copy it to the Garmin\'s GPX folder or load it with Garmin Explore / BaseCamp.</li>'
            '<li><b>Computer:</b> KML for Google Earth (double-click it), GPX for most mapping programs.</li>'
            '<li>Pins are guides that get you to the area. The official boundary is what counts: check it with <a href="kpc-in-park.html">Am I in the Park?</a></li></ul></details>')

PAGES = {}

# ================================================================== MAP ROOM
PAGES['kpc-map-room.html'] = ('Map Room | KPC', 'Every Kentucky Portable Club map tool in one place, with what each one does: park and summit maps, GPS boundary checks, trip planners and rare parks.', ''.join([
    hero('hero-map', 'KPC MAP ROOM • EVERY MAP TOOL IN ONE PLACE', 'THE MAP', 'ROOM',
         "Not sure which map to open? Here's every KPC map tool, what it's for, and when to use it. Kentucky tools first, then the ones that work in any state.",
         ['🗺 Find & plan', '📍 At the park', '🔎 Look it up', '🌎 Any state'],
         [('🗺 FIND & PLAN ↓', '#plan'), ('📍 AT THE PARK ↓', '#at'), ('🔎 LOOK IT UP ↓', '#look')]),
    section('FIND &amp; PLAN', '🗺 Find a Park or Summit, Plan a Trip', 'Start here when you\'re choosing where to go.', [
        card('finder.html', '🗺', 'KY Park Commander', 'The big Kentucky map: every POTA park, SOTA summit and KFF reference, with official boundary layers and overlapping-boundary (2-fer) areas.', 'you want to see everything in Kentucky on one map and pick a spot.', 'KENTUCKY'),
        card('kpc-planner.html', '📅', 'KY Trip Planner', 'Type a town and see the POTA parks, SOTA summits and KFF references nearby, then build a route that hits several in one trip.', 'you\'re planning a day out or a weekend of activations in Kentucky.', 'KENTUCKY'),
        card('kpc-planner-us.html', '🧭', 'US Trip Planner', 'The same idea for anywhere in the US: parks, summits and WWFF references near any town, with Street View, boundaries and a Google Maps route.', 'you\'re traveling out of state and want to activate on the way.', 'ANY STATE'),
        card('kpc-rare.html', '🎯', 'Rarely Activated Parks', 'Every Kentucky POTA park colored by how often it has been activated, so you can find the ones hunters are waiting for.', 'you want to give hunters a park they still need.', 'KENTUCKY'),
        card('kpc-sota.html', '⛰', 'SOTA Summit Map', 'Every SOTA summit in Kentucky or any US SOTA area. Load your SOTA log to see which summits you have chased or activated.', 'you\'re picking a summit or checking which ones you still need.', 'ANY STATE'),
    ], sid='plan'),
    section('AT THE PARK', '📍 Out in the Field', 'Tools made for your phone once you\'re on the way or at the park.', [
        card('kpc-in-park.html', '📍', 'Am I in the Park?', 'Uses your phone\'s GPS to check the official POTA and WWFF boundaries (and SOTA activation zones): inside or not, how far to the edge, and which way to walk.', 'you\'ve parked and want to be sure you\'re over the line before you set up.', 'ANY STATE'),
        card('kpc-kit.html', '🎒', 'Activation Kit', 'One park, summit or WWFF area on one screen: weather and bands, boundary map with parking, other references at the spot, where to stay and Spot Me. Save it at home and it opens with no signal.', 'you want everything for the trip in one tap, even with no cell signal.', 'ANY STATE'),
        card('kpc-park-info.html', '🏛', 'Park &amp; Summit Info Finder', 'Type any POTA, WWFF or SOTA number (or a park name) anywhere. Get the official website and the official boundary on a map, and save the boundary as KML, GPX or GeoJSON.', 'you need the official boundary or website for a park outside Kentucky.', 'ANY STATE'),
        card('kpc-weather.html', '🌦', 'Field Weather &amp; Radar', 'Weather alerts, the next 24 hours, a radar and lightning map, and NOAA Weather Radio for where you\'ll be.', 'you\'re checking for storms before and during an activation.', 'ANY STATE'),
    ], alt=True, sid='at'),
    section('LOOK IT UP', '🔎 Check &amp; Track', 'Quick answers about a spot or a call sign.', [
        card('kpc-lookup.html', '🔢', 'Grid &amp; County Lookup', 'Your grid square, Kentucky county and the nearest parks for your location or any reference.', 'a contact asks for your grid or county, or you\'re filling in a log.', 'KENTUCKY'),
        card('kpc-checker.html', '✅', 'Park Checker', 'Pick any state and see which POTA parks a call sign has <b>activated</b>, on a map and as a list. <b>Hunters</b> load the hunter file from pota.app to see which parks they\'ve worked and which they still need.', 'you want to know which parks you, or a friend, still need to activate or hunt, in any state.', 'ANY STATE'),
        card('kpc-tracker.html', '📊', 'Park Tracker', 'Tracks the Kentucky POTA parks a call sign has activated, with the KPC club leaderboard.', 'you\'re working toward activating every park in Kentucky.', 'KENTUCKY'),
    ], sid='look'),
    other_rooms('kpc-map-room.html'),
]))

# ================================================================== POTA ROOM
PAGES['kpc-pota-room.html'] = ('POTA Room | KPC', 'Parks on the Air in plain words: what POTA is, the rules (10 contacts in one UTC day), how to activate and hunt, Kentucky guides and tools.', ''.join([
    hero('hero-lake-camp', 'KPC POTA ROOM • PARKS ON THE AIR', 'PARKS ON', 'THE AIR',
         'Take a radio to a public park and make contacts, or hunt the people who do. Here are the rules in plain words, our Kentucky guides, and every tool you need.',
         ['📻 Activate', '🎯 Hunt', '🌲 Kentucky parks'],
         [('THE RULES ↓', '#rules'), ('HOW TO START ↓', '#how'), ('KENTUCKY GUIDES ↓', '#guides')]),
    '<section class="kb-sec"><div class="kb-in"><p class="kb-k">WHAT IT IS</p><h2>POTA in a Minute</h2>'
    '<p class="kb-lead"><b>Activators</b> set up a station inside a park on the POTA list and make contacts. <b>Hunters</b> work them from home, the car or another park. '
    'Every park has a number like <b>US-1277</b>. Kentucky has state parks, wildlife management areas, nature preserves, national forest land, wildlife refuges, historic sites and trails on the list.</p>'
    + nums([('10', 'contacts in one UTC day = a full activation'), ('100%', 'of you and your gear inside the park boundary'), ('ADIF', 'log uploaded at pota.app after you finish'), ('0', 'logs for hunters: activator logs give you credit')]) + '</div></section>',
    rules('THE RULES', '📜 The Main Rules', 'From the official POTA rules. Read them in full before your first activation.', [
        '<b>Make an account</b> at pota.app (activators need one; it\'s free).',
        '<b>10 contacts in one UTC day</b> make a full activation. The UTC day starts at midnight UTC: <b>8 PM Eastern / 7 PM Central</b> in summer, <b>7 PM Eastern / 6 PM Central</b> in winter. Contacts after that count toward the next day.',
        '<b>You and all of your equipment must be inside the park boundary.</b> The yellow dots on the POTA map are only approximate. Check the official boundary (our <a href="kpc-in-park.html">Am I in the Park?</a> does this).',
        '<b>Upload an ADIF log</b> when you\'re done, under My Log Uploads on pota.app. Any logging program that makes a proper ADIF file works.',
        '<b>Hunters don\'t send logs.</b> POTA runs on the honor system: hunters get credit from the logs activators upload.',
        '<b>Be a good guest:</b> follow the law and the park\'s rules, listen to rangers, leave no trace, be courteous to other visitors, and follow the DX Code of Conduct.',
        '<b>Overlapping parks (2-fers):</b> where two POTA parks overlap, one contact can count for both. Parks that only touch at a border are not a 2-fer. A WWFF or SOTA reference on the same ground is a different program, not a 2-fer.',
    ], 'Sources: <a href="https://parksontheair.com/rules/" target="_blank" rel="noopener">parksontheair.com/rules</a> and the detailed rules at <a href="https://docs.pota.app/" target="_blank" rel="noopener">docs.pota.app</a>.' + DISCLAIM),
    steps('HOW TO START', '🚀 Your First Activation or Hunt', [
        ('📻 Activating', ['Pick a park: <a href="finder.html">KY Park Commander</a> or <a href="kpc-rare.html">Rarely Activated Parks</a>.',
                          'Read its <a href="kpc-park-notes.html">Park Notes</a> and open its <a href="kpc-kit.html">Activation Kit</a> (weather, parking, boundary).',
                          'Tell people you\'re going on the <a href="kpc-activations.html">Activation Board</a>.',
                          'At the park, check the line with <a href="kpc-in-park.html">Am I in the Park?</a>, then set up.',
                          'Spot yourself with <a href="kpc-spot-me.html">Spot Me</a>, call CQ POTA and log every contact.',
                          'Get 10 before the UTC day ends, then upload your ADIF log at pota.app.']),
        ('🎯 Hunting', ['Watch <a href="kpc-spots.html">On The Air Now</a> or <a href="kpc-live.html">Happening Now</a> for spots.',
                        'Check the <a href="kpc-activations.html">Activation Board</a> for planned activations, or post a park you need.',
                        'Call with your call sign once, give a signal report and your state, and listen for the park number.',
                        'Log it. Your credit shows up after the activator uploads their log.',
                        'See which parks you still need, in any state, with the <a href="kpc-checker.html">Park Checker</a> (it reads your hunter file from pota.app).']),
    ]),
    section('KENTUCKY GUIDES', '📚 Our Kentucky POTA Guides', 'Free club guides for every Kentucky POTA park.', [
        card('kpc-guide-pota.html?order=num', '📗', 'Kentucky POTA Resource (by number)', 'Every Kentucky park in park-number order, with its details, the other references on the same ground, and links.', 'you know the park number.'),
        card('kpc-guide-pota.html?order=az', '📘', 'Kentucky POTA Resource (A to Z)', 'The same guide sorted by park name.', 'you know the park\'s name.'),
        card('kpc-new-to-pota.html', '🔰', 'New to POTA?', 'Our beginner\'s walk-through: what to bring and how your first activation goes.', 'it\'s your very first time.'),
        card('kpc-guide-top25.html', '🏅', 'Top 25 Rare Kentucky Parks', 'The 25 parks with the fewest contacts and the 25 with the fewest activations, updated every week.', 'you want to be the activation hunters remember.'),
        card('kpc-park-notes.html', '📝', 'Park Notes', 'Tips from members for every park: where to set up, gates, cell signal, RF noise.', 'you want to know what a park is like before you go.'),
        card('kpc-campgrounds.html', '🏕', 'Campgrounds &amp; Cabins', 'Places to stay inside Kentucky POTA parks, with reviews.', 'you\'re making a weekend of it.'),
        card('kpc-park-sheet.html', '🖨', 'Printable Park Sheet', 'A one-page sheet for any Kentucky park with QR codes and an optional paper log.', 'you want paper backup in the field.'),
    ], alt=True, sid='guides'),
    section('POTA TOOLS', '🧰 Tools That Help', '', [
        card('kpc-spot-me.html', '📣', 'Spot Me', 'Post your POTA spot (and copy it for other spotting sites) from one form.', 'you\'re on the air and want hunters to find you.'),
        card('kpc-spots.html', '🔴', 'On The Air Now', 'Live POTA spots for Kentucky parks and KPC members.', 'you\'re hunting.'),
        card('kpc-tracker.html', '📊', 'Park Tracker', 'Kentucky parks activated by any call sign, plus the club leaderboard.', 'you\'re chasing all of Kentucky.'),
        card('kpc-recap.html', '📅', 'Monthly Recap', 'What KPC members activated in Kentucky each month.', 'you want to see what the club has been up to.'),
        card('kpc-map-room.html', '🗺', 'Map Room', 'Every map tool in one place.', 'you need a map of any kind.'),
    ], alt=True),
    section('OFFICIAL LINKS', '🔗 POTA Itself', '', [
        card('https://pota.app/', '🌐', 'pota.app', 'Spots, park pages, your account, log uploads and awards.', 'you\'re uploading a log or looking up a park\'s stats.', ext=True),
        card('https://parksontheair.com/', '🏞', 'parksontheair.com', 'The official POTA website: news, rules and how to get started.', 'you want the official word.', ext=True),
        card('https://docs.pota.app/', '📖', 'POTA Docs', 'The full rules, logging details, and how parks get added.', 'you have a detailed rules question.', ext=True),
    ]),
    other_rooms('kpc-pota-room.html'),
]))

# ================================================================== WWFF ROOM
PAGES['kpc-wwff-room.html'] = ('WWFF / KFF Room | KPC', 'World Wide Flora & Fauna (KFF in the USA) in plain words: what it is, the rules (44 contacts for WWFF awards), how to activate and hunt, Kentucky guides and tools.', ''.join([
    hero('hero-river-camp', 'KPC WWFF ROOM • WORLD WIDE FLORA &amp; FAUNA', 'WWFF', '&amp; KFF',
         'WWFF is a worldwide program for nature areas. In the USA it\'s called KFF, and many Kentucky POTA parks also have a KFF number, so you can often do both on one trip.',
         ['🌿 Nature areas', '🌎 Worldwide', '🦌 KFF = USA'],
         [('THE RULES ↓', '#rules'), ('HOW TO START ↓', '#how'), ('KENTUCKY GUIDES ↓', '#guides')]),
    '<section class="kb-sec"><div class="kb-in"><p class="kb-k">WHAT IT IS</p><h2>WWFF in a Minute</h2>'
    '<p class="kb-lead">WWFF stands for <b>World Wide Flora &amp; Fauna</b>. It\'s about operating from protected nature areas. Each country runs its own program; '
    'the USA\'s is <b>KFF</b>, and its references look like <b>KFF-1277</b>. It works a lot like POTA, but the numbers and logging are different.</p>'
    + nums([('44', 'contacts for WWFF activator awards (can add up over several visits)'), ('100%', 'of your equipment inside the area boundary'), ('1', 'reference at a time'), ('0', 'QSL cards needed')]) + '</div></section>',
    rules('THE RULES', '📜 The Main Rules', 'From the WWFF Global Rules. KFF (the US program) can have its own extra rules: check wwff.us.', [
        '<b>44 contacts</b> count an activation toward WWFF activator awards. They don\'t have to happen in one visit: you can add them up over several trips to the same reference. National programs like KFF may accept fewer for their own awards.',
        '<b>All of your equipment must be inside the area\'s boundary.</b> Part of the station inside isn\'t enough.',
        '<b>One reference at a time.</b> Where two WWFF areas overlap, pick one; you can start a new activity under the other one after you finish the first.',
        '<b>Send in your log even if you don\'t reach 44.</b> Log every contact (ADIF or the WWFF CSV template).',
        '<b>Activators don\'t upload their own logs to WWFF Logsearch.</b> Logs go to the national log manager (for KFF, see wwff.us for how to send yours).',
        '<b>Hunters:</b> every contact counts once the activator\'s log is in Logsearch, no matter how many contacts the activator made. No QSL cards needed.',
        '<b>Same ground as a POTA park?</b> A KFF reference sharing ground with a POTA park is a different program: you can log both on one trip, but that\'s not a POTA 2-fer.',
    ], 'Sources: <a href="https://wwff.co/wwff_cont/uploads/2025/09/WWFF-Global-Rules-V_5.10.pdf" target="_blank" rel="noopener">WWFF Global Rules v5.10</a> and <a href="https://wwff.co/rules-faq/how-to-activate-a-wwff-reference" target="_blank" rel="noopener">How to activate a WWFF reference</a>.' + DISCLAIM),
    steps('HOW TO START', '🚀 Your First KFF Activation or Hunt', [
        ('📻 Activating', ['Find a KFF reference: <a href="finder.html">KY Park Commander</a>, our <a href="kpc-guide-wwff.html">KFF guide</a>, or the <a href="kpc-park-info.html">Info Finder</a> for other states.',
                          'Check the boundary with <a href="kpc-in-park.html">Am I in the Park?</a> (it shows WWFF areas too).',
                          'Many Kentucky KFF areas are also POTA parks: log both programs at once.',
                          'Spot yourself with <a href="kpc-spot-me.html">Spot Me</a> (fill in the WWFF/KFF box) and call CQ.',
                          'Aim for 44 over one or more visits, then send your log the way wwff.us explains.']),
        ('🎯 Hunting', ['Watch the WWFF spots (Spot Me and <a href="kpc-live.html">Happening Now</a> link to them).',
                        'A POTA activator in a park with a KFF number is often activating KFF too: ask, or check the spot.',
                        'Log the contact with the KFF reference number.',
                        'Your credit shows up in WWFF Logsearch once the activator\'s log is uploaded.']),
    ]),
    section('KENTUCKY GUIDES', '📚 Our Kentucky KFF Guide', '', [
        card('kpc-guide-wwff.html', '📗', 'Kentucky WWFF / KFF Resource', 'Every Kentucky KFF reference with its details and links.', 'you\'re picking a KFF reference in Kentucky.'),
        card('kpc-new-to-wwff.html', '🔰', 'New to WWFF?', 'Our beginner\'s walk-through for WWFF and KFF.', 'it\'s your very first time.'),
        card('kpc-park-notes.html', '📝', 'Park Notes', 'Member tips for every park and KFF reference.', 'you want to know what a place is like.'),
    ], alt=True, sid='guides'),
    section('TOOLS', '🧰 Tools That Help', '', [
        card('kpc-park-info.html', '🏛', 'Park &amp; Summit Info Finder', 'Any WWFF reference worldwide: official website and boundary map.', 'you\'re outside Kentucky.'),
        card('kpc-in-park.html', '📍', 'Am I in the Park?', 'GPS check against official POTA and WWFF boundaries.', 'you want to be sure you\'re inside.'),
        card('kpc-kit.html', '🎒', 'Activation Kit', 'Everything for one WWFF area on one screen, saved for no signal.', 'you\'re heading out.'),
        card('kpc-spot-me.html', '📣', 'Spot Me', 'Copies your spot in the WWFF format and opens the WWFF spot page.', 'you\'re on the air.'),
    ], alt=True),
    section('OFFICIAL LINKS', '🔗 WWFF Itself', '', [
        card('https://wwff.co/', '🌐', 'wwff.co', 'The worldwide WWFF site: rules, the reference directory, Logsearch and awards.', 'you want the official word.', ext=True),
        card('https://wwff.co/wwff_cont/uploads/2025/09/WWFF-Global-Rules-V_5.10.pdf', '📖', 'WWFF Global Rules (PDF)', 'The full rules, version 5.10.', 'you have a detailed rules question.', ext=True),
        card('https://wwff.us/', '🦅', 'wwff.us (KFF)', 'The US program: references, how to send your log, and US awards.', 'you\'re activating in the USA.', ext=True),
    ]),
    other_rooms('kpc-wwff-room.html'),
]))

# ================================================================== SOTA ROOM
PAGES['kpc-sota-room.html'] = ('SOTA Room | KPC', 'Summits on the Air in plain words: what SOTA is, the rules (activation zone, 1 contact to log, 4 for points), how to activate and chase, Kentucky W4K guides and tools.', ''.join([
    hero('hero-mast', 'KPC SOTA ROOM • SUMMITS ON THE AIR', 'SUMMITS ON', 'THE AIR',
         'Hike to the top of a listed mountain, set up a small station and make contacts, or chase the people who do. Kentucky\'s summits are in the W4K association.',
         ['⛰ Activate', '🎯 Chase', '🥾 Kentucky W4K'],
         [('THE RULES ↓', '#rules'), ('HOW TO START ↓', '#how'), ('KENTUCKY GUIDES ↓', '#guides')]),
    '<section class="kb-sec"><div class="kb-in"><p class="kb-k">WHAT IT IS</p><h2>SOTA in a Minute</h2>'
    '<p class="kb-lead"><b>Activators</b> carry a station to a listed summit and make contacts from the top. <b>Chasers</b> work them. Every summit has a reference like <b>W4K/EC-001</b> '
    'and a points value set by its height. Summits are picked by how much they stand out from the land around them, not just how high they are.</p>'
    + nums([('25 m', '(80 ft) below the top: the activation zone'), ('1', 'contact logs an activation'), ('4', 'contacts earn the summit\'s points'), ('0', 'cars: no operating from or next to a vehicle')]) + '</div></section>',
    rules('THE RULES', '📜 The Main Rules', 'Plain-language summary. Read the SOTA General Rules and the W4K (Kentucky) Association Reference Manual before you go.', [
        '<b>Activation zone:</b> you must be within <b>25 m (about 80 ft)</b> of height below the very top of the summit.',
        '<b>1 contact</b> is enough to log an activation; <b>4 contacts</b> are needed to earn the summit\'s points. Making more doesn\'t add points.',
        '<b>No vehicles:</b> you can\'t operate from or close to a vehicle, and the trip up has to be on foot (or under your own power). Use legitimate access routes and follow the local land rules.',
        '<b>Log every contact</b> and upload your log to the SOTA database (sotadata).',
        '<b>Chasers</b> log their contacts in the SOTA database too, to earn chaser points.',
        '<b>Points</b> for each summit are in the summit list; some associations add a seasonal bonus. Check the W4K manual for Kentucky\'s.',
        '<b>Same ground as a POTA park?</b> A summit inside a POTA park is a different program: you can log both, but that\'s not a POTA 2-fer. For POTA you must still be inside the park boundary.',
    ], 'Sources: <a href="https://www.sota.org.uk/" target="_blank" rel="noopener">sota.org.uk</a> (General Rules and the W4K Association Reference Manual).' + DISCLAIM),
    steps('HOW TO START', '🚀 Your First Summit or Chase', [
        ('⛰ Activating', ['Pick a summit: our <a href="kpc-guide-sota.html">Kentucky SOTA guide</a> or the <a href="kpc-sota.html">SOTA Summit Map</a>.',
                         'Post an alert on SOTAwatch and the <a href="kpc-activations.html">Activation Board</a>, and check <a href="kpc-weather.html">Field Weather</a>.',
                         'Hike up. At the top, <a href="kpc-in-park.html">Am I in the Park?</a> shows whether you\'re inside the 25 m activation zone.',
                         'Set up away from your vehicle, spot yourself (<a href="kpc-spot-me.html">Spot Me</a> copies the SOTAwatch format) and call CQ SOTA.',
                         'Get at least 4 contacts, then upload your log at sotadata.']),
        ('🎯 Chasing', ['Watch SOTAwatch for spots and alerts (<a href="kpc-live.html">Happening Now</a> shows SOTA spots too).',
                        'Call once with your call sign, give a report, and listen for the summit reference.',
                        'Log the contact with the summit reference.',
                        'Upload your chaser log at sotadata to get your points.']),
    ]),
    section('KENTUCKY GUIDES', '📚 Our Kentucky SOTA Guide', '', [
        card('kpc-guide-sota.html', '📗', 'Kentucky SOTA (W4K) Resource', 'Every Kentucky summit with its details and the summits near it.', 'you\'re picking a Kentucky summit.'),
        card('kpc-new-to-sota.html', '🔰', 'New to SOTA?', 'Our beginner\'s walk-through for your first summit.', 'it\'s your very first time.'),
        card('kpc-park-notes.html', '📝', 'Park Notes', 'Member tips for every summit: trails, parking, where to set up.', 'you want to know the hike before you go.'),
    ], alt=True, sid='guides'),
    section('TOOLS', '🧰 Tools That Help', '', [
        card('kpc-sota.html', '⛰', 'SOTA Summit Map', 'Every summit in Kentucky or any US SOTA area; load your log to see what you\'ve done.', 'you\'re planning which summit is next.'),
        card('kpc-in-park.html', '📍', 'Am I in the Park?', 'Shows your height against the summit\'s and whether you\'re in the activation zone.', 'you\'re at the top.'),
        card('kpc-kit.html', '🎒', 'Activation Kit', 'Weather, bands, map and more for one summit, saved for no signal.', 'you\'re heading out.'),
        card('kpc-spot-me.html', '📣', 'Spot Me', 'Copies your spot in the SOTAwatch format and opens SOTAwatch.', 'you\'re on the air.'),
    ], alt=True),
    section('OFFICIAL LINKS', '🔗 SOTA Itself', '', [
        card('https://www.sota.org.uk/', '🌐', 'sota.org.uk', 'The official SOTA site: General Rules and each association\'s reference manual.', 'you want the official word.', ext=True),
        card('https://sotawatch.sota.org.uk/', '👀', 'SOTAwatch', 'Live spots and alerts.', 'you\'re chasing or posting an alert.', ext=True),
        card('https://www.sotadata.org.uk/', '🗄', 'SOTAdata', 'Upload logs and see your points and awards.', 'you\'re logging an activation or chase.', ext=True),
        card('https://sotl.as/', '🗺', 'SOTLAS', 'A map of every summit worldwide with activation history.', 'you want summit details and past activations.', ext=True),
    ]),
    other_rooms('kpc-sota-room.html'),
]))

if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
    for page, (title, desc, body) in PAGES.items():
        mf = os.path.join(HERE, 'out', page.replace('.html', '-main.html'))
        open(mf, 'w', encoding='utf-8').write('<link rel="stylesheet" href="kpc-boards.css?v=20261016b"><link rel="stylesheet" href="kpc-rooms.css?v=20261016a">\n@@HEADER@@\n<main class="kb rm">' + body + '</main>\n@@FOOTER@@\n')
        subprocess.run(['python3', os.path.join(REPO, '.claude/build/assemble.py'), mf, page, title, desc], cwd=REPO, check=True)
