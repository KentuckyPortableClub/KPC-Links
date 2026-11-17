# Matching plan (Fable, 17 Nov 2026) - for the chat that builds the key batch (Opus)

Owner, 17 Nov 12:17 PM: "Anything more we can do to get the bots better at matching? This is the part we need to nail."
Design only; nothing here is built. Build it WITH the ledger-75 batch (reviewers A + B) so the keys are rebuilt once.
Counts are from the published US key + KPC-Data data/parkinfo (17 Nov). Lists: KPC-Data branch tools-out, research/matching-nov17/.

## The idea in one line
Today each park is matched alone ("which records look like me?"), so two parks can both take one record and a park can take
its neighbour's. Add the other half: "which PARK does this record fit best?" A park keeps a record only when no other POTA
park fits that record better. One rule (THE CONTEST) replaces four patches: exact-name-wins, D9, the type-letters step and the
sibling fix.

## 1. THE CONTEST (build first; US, then Canada + world)
After the name joins of a state, for every record joined by NAME (not a person's join, not B12 parts):
- Fit of a park to a record, best first: (a) full name equal [D9 today]; (b) place words equal AND the record's type words
  name the park's kind; (c) the record's type words name the park's kind (only one such park); (d) place words equal;
  (e) starts-with; (f) shared words.
- Type words include the agencies' short forms: SP, SRP, SF, NF, WA, WMA, SWA, FWA, SGL, SB, SHP, SHS, SRA, NRA, SNA, DNP,
  SNP, NWR, NCA, WSA, HMA. kinds() in kpc_us_key.py does NOT know them today ('Scioto Trail SF' has no kind), which is why
  the State Park and the State Forest both take it. No type word on the record = use the layer's kind (state-gis 'kind').
- Compare against EVERY POTA park of the state, not only the ones that took the record (a pin park can still be the better
  fit: then the taker gives it back and the record is offered to the better park).
- A record naming two kinds with and / & / slash stays on both ('same land, two park numbers').
- A tie, or a bare name nobody fits better = off every park, to a person, with both names. Never left on everyone.
- Kind words that only DIFFER are not a block by themselves: 825 name joins on 416 parks have record type words that are not
  the park's (type-word-clash-joins.csv), and many are fine (Montana 'Fishing Access Site' = 'State Fish and Wildlife Area',
  'Shabbona Lake State Park' = the State Recreation Area). A clash matters only when another POTA park fits better.
- Measured on shared records (hole2-shared-records.csv): 909 open records = 222 cases; 100 settled, 7 both, 115 to a person.
- Tests: Scioto Trail / Blue Rock / Tar Hollow (OH) SF vs SP; Salt Fork WA; Susquehanna Sp (MD) leaves the refuge; Will
  Rogers SHP / SB (CA); Alexandria SRA (NE) goes to Alexandria LAKES SRA, not Alexandria WMA; White River Marsh (WI, 333
  parcels); San Diego NWR vs San Diego Bay NWR; Great Sand Dunes NP vs Preserve. Must NOT change: the 7 'both' records, B12
  part parks, hand joins. Same switch as D9 (KPC_ONE_RECORD_ONE_PARK), wired per reviewer B #7.

