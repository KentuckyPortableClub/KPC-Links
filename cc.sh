UA='Mozilla/5.0 (KPC-Links contest calendar)'
for u in https://www.contestcalendar.com/calendar.rss https://www.contestcalendar.com/calendar.ics https://www.contestcalendar.com/weeklycont.php https://www.contestcalendar.com/fivewkcal.html https://www.contestcalendar.com/contestcal.html; do echo "== $u $(curl -sL -A "$UA" -m 25 -o /tmp/x -w '%{http_code} %{size_download}' $u)"; head -c 1500 /tmp/x | tr -s '\n' ' '; echo; done
curl -sL -A "$UA" -m 25 https://www.contestcalendar.com/weeklycont.php > wk.html
L=$(grep -o 'contestdetails.php?ref=[0-9]*' wk.html | head -1); echo "detail $L"; curl -sL -A "$UA" -m 25 "https://www.contestcalendar.com/$L" > det.html
