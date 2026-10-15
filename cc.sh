UA='Mozilla/5.0 (KPC-Links contest calendar)'
for p in index.php weeklycont.php fivewkcal.php contestcal.php stateparties.php; do echo "== $p"; curl -sL -A "$UA" -m 25 https://www.contestcalendar.com/$p | grep -o -i 'href="[^"]*rss[^"]*"' | sort -u; done
for f in calendar.rss calendarfivewk.rss fivewkcal.rss contestcal.rss stateparties.rss; do echo "== $f $(curl -sL -A "$UA" -m 25 -o /tmp/r -w '%{http_code}' https://www.contestcalendar.com/$f) items=$(grep -c '<item>' /tmp/r)"; done
curl -sL -A "$UA" -m 25 https://www.contestcalendar.com/calendar.rss > cal.rss
