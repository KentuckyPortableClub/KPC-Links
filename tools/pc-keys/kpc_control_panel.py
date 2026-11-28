#!/usr/bin/env python3
"""KPC control panel: one page with a button for every PC tool, in the order the work goes.

Double-click "KPC CONTROL PANEL.bat" (in the Tools folder). A small window starts the panel and your web browser opens it.
Each button starts the tool's own .bat file in its OWN window, exactly as if you double-clicked it, so two tools can run at
once. Two jobs that change the same files are not started together (the second button waits). Close the small panel
window to close the panel; tools already started keep running.

The page lives only on this PC (address 127.0.0.1, which nothing outside the PC can open) and every button carries a secret
made fresh at each start, so no web site can press a button. It only starts the .bat files listed below: never a typed
command. Python standard library only.

  py -3 kpc_control_panel.py            start the panel and open the browser
  py -3 kpc_control_panel.py --check    print every button, whether its file is here, and the "what next" lines
"""
import datetime, glob, html, json, os, pathlib, secrets, subprocess, sys, threading, time, urllib.parse, webbrowser, zipfile
import http.server

VERSION = 'KPC control panel 2026-11-27a'
ROOT = pathlib.Path(os.environ.get('KPC_TOOLS_ROOT') or pathlib.Path(__file__).resolve().parent)

FOLDERS = {   # tool folders, from the tools folder. 26 Nov: 'new name|old name', the first that exists is used
    'store': r'..\3-MAP-STORE-US-CA|KPC-TOOLS-NOV14\1-STORE-TOOL\kpc-outline-store-full',
    'world': r'..\4-MAP-STORE-WORLD|kpc-outline-store-world-v4\kpc-outline-store-world',
    'bots': r'PAGE-READER|KPC-PC-BOTS-NOV21',
    'ids': r'PARK-ID-MATCHER|KPC-ID-crosswalk',
    'fers': r'2FER-FINDER-V1|kpc-fers-pc-v1.2\kpc-fers-pc',
    'ferbot': r'2FER-FINDER|KPC-2FER-PC-RUNNER\KPC-2FER-PC-RUNNER',
    'hand': r'FILE-HAND-DOWNLOADS|KPC-TOOLS-NOV14\3-HAND-HELPER\kpc-hand-helper',
    'trace': r'TRACE-TEST|KPC-TRACE-TEST',
    'keys': r'..\5-ANSWER-KEY-TEST|..\key builder files',   # the PC test keys (next to the tools folder)
    'house': r'HOUSEKEEPING',          # sizes, clean-up (archive, never delete), fix paths, layer guide, back-up
}

