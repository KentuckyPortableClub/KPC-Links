UA='Mozilla/5.0 (KPC-Links contest calendar)'
curl -sL -A "$UA" -m 30 https://www.arrl.org/contest-calendar -o arrlcc.html; echo "arrl $(wc -c < arrlcc.html)"
grep -o 'href="[^"]*contest[^"]*"' arrlcc.html | sort -u | head -40
curl -sL -A "$UA" -m 30 https://www.arrl.org/robots.txt | head -40
curl -sL -A "$UA" -m 30 https://www.contestcalendar.com/robots.txt | head -20
