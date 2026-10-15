UA='Mozilla/5.0 (KPC-Links contest calendar)'
curl -sL -A "$UA" -m 30 http://www.sk3bg.se/contest/ -o sk.html; echo "sk $(wc -c < sk.html)"
grep -o -i 'href="[^"]*\(ics\|ical\|rss\|xml\|csv\|json\|copyright\|terms\)[^"]*"' sk.html | sort -u | head
sed -e 's/<[^>]*>/ /g' sk.html | tr -s ' \n\t' ' ' | head -c 2500
