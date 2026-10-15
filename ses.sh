UA="Mozilla/5.0 KPC-Links events"
curl -sL -A "$UA" -m 30 "https://www.arrl.org/special-event-stations" -o ses1.html; echo "p1 $(wc -c <ses1.html)"
curl -sL -A "$UA" -m 30 "https://www.arrl.org/special-event-stations?page=2" -o ses2.html; echo "p2 $(wc -c <ses2.html)"
L=$(grep -o 'href="/special-event/[^"]*"' ses1.html | head -1 | cut -d'"' -f2); echo "detail $L"
curl -sL -A "$UA" -m 30 "https://www.arrl.org$L" -o ses-detail.html; echo "d $(wc -c <ses-detail.html)"
for u in https://www.13colonies.net/ https://www.nj2bb.org/museum/ https://illw.net/ https://www.wwbota.net/ ; do echo "== $u $(curl -sL -A "$UA" -m 20 -o /dev/null -w '%{http_code}' $u)"; done
curl -s -m 20 "https://spothole.app/api/v1/spots?limit=3" | head -c 2500
