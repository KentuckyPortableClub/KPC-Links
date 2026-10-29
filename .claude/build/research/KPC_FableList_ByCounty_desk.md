# Open parks with no PAD-US record at the pin, grouped by county (chat 8, Oct 29 ~6:40 PM)
Source: chat 2's 2-county-01..06 answers (Census county at each pin). Full list with ref, name, pin: county_groups.json. 229 counties, 293 parks. Parcel requests go out where a state-wide parcel layer exists (NC, VT, AR, IN first: 8-parcel-nc/vt/ar/in); others need the county's own parcel service found first.

- state FIPS 01: 8 counties: Butler 2, Chilton 1, Morgan 1, Dallas 1, Bibb 1, Washington 1, Limestone 1, Sumter 1
- state FIPS 02: 1 counties: Fairbanks North Star Borough 1
- state FIPS 04: 1 counties: La Paz 1
- state FIPS 05: 14 counties: Clark 1, Arkansas 1, Newton 1, Randolph 1, Ouachita 1, Sebastian 1, Cleburne 1, Lonoke 1, Garland 1, Benton 1, Fulton 1, Nevada 1, Perry 1, Conway 1
- state FIPS 06: 2 counties: Tehama 1, San Mateo 1
- state FIPS 08: 1 counties: Prowers 1
- state FIPS 09: 1 counties: Lower Connecticut River Valley Planning Region 1
- state FIPS 10: 2 counties: Sussex 1, Kent 1
- state FIPS 12: 1 counties: Okeechobee 1
- state FIPS 13: 4 counties: Houston 1, Union 1, Fannin 1, Monroe 1
- state FIPS 16: 11 counties: Owyhee 1, Bonneville 1, Lemhi 1, Teton 1, Blaine 2, Valley 1, Adams 1, Boundary 1, Idaho 1, Elmore 1, Custer 1
- state FIPS 17: 2 counties: Pope 1, Jersey 1
- state FIPS 18: 5 counties: Putnam 1, Spencer 1, Posey 1, Jefferson 1, Wayne 1
- state FIPS 20: 12 counties: Miami 1, Doniphan 2, Linn 2, Douglas 1, Wyandotte 1, Washington 1, Morris 1, Republic 1, Lyon 1, Sheridan 1, Riley 1, Barton 1
- state FIPS 22: 3 counties: Rapides Parish 1, West Feliciana Parish 1, St. Bernard Parish 1
- state FIPS 24: 3 counties: Garrett 1, Anne Arundel 1, Calvert 1
- state FIPS 25: 5 counties: Essex 1, Norfolk 1, Suffolk 1, Franklin 1, Berkshire 1
- state FIPS 26: 9 counties: Crawford 1, Menominee 2, Emmet 1, Keweenaw 2, Presque Isle 1, Sanilac 1, Luce 1, Cheboygan 1, Chippewa 1
- state FIPS 27: 1 counties: Lake 1
- state FIPS 28: 29 counties: Noxubee 1, Adams 1, Jasper 2, Lee 2, Tippah 1, Monroe 2, Neshoba 1, Lauderdale 2, Simpson 1, Smith 1, Jones 2, Lawrence 1, Covington 2, Jefferson Davis 1, Walthall 1, Bolivar 1, Lafayette 2, Franklin 1, Tate 1, Yalobusha 1, Grenada 1, Lowndes 1, Tishomingo 1, Chickasaw 1, Clarke 1, Stone 1, Wayne 1, Newton 1, Harrison 1
- state FIPS 29: 2 counties: Shannon 1, Clay 2
- state FIPS 30: 1 counties: Fergus 1
- state FIPS 31: 5 counties: Antelope 1, Webster 1, Douglas 3, Jefferson 1, Fillmore 1
- state FIPS 32: 15 counties: White Pine 2, Carson City 1, Elko 5, Clark 3, Lander 1, Douglas 2, Nye 2, Humboldt 3, Churchill 3, Washoe 7, Storey 3, Eureka 1, Lincoln 5, Lyon 3, Pershing 1
- state FIPS 33: 3 counties: Coos 1, Rockingham 1, Merrimack 1
- state FIPS 35: 2 counties: Rio Arriba 1, De Baca 1
- state FIPS 36: 2 counties: Hamilton 1, Ulster 1
- state FIPS 37: 7 counties: Davidson 1, Clay 1, Orange 1, Lenoir 1, Rowan 1, Wake 1, Vance 1
- state FIPS 38: 22 counties: Barnes 3, Stutsman 1, Divide 1, McHenry 2, Ransom 1, Richland 1, Rolette 1, Morton 3, Griggs 5, Sargent 1, Burleigh 3, Grant 1, Billings 1, Williams 2, Mercer 1, Bowman 1, McLean 1, Pembina 3, Dickey 2, Dunn 1, Cass 1, Emmons 1
- state FIPS 40: 5 counties: Garfield 1, Alfalfa 2, Logan 2, Noble 1, Oklahoma 1
- state FIPS 41: 10 counties: Benton 1, Lane 2, Linn 1, Jackson 1, Lincoln 1, Tillamook 1, Douglas 1, Curry 1, Clatsop 1, Malheur 1
- state FIPS 45: 3 counties: Union 1, Lexington 1, Williamsburg 1
- state FIPS 47: 5 counties: Grundy 1, Franklin 1, Cannon 1, Carroll 1, Wilson 1
- state FIPS 48: 8 counties: Midland 1, Armstrong 1, Goliad 1, Brazoria 1, Travis 1, San Augustine 1, Fannin 1, Austin 1
- state FIPS 49: 4 counties: Iron 1, Cache 1, Weber 3, Garfield 1
- state FIPS 50: 3 counties: Washington 1, Essex 1, Windham 1
- state FIPS 51: 1 counties: Staunton city 1
- state FIPS 53: 4 counties: Kitsap 1, King 1, Stevens 2, Cowlitz 1
- state FIPS 54: 6 counties: Randolph 1, Pocahontas 1, Morgan 1, Grant 1, Kanawha 1, Jackson 1
- state FIPS 55: 1 counties: Grant 1
- state FIPS 56: 5 counties: Sheridan 1, Natrona 1, Fremont 1, Big Horn 1, Park 1