# (section, id, button, what it does, folder, .bat, where its results go (newest = last finished))
JOBS = [
    # 27 Nov 2026 (owner: 'update the html ... so we know what fables updates do'): the three main buttons the matching chat
    # made on 26-27 Nov come first, in the order to use them. Each asks 1 status / 2 / 3 and writes one status page.
    ('0. Start here: the main buttons, in this order', 'layerrec', 'Store room: 1 status, 2 rebuild, 3 download what is missing (LAYER-RECORDS)',
     'The layer files the keys read. Start with 1 (status, no internet) and do what its last lines say. 2 rebuilds the layer files from what is already downloaded (no internet). 3 downloads only what is missing: it shows the list and waits for your Y. Every choice writes results\\STORE-ROOM-STATUS.txt.',
     'store', 'LAYER-RECORDS.bat', ['results/STORE-ROOM-STATUS.txt']),
    ('0. Start here: the main buttons, in this order', 'pagereader', 'Page reader: 1 status, 2 re-read kept pages, 3 read what is missing (PAGE-READER)',
     'Park web pages. 1 = status, what is read and what is not (no internet). 2 = read the pages already kept on this PC again with the newest rules (no internet; do it after every reader fix). 3 = read only what is missing or failed, and the slow sites as slowly as they ask; it can run all night. The page browser is switched on when it is installed. Writes PAGE-READER-STATUS.txt.',
     'bots', 'PAGE-READER.bat', ['PAGE-READER-STATUS.txt']),
    ('0. Start here: the main buttons, in this order', 'v2prep', 'New key (v2): prepare a state',
     'Type one state, several, or US. Reads the saved layers and park facts, finds the fields that carry the parks\' ids and names, and proposes rule-table rows. Changes nothing, no internet. Run it before the first build of a new state.',
     'keys', 'V2-STATE-PREP.bat', ['reports/v2-prep-*/STATE-PREP-*.txt']),
    ('0. Start here: the main buttons, in this order', 'v2build', 'New key (v2): build',
     'Builds the new key for the states or provinces you pick, from today\'s saved layer files only, twice each to check the locks, and compares with the old key where there is one. Never downloads, uploads or publishes. The answer: V2-BUILD-SUMMARY.txt in the newest folder inside v2-keys.',
     'keys', 'V2-BUILD.bat', ['v2-keys/*/V2-BUILD-SUMMARY.txt']),
    ('0. Start here: the main buttons, in this order', 'v2side', 'New key (v2): side by side with your last old-key test',
     'About 2 minutes for MN NY. The answer is the first line of reports\\v2-...\\V2-SCORECARD.txt: V2 PASSES or V2 DOES NOT PASS YET.',
     'keys', 'V2-SIDE-BY-SIDE.bat', ['reports/v2-*/V2-SCORECARD.txt']),
    ('1. Collect information', 'pages', 'Read park web pages (older button: PAGE-READER choice 3 does this now)', 'Reads each park\'s own web page for its name, size, manager and maps. Likely wrong matches first. Up to 3 hours a run; it carries on where it stopped. Pages that build themselves are opened in the page browser once it is installed.',
     'bots', '2-READ-PARK-PAGES.bat', ['page-reader/out/summary.md']),
    ('1. Collect information', 'tonight', 'Run everything tonight (older button: read, find own pages, slow sites, map points, upload pack)', 'One window, no pauses: reads park pages, looks for the own pages of parks with no good link, reads the slow sites, turns addresses into map points and makes the upload pack. Start it before bed.',
     'bots', 'RUN-ALL-TONIGHT.bat', ['SEND-BACK/kpc-upload-pack-*.zip']),
    ('1. Collect information', 'reread', 'Read the kept pages again (older button: PAGE-READER choice 2 does this now)', 'Reads the pages already saved on this PC again with the newest reader, so a reader fix reaches every park. Asks no website. Run it after a reader update.',
     'bots', '2e-REREAD-KEPT-PAGES.bat', ['page-reader/out/summary.md']),
    ('1. Collect information', 'findown', 'Find own pages (parks with no link, a dead link or only the front page)', "Looks on the agency's own site for the park's own page; keeps it only on a sure match. robots.txt always wins.",
     'bots', '2f-FIND-OWN-PAGES.bat', ['page-reader/out/found-links-summary.txt']),
    ('1. Collect information', 'names', 'Find the real names (parks whose name may not match)', 'Reads the pages already kept on this PC again, only for parks with a possible name problem, and saves every name the page calls the park. No website is asked.',
     'bots', '2h-FIND-REAL-NAMES.bat', ['page-reader/out/name-refs.json']),
    ('1. Collect information', 'slow', 'Read the slow sites (older button: PAGE-READER choice 3 does this now)', 'Reads the parks whose sites ask for long waits between pages, slowly, as they ask.',
     'bots', '2g-READ-SLOW-SITES.bat', ['page-reader/out/summary.md']),
    ('1. Collect information', 'uploadpack', 'Make the upload pack (after reading park pages)', 'Packs the page facts of finished areas and the crosswalk of the agencies you allowed (upload-approved-agencies.txt) into one file in SEND-BACK. Nothing uploads: you put it on KPC-Data (intake-files, pc-upload) and run "KPC PC upload pack (by hand)".',
     'bots', '5-MAKE-UPLOAD-PACK.bat', ['SEND-BACK/kpc-upload-pack-*.zip']),
    ('1. Collect information', 'pagebrowser', 'Page reader: install the page browser (once)', 'Some park pages build themselves in a browser and look empty to the reader. This adds a hidden browser (about 150 MB) so the reader reads those too, with the same manners. Asks YES first.',
     'bots', '0-INSTALL-PAGE-BROWSER.bat', []),
    ('1. Collect information', 'agencylists', 'Download agency park lists', 'Downloads each agency\'s own list of its parks (rows only, no maps) for the matching below. Asks YES first.',
     'store', 'A-READ-AGENCY-LISTS.bat', ['results/agency-lists/agency-lists-read.csv']),
    ('1. Collect information', 'fetch', 'Download map layers (only what is new)', 'Downloads the official park outlines the store does not have yet. Anything already on this PC is never asked for again, so a second run is short. Polite and slow; safe to stop and run again. Asks YES first.',
     'store', '2-FETCH-ALL.bat', ['results/report/SUMMARY-ALL.txt']),
    ('1. Collect information', 'terms', 'Read layer licences', 'Reads only the licence words of layers already on this PC, so we know what may be published.',
     'store', 'L-READ-TERMS.bat', ['results/report/licence-tool-classes-ALL.csv']),
    ('1. Collect information', 'handlist', 'Show the files to download by hand', 'Lists the layers a person must download in a browser (the site does not allow programs), with the page to open.',
     'hand', '1-SHOW-LIST.bat', []),
    ('1. Collect information', 'handdl', 'Help me download those files', 'Opens each hand-download page in turn and files what you saved in the right place.',
     'hand', '2-START-DOWNLOADS.bat', []),
    ('2. Make the map', 'plan', 'How much is new to download? (downloads nothing)', 'Counts what the store would still have to download, server by server, and about how long it would take. Nothing is downloaded. Run this first: if it says nothing or very little is new, a restock is quick.',
     'store', '1-PLAN-ALL.bat', ['results/report/plan-ALL.txt', 'results/SEND-BACK/plan-ALL.txt']),
    ('2. Make the map', 'restock', 'Restock the store (download what is new, then build)', 'The two steps a restock needs, one after the other: "Download map layers (only what is new)", then "Build the map store". No compare. Asks YES before downloading; press a key between the steps.',
     'store', 'RESTOCK-STORE.bat', ['results/store/*.kpcstore.json.gz']),
    ('2. Make the map', 'build', 'Build the map store (US + Canada)', 'Makes every park outline from what is downloaded. No internet. Type the states in areas.txt to do only those.',
     'store', '3-BUILD-ALL.bat', ['results/store/*.kpcstore.json.gz']),
    ('2. Make the map', 'all', 'Everything in one go (download, build, compare, count)', 'Download, build, compare with the live map and list, one YES for all. For a plain restock use "Restock the store" instead (no compare). Stops at the first step that fails and says which.',
     'store', 'RUN-ALL.bat', ['results/report/SUMMARY-ALL.txt']),
    ('2. Make the map', 'compare', 'Compare my map with the live map (not needed for a restock)', 'Shows what is new or different from the map on the website today. Only useful when you want to see the changes; a restock and the sync do not need it.',
     'store', '3b-COMPARE.bat', ['results/report/compare-ALL.csv']),
    ('2. Make the map', 'publishable', 'Count what we may publish', 'Counts the parks whose licences allow them on the website.',
     'store', '4-LIST-PUBLISHABLE.bat', ['results/report/publishable-ALL.csv']),
    ('2. Make the map', 'worldall', 'World map: download + build', 'The same for the rest of the world. One YES for all.',
     'world', 'RUN-ALL.bat', ['results/report/SUMMARY-ALL.txt']),
    ('2. Make the map', 'worldbuild', 'World map: build only', 'Builds the world outlines from what is downloaded. No internet.',
     'world', '3-BUILD-ALL.bat', ['results/store/*.kpcstore.json.gz']),
    ('3. Check the matches', 'mismatch', 'Find likely wrong matches', 'Checks every park against its map record (inside? the right size?) and makes the private lists the readers use first.',
     'bots', '1-MAKE-PRIVATE-LISTS.bat', ['PRIVATE/priority-parks.csv']),
    ('3. Check the matches', 'idmatch', 'Match web links and agency lists to map records', 'Checks that the ID in each park\'s web link, and in the agency\'s own list, is on the map record we joined. Confirms parks or flags wrong joins. No internet.',
     'ids', 'RUN.bat', ['crosswalk-out/*/summary.txt', 'agency-fields-out/*/summary.txt']),
    ('3. Check the matches', 'testkeys', 'Test the OLD answer keys on this PC (START-HERE)', 'Builds the answer keys from the saved copies only and writes reports\\test-...\\REPORT.txt (counts only). Adds any new kit update first. Nothing is downloaded or published.',
     'keys', 'START-HERE.bat', ['reports/*/REPORT.txt']),
    ('3. Check the matches', 'crossstate', 'Get the cross-state pieces (once)', "Asks the agencies once, slowly, for the few park pieces across a state line (rule W11, your one-time OK of 23 Nov), then adds them to this PC's saved copies. Run START-HERE after it.",
     'keys', 'GET-CROSS-STATE.bat', ['cross-state-report.txt']),
    ('4. 2-fers', 'fers', 'Find 2-fers from my map store', 'Finds overlapping parks from the outlines on this PC. Results stay on this PC (club room only).',
     'fers', '1-FIND-2FERS.bat', ['results/SUMMARY.txt']),
    ('4. 2-fers', 'ferscompare', 'Compare 2-fers with the live list', 'Shows which 2-fers are new or gone against the website today.',
     'fers', '2-COMPARE-WITH-TODAY.bat', ['results/COMPARE-SUMMARY.txt']),
    ('4. 2-fers', 'ferbotcode', 'GitHub 2-fer bot: get its code', 'Once, and after a code change: downloads the 2-fer bot\'s exact code from GitHub.',
     'ferbot', '1-GET-CODE.bat', ['repos']),
    ('4. 2-fers', 'ferbot', 'GitHub 2-fer bot: run it here (US + Canada)', 'Runs the same 2-fer bot GitHub runs, on this PC\'s map store, to catch it up.',
     'ferbot', '2-RUN-2FERS.bat', ['RESULTS']),
    ('4. 2-fers', 'ferbotworld', 'GitHub 2-fer bot: run it here (world)', 'The same for the world map store.',
     'ferbot', '3-RUN-WORLD-2FERS.bat', ['RESULTS']),
    ('4. 2-fers', 'ferbotcheck', 'GitHub 2-fer bot: check and summary', 'Checks the bot\'s results and writes the summary to send back.',
     'ferbot', '4-CHECK-AND-SUMMARY.bat', ['RESULTS']),
    ('5. Research (suggestions only; a person decides)', 'findright', 'Find the right record for wrong matches', 'For each likely wrong match, asks the layer the park is joined to which records hold the park\'s pin and are named for it. Mark ALSO / INSTEAD / NO, then "Apply what I marked". Asks YES first; carries on where it stopped.',
     'store', 'R1-FIND-RIGHT-RECORDS.bat', ['results/research/right-records-summary.txt']),
    ('5. Research (suggestions only; a person decides)', 'findlayers', 'Find map layers for parks with no outline', 'Looks for a public map layer with a record named for the park at its pin: the park\'s own pages first, then ArcGIS Online, then the state open-data portals and the boundary files already on this PC (a portal file it lacks is downloaded once). Mark YES / NO, then "Apply what I marked".',
     'store', 'R2-FIND-MAP-LAYERS.bat', ['results/research/layer-candidates-summary.txt']),
    ('5. Research (suggestions only; a person decides)', 'apply', 'Apply what I marked', 'Takes your answers in the "your answer" column (right records: ALSO / INSTEAD / NO; map layers: YES / NO) and changes the matches on this PC. Shows the plan, asks YES, keeps a backup. Then build the map store.',
     'store', 'R4-APPLY-WHAT-I-MARKED.bat', ['results/research/apply-summary.txt']),
    ('5. Research (suggestions only; a person decides)', 'undoapply', 'Undo the last apply', 'Puts the files back as they were before the last "Apply what I marked".',
     'store', 'R5-UNDO-LAST-APPLY.bat', []),
    ('5. Research (suggestions only; a person decides)', 'licdrafts', 'Draft licence notes', 'For each layer whose licence is unclear, quotes its own terms words and drafts a class for a person to settle. No internet.',
     'store', 'R3-DRAFT-LICENCE-NOTES.bat', ['results/research/licence-drafts.csv']),
    ('5. Research (suggestions only; a person decides)', 'sortnames', 'Sort the name questions', 'Puts the page reader\'s "name differs" questions in groups, so only the real differences go to a person. Runs by itself after each page-reader run too.',
     'bots', '3-SORT-NAME-QUESTIONS.bat', ['page-reader/out/name-differs-sorted.csv']),
    ('5. Research (suggestions only; a person decides)', 'picmaps', 'Save picture maps', 'For parks with no outline, collects picture maps: your own PDFs (Tools\\picture-maps\\my-pdfs, named starting with the park number), the maps already on GitHub, and the PDF links found on the parks\' own pages. Deleted once the park gets an outline.',
     'bots', '4-SAVE-PICTURE-MAPS.bat', ['../picture-maps/index.json']),
    ('6. Tracing (approximate; nothing goes on the map)', 'traceinstall', 'Tracing: install its packages (once)', 'The tracer needs free Python packages (about 200 MB). Asks YES first.',
     'trace', '0-INSTALL-PACKAGES.bat', []),
    ('6. Tracing (approximate; nothing goes on the map)', 'tracetest', 'Tracing accuracy test', 'Traces parks that already have official outlines from their agency picture maps, blind, and measures each trace against the real outline. Says if the bar is met.',
     'trace', '1-RUN-TRACE-TEST.bat', ['reports/*/bar.txt']),
    ('6. Tracing (approximate; nothing goes on the map)', 'traceheld', 'Trace parks with no outline (held)', 'Traces the parks with no outline from the picture maps saved on this PC. Every trace is held in Tools\\traces, never on a map, until you rule.',
     'trace', '2-TRACE-PARKS-WITH-NO-OUTLINE.bat', ['../traces/report.csv']),
    ('7. Keep it tidy', 'sizes', 'Folder sizes (one line)', 'How big the KPC folder is and how much it grew since last time. The panel also does this by itself when a tool finishes (the line at the top), and when it starts it empties TEMP of files older than 7 days.',
     'house', '1-SIZES.bat', ['sizes.csv']),
    ('7. Keep it tidy', 'cleanup', 'Clean up: old copies to the archive', 'Shows the old copies (kit zips already added, older test reports, old .before copies, exact duplicates, retired folders) and moves them to the archive after you type YES. Keeps the newest ones and test-2026-11-25-2245. Never touches the layers, the originals or the map store.',
     'house', '2-CLEAN-UP.bat', ['../../ARCHIVE/*/moved.csv']),
    ('7. Keep it tidy', 'undoclean', 'Undo the last clean-up', 'Puts everything the last clean-up moved back where it was.',
     'house', '3-UNDO-CLEAN-UP.bat', ['../../ARCHIVE/*/undone.csv']),
    ('7. Keep it tidy', 'fixpaths', 'Fix paths after a move', 'After a new drive letter or folder name: shows every settings line that still names the old place (D:\\...) and rewrites it to this folder after you type YES. The old lines are kept.',
     'house', '4-FIX-PATHS.bat', ['fix-paths-log.txt']),
    ('7. Keep it tidy', 'layerguide', 'Layer guide (answer key for every layer code)', 'One row per layer code: plain name, agency, area, which key uses it, and what this PC holds of it (whole-layer files, complete or not, your hand files, Layers-TIDY). Saves over LAYER-GUIDE.csv and opens LAYER-GUIDE.html (type to search).',
     'house', '5-LAYER-GUIDE.bat', ['LAYER-GUIDE.html']),
    ('7. Keep it tidy', 'backup', 'Back up to an outside drive', 'Copies the whole KPC folder to the drive letter you type (copy only; a second run copies only what changed).',
     'house', '6-BACK-UP.bat', ['BACKUP-LOG.txt']),
    ('7. Keep it tidy', 'dupes', 'Remove duplicate layer files', 'Finds layer files that are exactly the same, byte for byte, in the layer folders (map layers and new downloads). Shows the list, then after you type YES removes the extra copies for good. One copy of each always stays (the one in Originals first). Never Private.',
     'house', '7-DUPLICATE-LAYERS.bat', ['duplicates-removed.csv']),
]
# 27 Nov 2026 (owner: 'make notes somewhere so we know what fables updates do'): the long version is C:\\KPC\\7-NOTES\\WHAT-CHANGED.txt
CHANGES = [
    ('What changed lately (26-27 Nov). The full notes: 7-NOTES\\WHAT-CHANGED.txt', 'New key (v2)', 'A new, simpler key builder. It reads only today\'s layer files, the park facts and one rule table: no old answers carried forward. Your MN NY run passed (MN 295, NY 819 outlined) and it gave no park another unit\'s land (the old key gave 29 parks about 402,000 acres that were not theirs). The old key is not changed.'),
    ('What changed lately (26-27 Nov). The full notes: 7-NOTES\\WHAT-CHANGED.txt', 'Store room (LAYER-RECORDS)', 'One button with 1 status / 2 rebuild / 3 download. Fixed: one empty record blocked a whole state (MA, NC), the wrong id column (Iowa, MN, WI), Canada layers read twice, national layers saved whole in a state file, failed downloads that still counted as fresh.'),
    ('What changed lately (26-27 Nov). The full notes: 7-NOTES\\WHAT-CHANGED.txt', 'Page reader (PAGE-READER)', 'One button with 1 status / 2 re-read / 3 read what is missing. Fixed: about 5,000 parks counted as read when the site sent nothing, headings saved as names, square km saved as acres, failed reads that could wipe good facts, and the page browser was never switched on overnight. Sites that stop answering are read through the page browser.'),
    ('What changed lately (26-27 Nov). The full notes: 7-NOTES\\WHAT-CHANGED.txt', 'The site rule (your ruling)', 'Only a real robots.txt Disallow line is a no. A 401 / 403 is that page only, for that run. Five in a row from one site, or one 429, stops that site for the run. Nothing is carried into the next run.'),
]
NOT_YET = [
    ('8. Not on this PC yet', "Build the website's answer keys", '"Test the answer keys" above builds them on this PC for checking only. The website build is a long chain of GitHub steps (saved copies, gates, freeze, overlay). Waits for the patches and your word to lift NO BUILDING.'),
    ('8. Not on this PC yet', 'Move approved traces to the map store', 'Only after the tracing test passes and you rule. Traces would go in as approximate, never official, never a 2-fer.'),
    ('8. Not on this PC yet', 'Upload by itself', 'The PC never uploads on its own: "Make the upload pack" makes the file, you carry it up.'),
]
SEND = [   # small, shareable results only (never the store, the cache, or a PRIVATE file)
    ('store', 'results/SEND-BACK/*'), ('store', 'results/report/SUMMARY-ALL.txt'), ('store', 'results/report/publishable-ALL.csv'),
    ('store', 'results/agency-lists/agency-lists-read.csv'), ('ids', 'crosswalk-out/*/summary.txt'), ('ids', 'crosswalk-out/*/pairs.csv'),
    ('ids', 'crosswalk-out/*/by-area.csv'), ('ids', 'agency-fields-out/*/summary.txt'), ('ids', 'agency-fields-out/*/columns.csv'),
    ('ids', 'agency-fields-out/*/proposed-agency-lists.json'), ('bots', 'page-reader/out/summary.md'), ('bots', 'page-reader/out/run.json'),
    ('bots', 'SEND-BACK/counts-to-share.txt'), ('bots', 'PRIVATE/counts-to-share.txt'), ('fers', 'results/SUMMARY.txt'), ('fers', 'results/COMPARE-SUMMARY.txt'),
    ('fers', 'results/run.json'), ('world', 'results/report/SUMMARY-ALL.txt'),
    ('store', 'results/research/right-records-summary.txt'), ('store', 'results/research/layer-candidates-summary.txt'),
    ('trace', 'reports/*/bar.txt'), ('trace', 'reports/*/t1-summary.md'),
    ('store', 'results/research/apply-summary.txt'), ('store', 'results/research/portal-files-to-look-at.csv'),
    ('store', 'results/research/licence-drafts-summary.txt'), ('store', 'results/research/licence-drafts.csv'), ('bots', 'page-reader/out/name-differs-counts.txt'),
]
SEND_NEVER = ('private', '.kpcstore', 'store/', 'cache', 'fetch-state')


