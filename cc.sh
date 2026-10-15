UA='Mozilla/5.0 (KPC-Links contest calendar)'
curl -sL -A "$UA" -m 25 https://www.contestcalendar.com/terms.php | sed -e 's/<[^>]*>/ /g' | tr -s ' \n\t' ' ' | head -c 6000
echo; echo ===WK; grep -o 'weeklycontdetails.php?ref=[0-9a-z]*' wk.html | head -2
L=$(grep -o 'weeklycontdetails.php?ref=[0-9a-z]*' wk.html | head -1); curl -sL -A "$UA" -m 25 "https://www.contestcalendar.com/$L" | sed -e 's/<[^>]*>/ /g' | tr -s ' \n\t' ' ' | head -c 2500