## P-3 parcel answers, first 4 states (Oct 29 ~6:50 PM). Data: KPC_Parcels_P3_chat8.json (ref, owner, parcel id, acres, why-not)
All four statewide layers worked (AR, IN, NC, VT); 29 pins asked.
- **Owner = the park's own agency (R-G7 4b: the parcel is the candidate outline, chat 11 yes/no first):** AR Janet Huckabee Nature Center US-11960, Joe Hogan US-12753, Hulsey Hatchery US-12754, Craig Hatchery US-12762, Hinkle Hatchery US-12764 (all Game & Fish Commission); AR Cook's Lake US-11355 (Game & Fish FOUNDATION, a partner, ask); AR Sugarloaf Mtn US-12093 (Arkansas State University, a university, check); NC CSS Neuse US-6837 (0.23 ac), NC Transportation Museum US-6847 (58.8 ac), State Capitol US-6852 (6.2 ac) (State of NC); VT Little River US-3129 and Nash Stream US-4936 (State of Vermont).
- **PIN DOUBT (the owner is a private person or company, so the pin may sit on the wrong land; R-G11 pin-outside split):** AR Highway 7 US-11214 (Maranatha Agriculture LLC), Muddy Creek WMA US-11394 (a family), Tates Bluff US-11874 (Bacon Family Trust), Little Missouri River Access US-7437 (Rock N Eagles Nest LLC); NC Nutbush WMA US-6963 (Wake Forest Land Associates, 2.75 ac); VT White Farm US-4980 (Narrow Brook Farm LLC).
- **No parcel at the pin (7):** AR Ponca Nature Center, Nimrood Lake River Road, Cherokee SRA; IN Lieber SRA, New Harmony; NC Vietnam Veterans Memorial, Brumley Forest. why-not = needs-parcel, try the county's own layer.
- **Blank owner field (6):** IN Spencer County SF, Lanier Mansion, Levi Coffin House; NC Chatuge Dam Trail: the layer gives a parcel id but no owner; need the county tax lookup.
- Indiana's layer gives parcels with no owner; owner needs the county.