def folder(key):
    cands = [ROOT / pathlib.Path(*c.split('\\')) for c in FOLDERS[key].split('|')]
    return next((c for c in cands if c.exists()), cands[0])


def newest(key, pats):
    """The newest file (or folder) among a job's result patterns, newest first per pattern (a folder of runs: its newest run)."""
    best = None
    for p in pats:
        for f in glob.glob(str(folder(key) / p)):
            try: t = os.path.getmtime(f)
            except OSError: continue
            if best is None or t > best: best = t
    return best


def when(t):
    if not t: return 'not run yet'
    d = datetime.datetime.fromtimestamp(t)
    today = datetime.date.today()
    day = 'today' if d.date() == today else 'yesterday' if d.date() == today - datetime.timedelta(days=1) else d.strftime('%a %d %b')
    return f'{day} {d.strftime("%I:%M %p").lstrip("0")}'


def next_steps():
    """Plain-word hints from the results' dates. Each is a suggestion; nothing is started."""
    out = []
    kd = folder('keys')   # 26 Nov: a kit update that START-HERE has not added yet
    waiting = sorted(z.stem for z in kd.glob('kpc-kit-update-*.zip') if not (kd / 'links' / f'.done-{z.stem}').exists())
    if waiting: out.append(('testkeys', f'Test the answer keys: kit {waiting[-1].replace("kpc-kit-update-", "")} is waiting (START-HERE adds it first).'))
    st = folder('bots') / 'page-reader' / 'out' / 'state.json'
    try:
        left = len(json.loads(st.read_text(encoding='utf-8')).get('left') or [])
        if left: out.append(('pagereader', f'Page reader, choice 3: {left:,} parks still to read (it carries on where it stopped).'))
    except (OSError, ValueError): pass
    store = newest('store', ['results/store/*.kpcstore.json.gz'])
    lists = newest('store', ['results/agency-lists/*.json.gz'])
    matched = newest('ids', ['agency-fields-out/*'])
    if lists and (not matched or lists > matched):
        out.append(('idmatch', 'Match web links and agency lists to map records: new agency lists are here.'))
    hand = newest('store', ['have/*/*'])
    if hand and store and hand > store:
        out.append(('build', 'Build the map store: files were added to the have folder after the last build.'))
    pl = newest('bots', ['PRIVATE/priority-parks.csv'])
    if store and (not pl or store > pl):
        out.append(('mismatch', 'Find likely wrong matches: the map store changed since the lists were made.'))
    fers = newest('fers', ['results/SUMMARY.txt'])
    if store and (not fers or store > fers):
        out.append(('fers', 'Find 2-fers from my map store: the map store changed since the last 2-fer run.'))
    try:   # 22 Nov: the walk is finished and the page facts are newer than the last upload pack
        stj = json.loads((folder('bots') / 'page-reader' / 'out' / 'state.json').read_text(encoding='utf-8'))
        facts = newest('bots', ['page-reader/out/facts/*.json']); pack = newest('bots', ['SEND-BACK/kpc-upload-pack-*.zip'])
        if not (stj.get('left') or []) and facts and (not pack or facts > pack):
            out.append(('uploadpack', 'Make the upload pack: the page reader finished, and its results are newer than the last pack. Then carry it up to GitHub.'))
    except (OSError, ValueError): pass
    q = newest('bots', ['page-reader/out/questions.csv']); qs = newest('bots', ['page-reader/out/name-differs-sorted.csv'])
    if q and (not qs or q > qs): out.append(('sortnames', 'Sort the name questions: the page reader wrote new questions.'))
    sl = newest('store', ['results/report/second-look-list.csv']); ld = newest('store', ['results/research/licence-drafts.csv'])
    if sl and (not ld or sl > ld): out.append(('licdrafts', 'Draft licence notes: the second-look list changed.'))
    rr = newest('store', ['results/research/right-records-state.json'])
    if pl and (not rr or pl > rr): out.append(('findright', 'Find the right record for wrong matches: new likely wrong matches are on the list.'))
    return out


