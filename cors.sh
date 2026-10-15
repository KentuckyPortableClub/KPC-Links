O=https://kentuckyportableclub.github.io
for u in https://api.pota.app/spot https://api.pota.app/spot/ https://api2.sota.org.uk/api/spots https://spots.wwff.co/api/spots https://www.cqgma.org/api/spot.php https://www.gma.rocks/api/spot.php https://holycluster.iarc.org https://www.dxsummit.fi/api/v1/spots; do
 echo "=== $u"; curl -s -m 20 -o /dev/null -D - -X OPTIONS -H "Origin: $O" -H "Access-Control-Request-Method: POST" -H "Access-Control-Request-Headers: content-type" "$u" | grep -iE "^HTTP|access-control|allow:" 
done
echo "=== holy html"; curl -s -m 20 https://holycluster.iarc.org | head -c 1500