## 2. THE AGENCY LEG, from POTA's own website field (the owner's idea, the part that pays)
- data/parkinfo/<area>.json already holds POTA's website per park (field 1): 12,756 of 12,857 US parks. No request needed.
- Do NOT read the pages (every agency's page is different, addresses are offices and gates, the pin already gives the place).
  Read only the ADDRESS OF THE SITE: fws.gov = the refuge system, agfc.com = Arkansas Game and Fish, arkansasstateparks.com,
  cpw.state.co.us, nps.gov, blm.gov...
- LEARN the table, do not hand-write it: from the 12,944 person-reviewed joins (4,051 parks), count for each website which
  layers (and, for PAD-US, which Mang_Name) its parks' records come from. "Parks from this website live in these layers."
- Use 1, contest tie-break: of the 115 person cases, 52 are between parks with DIFFERENT websites (Big Lake: fws.gov vs
  agfc.com; Browns Park: fws.gov vs cpw.state.co.us; Cut-off Creek: arkansasheritage.com vs agfc.com). The record's own
  manager (PAD-US Mang_Name / Own_Name, or its layer's agency) picks the park whose website family it belongs to.
- Use 2, a third leg for D2 'sure' = name + place + AGENCY agrees. Report first.
- Use 3, report only: name joins whose layer is not in the park's website family. A hand-made federal / state split gave
  234 parks (agency-leg-mismatch.csv) but is noisy (state copies of federal units = D7; club and third-party websites), so
  it is evidence and a list for a person, never a block.
- Pins: 506 of the 1,380 US pins are blm.gov parks, 74 nps.gov. The website says which agency's layer to look for (feeds
  the parked GIS research list).

## 3. HARD NUMBERS BEFORE NAMES
- NPS: 468 US parks have nps.gov/<4-letter unit code> in their POTA website. The Park Service boundary layer carries the
  same code (UNIT_CODE; check the field name on the layer the key reads). Join by CODE first: no name test at all. 63 of
  the 468 are pins today (12 historic sites, 10 wild and scenic rivers, 6 memorials, 6 monuments...). 25 codes are used by
  2+ POTA parks (park + preserve, trails): there the names decide INSIDE the unit (owner ruling: each unit its own).
- Survey per state (not done): websites that carry the agency's own id in the address (Minnesota WMA detail_report.html?id=,
  Michigan details.aspx?id=). Where the state layer has the same id field = join by id.
- Canada: CPCAD ZONE_ID with name + hectares (reviewer B #3).
- A saved hand join is saved as the LAND (name + acres), D1; a NO likewise (owner ruling today).

## 4. THE GRADE (how we know matching got better: build this before switching anything on)
- People's answers are the answer sheet: 12,944 reviewed joins + 2,484 NOs (US), more in CA / world.
- kpc_key_scorecard.py, OFFLINE (KPC_KEY_OFFLINE=1, saved copies), one state at a time: build once with the people's
  answers hidden (overrides empty, reviewed rows not carried), compare with their answers:
  FOUND = share of person-YES records the matcher joins by itself; WRONG = person-NO records it joins; EXTRA = records it
  joins on reviewed parks that the person did not (a person skims the top ones once).
- One line per state, before and after each rule or switch. A change that lowers FOUND or raises WRONG in any state does not
  merge without the owner's word. Set the pass mark after the first full measurement.
- Compare two OFFLINE runs, never offline against the published file (reviewer A #8).

## 5. LEFTOVERS, by elimination (a person's list, never automatic)
- After the contest: a pin park and an unmatched record ('places with no POTA park', nonum) in the same website family's
  layer, with the park's pin inside or beside the record = proposed pair, best first. Catches other names for the same
  place (Ozone Falls SNA, the Forest Service 'Manistee, Michigan' rivers).
- Every person YES on a different name is kept as an 'also called' pair and offered again in that layer family.

## 6. World names (rule sheet in the Fable doc, claude.ai/artifact/R3fgqUTL2xaLAxL4RihKXQ)
- Near-identical name (1-2 letters or endings) + pin inside + kind does not disagree = approximate + a person's list:
  207 parks (hole1-world-near-names.csv). Other alphabets: no gain today, skip until a source needs it.

## Order
(0) wire the switches + hash them (reviewer B #7) -> (4) the scorecard -> (1) the contest -> NO-is-the-land + D1 ->
(3) NPS codes -> (2) agency table + tie-break -> D3 by label + D7 -> bug fixes -> (5) leftovers list -> (6) world names.
One offline proof per step on a state that has candidates (OH / WI / AR / CA / MD), then ONE rebuild.