def make_send_zip():
    """Zip the small shareable results into Tools\\TO-CLAUDE\\. -> (path, files)."""
    dest = ROOT / 'TO-CLAUDE'
    dest.mkdir(exist_ok=True)
    zp = dest / f'to-claude-{datetime.datetime.now().strftime("%Y-%m-%d-%H%M")}.zip'
    files = []
    for key, pat in SEND:
        got = sorted(glob.glob(str(folder(key) / pat)), key=lambda f: os.path.getmtime(f))
        if '*/' in pat: got = got[-1:]          # a folder of runs: only the newest run's file
        for f in got:
            rel = os.path.relpath(f, ROOT).replace('\\', '/')
            if any(w in rel.lower() for w in SEND_NEVER) and not rel.lower().endswith('counts-to-share.txt'): continue
            if os.path.isfile(f) and os.path.getsize(f) < 30_000_000: files.append((f, rel))
    with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
        for f, rel in files: z.write(f, rel)
    return zp, [r for _, r in files]


_SIZE = {'busy': False}


def refresh_sizes():
    """26 Nov: the one-line folder size (and TEMP emptied of old files) in the background: at start and when a tool finishes."""
    if _SIZE['busy'] or not (folder('house') / 'kpc_housekeeping.py').is_file(): return
    _SIZE['busy'] = True

    def go():
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location('kpc_housekeeping', folder('house') / 'kpc_housekeeping.py')
            m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
            m.temp(quiet=True); m.sizes(quiet=True)
        except Exception: pass   # noqa: BLE001 (a size line is never worth stopping the panel for)
        finally: _SIZE['busy'] = False
    threading.Thread(target=go, daemon=True).start()


