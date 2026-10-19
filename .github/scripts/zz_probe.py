import json, urllib.parse, urllib.request
Q = ['Arkansas Game and Fish Commission Wildlife Management Areas', 'Michigan DNR state game areas boundaries', 'NCWRC game lands boundaries',
     'Colorado Parks and Wildlife State Wildlife Areas', 'WDFW wildlife areas boundaries', 'WDFW water access sites', 'IDFG access areas',
     'Missouri Department of Conservation conservation areas', 'Nebraska Game and Parks Commission public access areas', 'New Hampshire conservation public lands GRANIT',
     'MDWFP wildlife management areas', 'LDWF wildlife management areas', 'MassWildlife wildlife management areas', 'Utah DWR wildlife management areas',
     'Connecticut DEEP state parks forests boundaries', 'Indiana DNR properties', 'Alaska state park units boundaries', 'Wisconsin DNR managed lands',
     'ODNR wildlife areas', 'Kansas KDWP public lands', 'Tennessee state natural areas TDEC', 'Oregon state parks boundaries', 'Vermont state lands ANR',
     'Florida water management district lands', 'Illinois DNR sites boundaries', 'Mississippi state parks boundaries', 'Wyoming Game and Fish wildlife habitat management areas']
out = {}
for q in Q:
    try:
        u = 'https://www.arcgis.com/sharing/rest/search?' + urllib.parse.urlencode({'q': q + ' type:"Feature Service"', 'num': 8, 'f': 'json', 'sortField': 'numviews', 'sortOrder': 'desc'})
        j = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'KPC'}), timeout=60).read())
        out[q] = [[r.get('title'), r.get('owner'), r.get('url'), r.get('access'), (r.get('snippet') or '')[:120]] for r in j.get('results', [])]
    except Exception as e:  # noqa: BLE001
        out[q] = str(e)
json.dump(out, open('probe.json', 'w'), indent=1)
print('done', len(out))