def size_line():
    try: return (folder('house') / 'size-line.txt').read_text(encoding='utf-8').strip()
    except OSError: return ''


class Runner:
    """Starts a job's .bat in its own window and remembers it until that window closes."""
    def __init__(self, fake=False):
        self.fake, self.running, self.lock = fake, {}, threading.Lock()

    def busy(self):
        with self.lock:
            for j in list(self.running):
                if self.running[j].poll() is not None:
                    del self.running[j]
                    if not self.fake: refresh_sizes()
            return dict((j, JOB[j][4]) for j in self.running)

    def start(self, jid):
        job = JOB.get(jid)
        if not job: return 'no such button'
        b = self.busy()
        if jid in b: return 'already running'
        same = [JOB[j][2] for j in b if clash(jid, j)]
        if same: return f'waits: "{same[0]}" is using the same files'
        fd = folder(job[4])
        if not (fd / job[5]).is_file(): return f'{job[5]} is not in {fd}'
        if self.fake: p = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(8)'], cwd=str(fd))
        else: p = subprocess.Popen(['cmd.exe', '/c', job[5]], cwd=str(fd), creationflags=getattr(subprocess, 'CREATE_NEW_CONSOLE', 0))
        with self.lock: self.running[jid] = p
        return 'started'


JOB = {j[1]: j for j in JOBS}

# What each job writes and reads: two jobs wait for each other only when one WRITES what the other writes or reads.
# (Reading the same thing at once is fine, so the page reader and the 2-fer finder can run while you check matches.)
USES = {
    'pages': ({'pages'}, {'page-browser'}), 'pagebrowser': ({'page-browser'}, set()), 'agencylists': ({'store-net', 'agency-lists'}, set()), 'fetch': ({'store-net'}, {'store-hand'}),
    'terms': ({'store-net'}, set()), 'handlist': (set(), {'hand'}), 'handdl': ({'hand', 'store-have'}, set()),
    'build': ({'store-map', 'store-report'}, {'store-net', 'store-have', 'store-hand'}), 'all': ({'store-net', 'store-map', 'store-report'}, {'store-have', 'store-hand'}),
    'apply': ({'store-hand'}, {'research-r1', 'research-r2'}), 'uploadpack': ({'upload'}, {'pages', 'ids', 'agency-lists'}), 'undoapply': ({'store-hand'}, set()),
    'compare': ({'store-report'}, {'store-map'}), 'publishable': ({'store-report'}, {'store-map'}),
    'worldall': ({'world-net', 'world-map'}, set()), 'worldbuild': ({'world-map'}, {'world-net'}),
    'mismatch': ({'lists'}, {'store-map'}), 'idmatch': ({'ids'}, {'agency-lists'}),
    'fers': ({'fers'}, {'store-map', 'world-map'}), 'ferscompare': ({'fers'}, set()),
    'findright': ({'store-net', 'research-r1'}, {'store-map', 'lists'}), 'findlayers': ({'store-net', 'research-r2'}, {'store-report', 'pages'}),
    'licdrafts': ({'research-r3'}, {'store-map', 'store-report'}), 'sortnames': ({'names'}, {'pages'}), 'picmaps': ({'pics'}, {'pages', 'store-map'}),
    'traceinstall': ({'trace-pkgs'}, set()), 'tracetest': ({'trace-work'}, {'trace-pkgs', 'store-map', 'pages'}),
    'traceheld': ({'trace-held'}, {'trace-pkgs', 'pics'}),
    'tonight': ({'pages', 'upload'}, {'page-browser'}), 'reread': ({'pages'}, {'page-browser'}), 'findown': ({'pages'}, set()), 'slow': ({'pages'}, set()),
    'testkeys': ({'keys'}, {'store-layerfiles'}), 'crossstate': ({'keys'}, set()),
    'layerrec': ({'store-net', 'store-layerfiles'}, set()), 'pagereader': ({'pages'}, {'page-browser'}), 'names': ({'pages'}, set()),
    'v2prep': ({'v2'}, {'store-layerfiles'}), 'v2build': ({'v2'}, {'store-layerfiles'}), 'v2side': ({'v2'}, {'keys', 'store-layerfiles'}), 'sizes': ({'sizes'}, set()), 'layerguide': ({'guide'}, {'store-layerfiles'}),
    'backup': ({'backup'}, set()),
    'ferbotcode': ({'ferbot'}, set()), 'ferbot': ({'ferbot'}, {'store-map'}), 'ferbotworld': ({'ferbot'}, {'world-map'}), 'ferbotcheck': ({'ferbot'}, set()),
}


EXCLUSIVE = {'cleanup', 'undoclean', 'fixpaths', 'dupes'}   # 26 Nov: they move or rewrite other tools' files: they wait for every tool, and every tool waits for them


def clash(a, b):
    if a in EXCLUSIVE or b in EXCLUSIVE: return True
    wa, ra = USES.get(a, ({a}, set())); wb, rb = USES.get(b, ({b}, set()))
    return bool(wa & (wb | rb) or wb & ra)


_NEXT = {'t': 0, 'v': []}


def status(runner):
    b = runner.busy()
    if time.time() - _NEXT['t'] > 20: _NEXT.update(t=time.time(), v=next_steps())
    return {'jobs': {j[1]: {'last': when(newest(j[4], j[6])), 'here': (folder(j[4]) / j[5]).is_file(), 'running': j[1] in b,
                            'waits': next((JOB[x][2] for x in b if x != j[1] and clash(j[1], x)), '')} for j in JOBS},
            'next': [{'job': k, 'text': t} for k, t in _NEXT['v']], 'now': when(time.time()), 'size': size_line()}


PAGE = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>KPC control panel</title><style>
:root{--bg:#f6f4ef;--card:#fff;--ink:#1d2a22;--soft:#5b6b60;--line:#d9d4c7;--go:#1f6b3a;--busy:#a05a00;--off:#9aa39d}
*{box-sizing:border-box}body{margin:0;font:16px/1.4 system-ui,Segoe UI,sans-serif;background:var(--bg);color:var(--ink)}
header{padding:14px 18px;background:#1d2a22;color:#fff}header h1{margin:0;font-size:20px}header p{margin:4px 0 0;color:#cfd8d2;font-size:14px}
main{max-width:1100px;margin:0 auto;padding:14px}
.next{background:#fff7e0;border:1px solid #e7cf86;border-radius:8px;padding:10px 14px;margin-bottom:14px}
.next h2{margin:0 0 6px;font-size:16px}.next li{margin:3px 0}.next button{margin-left:6px}
section{margin-bottom:18px}section h2{font-size:17px;margin:0 0 8px;border-bottom:2px solid var(--line);padding-bottom:4px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:10px}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 12px;display:flex;flex-direction:column;gap:6px}
.card h3{margin:0;font-size:16px}.card p{margin:0;color:var(--soft);font-size:14px}.meta{font-size:13px;color:var(--soft)}
.row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
button{font:inherit;border:0;border-radius:6px;padding:7px 14px;cursor:pointer;background:var(--go);color:#fff}
button.small{background:#e8e4da;color:var(--ink);padding:5px 10px;font-size:14px}
button:disabled{background:var(--off);cursor:default}.run{color:var(--busy);font-weight:600}
.msg{position:fixed;bottom:14px;left:50%;transform:translateX(-50%);background:#1d2a22;color:#fff;padding:8px 14px;border-radius:6px;display:none}
footer{color:var(--soft);font-size:13px;padding:8px 0 30px}header p.size{color:#f1e3b0;font-size:13px}
</style></head><body><header><h1>KPC control panel</h1><p>Each button opens the tool in its own window. Two tools can run at once; tools that change the same files take turns.</p><p id="size" class="size"></p></header>
<main><div class="next" id="next"><h2>What next?</h2><ul id="nextlist"><li>Looking...</li></ul></div>
@@SECTIONS@@
<section><h2>Send results to Claude</h2><div class="grid"><div class="card"><h3>Make the zip for Claude</h3>
<p>Collects only the small summaries and counts (never the map store, the downloads or a PRIVATE file) into Tools\\TO-CLAUDE and opens that folder.</p>
<div class="row"><button onclick="act('send')">Make the zip</button></div></div>
<div class="card"><h3>Read the research rule sheet</h3><p>What the research helpers count, what they never do, and the questions waiting for your word.</p>
<div class="row"><button class="small" onclick="act('rules')">Open the rule sheet</button></div></div></div></section>
<footer>@@VERSION@@ - this page lives only on this PC. Close the small panel window to close it.</footer></main><div class="msg" id="msg"></div>
<script>
const T="@@TOKEN@@";
function say(t){const m=document.getElementById('msg');m.textContent=t;m.style.display='block';clearTimeout(say.h);say.h=setTimeout(()=>m.style.display='none',4000)}
async function post(path,body){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(Object.assign({t:T},body||{}))});return r.json()}
async function run(id){const r=await post('/run',{job:id});say(r.msg);refresh()}
async function act(a,id){const r=await post('/'+a,{job:id});say(r.msg)}
async function refresh(){try{const r=await fetch('/status?t='+T);const s=await r.json();
 for(const [id,j] of Object.entries(s.jobs)){const c=document.getElementById('j-'+id);if(!c)continue;
  c.querySelector('.last').textContent='Last finished: '+j.last;const b=c.querySelector('button.go');const st=c.querySelector('.state');
  if(!j.here){b.disabled=true;st.textContent='Not found on this PC';st.className='state'}
  else if(j.running){b.disabled=true;st.textContent='Running in its own window';st.className='state run'}
  else if(j.waits){b.disabled=true;st.textContent='Waits for: '+j.waits;st.className='state run'}
  else{b.disabled=false;st.textContent='';st.className='state'}}
 document.getElementById('size').textContent=s.size||'';
 const ul=document.getElementById('nextlist');ul.innerHTML='';
 if(!s.next.length){ul.innerHTML='<li>Nothing is behind. Pick any step below.</li>'}
 for(const n of s.next){const li=document.createElement('li');li.textContent=n.text;const b=document.createElement('button');b.className='small';b.textContent='Start';b.onclick=()=>run(n.job);li.appendChild(b);ul.appendChild(li)}
}catch(e){document.getElementById('nextlist').innerHTML='<li>The panel window was closed: start it again.</li>'}}
refresh();setInterval(refresh,3000);
</script></body></html>'''


def page(token):
    secs, cur = [], None
    for sec, name, what in CHANGES:   # 27 Nov: what changed lately, above the buttons
        if sec != cur:
            if cur: secs.append('</div></section>')
            secs.append(f'<section><h2>{html.escape(sec)}</h2><div class="grid">'); cur = sec
        secs.append(f'<div class="card"><h3>{html.escape(name)}</h3><p>{html.escape(what)}</p></div>')
    if cur: secs.append('</div></section>')
    cur = None
    for sec, jid, name, what, fk, bat, _ in JOBS:
        if sec != cur:
            if cur: secs.append('</div></section>')
            secs.append(f'<section><h2>{html.escape(sec)}</h2><div class="grid">'); cur = sec
        secs.append(f'<div class="card" id="j-{jid}"><h3>{html.escape(name)}</h3><p>{html.escape(what)}</p>'
                    f'<div class="meta"><span class="last"></span> <span class="state"></span></div>'
                    f'<div class="row"><button class="go" onclick="run(\'{jid}\')">Start</button>'
                    f'<button class="small" onclick="act(\'open\',\'{jid}\')">Open its folder</button></div></div>')
    secs.append('</div></section>')
    cur = None
    for sec, name, what in NOT_YET:
        if sec != cur:
            if cur: secs.append('</div></section>')
            secs.append(f'<section><h2>{html.escape(sec)}</h2><div class="grid">'); cur = sec
        secs.append(f'<div class="card"><h3>{html.escape(name)}</h3><p>{html.escape(what)}</p></div>')
    secs.append('</div></section>')
    return PAGE.replace('@@SECTIONS@@', '\n'.join(secs)).replace('@@TOKEN@@', token).replace('@@VERSION@@', VERSION)


def serve(port=0, fake=False, open_browser=True):
    token, runner = secrets.token_urlsafe(24), Runner(fake=fake)

    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a): pass

        def _send(self, code, body, ctype='application/json'):
            b = body.encode('utf-8') if isinstance(body, str) else body
            self.send_response(code); self.send_header('Content-Type', ctype + '; charset=utf-8'); self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)

        def _ok_token(self, t): return isinstance(t, str) and secrets.compare_digest(t, token)

        def do_GET(self):
            u = urllib.parse.urlsplit(self.path); q = dict(urllib.parse.parse_qsl(u.query))
            if not self._ok_token(q.get('t')): return self._send(403, 'This page needs the address the panel opened.', 'text/plain')
            if u.path == '/': return self._send(200, page(token), 'text/html')
            if u.path == '/status': return self._send(200, json.dumps(status(runner)))
            self._send(404, '{}')

        def do_POST(self):
            host = self.headers.get('Host', ''); origin = self.headers.get('Origin', '')
            try: body = json.loads(self.rfile.read(min(int(self.headers.get('Content-Length') or 0), 10_000)) or b'{}')
            except ValueError: body = {}
            if not self._ok_token(body.get('t')) or (origin and urllib.parse.urlsplit(origin).netloc != host):
                return self._send(403, json.dumps({'msg': 'refused'}))
            p = urllib.parse.urlsplit(self.path).path
            jid = str(body.get('job') or '')
            if p == '/run': return self._send(200, json.dumps({'msg': f'{JOB[jid][2] if jid in JOB else jid}: {runner.start(jid)}'}))
            if p == '/open' and jid in JOB:
                fd = folder(JOB[jid][4])
                if fake: return self._send(200, json.dumps({'msg': f'would open {fd}'}))
                if fd.is_dir(): os.startfile(str(fd))  # noqa: S606 (Windows only: opens the folder in Explorer)
                return self._send(200, json.dumps({'msg': 'opened' if fd.is_dir() else 'folder not found'}))
            if p == '/rules':
                f = ROOT / 'RESEARCH-RULES.txt'
                if fake: return self._send(200, json.dumps({'msg': f'would open {f}'}))
                if f.is_file(): os.startfile(str(f))  # noqa: S606
                return self._send(200, json.dumps({'msg': 'opened' if f.is_file() else 'RESEARCH-RULES.txt not found'}))
            if p == '/send':
                zp, files = make_send_zip()
                if not fake and hasattr(os, 'startfile'): os.startfile(str(zp.parent))
                return self._send(200, json.dumps({'msg': f'{len(files)} files in {zp.name}', 'files': files}))
            self._send(404, json.dumps({'msg': 'no such action'}))

    srv = http.server.ThreadingHTTPServer(('127.0.0.1', port), H)
    url = f'http://127.0.0.1:{srv.server_address[1]}/?t={token}'
    return srv, url, runner


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if '--check' in argv:
        print(VERSION, '  tools folder:', ROOT)
        for sec, jid, name, what, fk, bat, res in JOBS:
            print(f'  [{"here" if (folder(fk) / bat).is_file() else "MISSING"}] {sec} | {name} | {os.path.relpath(folder(fk), ROOT)}\\{bat} | last: {when(newest(fk, res))}')
        for k, t in next_steps(): print('  NEXT:', t)
        return 0
    srv, url, _ = serve(fake='--fake' in argv)
    if '--fake' not in argv: refresh_sizes()
    print(f'{VERSION}\nThe panel is open in your browser. If it did not open, paste this address into the browser:\n  {url}\n'
          'Keep this window open while you use the panel; close it to close the panel.')
    if '--no-browser' not in argv: webbrowser.open(url)
    try: srv.serve_forever()
    except KeyboardInterrupt: pass
    return 0


if __name__ == '__main__':
    sys.exit(main())
