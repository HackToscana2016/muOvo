import json
import urllib
import datetime
from math import floor
from polyline.codec import PolylineCodec
from geopy.geocoders import Nominatim
from urlparse import urlparse, parse_qs


def getTrip(fromAddr,toAddr,toDate,toTime):
    geolocator = Nominatim()
    location = geolocator.geocode(fromAddr)
    print "fromAddr",fromAddr,"location",location
    fromCoord=','.join(map(str,(location.latitude,location.longitude)))
    location = geolocator.geocode(toAddr)
    print "toAddr",toAddr,"location",location
    toCoord=','.join(map(str,(location.latitude,location.longitude)))

    #fromCoord='43.83412,11.19555'
    #toCoord='43.77187,11.25790'

    xmlurl = 'http://localhost:8080/otp/routers/default/plan?fromPlace=%s&toPlace=%s&date=%s&time=%s&arriveBy=true&mode=TRANSIT,WALK&maxWalkDistance=750&walkReluctance=20' % (fromCoord, toCoord, toDate[0], toTime[0])
    xmlpath=xmlurl
    html = urllib.urlopen(xmlpath)
    response = json.loads(html.read())

    plan=response['plan']

    reqParams=response['requestParameters']

    arriveBy=datetime.datetime.strptime(reqParams['date']+' '+reqParams['time'], '%m-%d-%Y %H:%M')

    fromName=plan['from']['name']
    toName=plan['to']['name']

    print "From", fromName
    print "To", toName

    itin=[]

    for it in plan['itineraries']:
        newItin={}
        endTime=datetime.datetime.fromtimestamp(int(it['endTime']/1000))
        newItin['endTime']=endTime.strftime('%Y-%m-%d %H:%M:%S')
        startTime=datetime.datetime.fromtimestamp(int(it['startTime']/1000))
        newItin['startTime']=startTime.strftime('%Y-%m-%d %H:%M:%S')
        newItin['transfers']=it['transfers']
        deltaEndTime=(arriveBy - endTime).total_seconds()/60
        newItin['deltaEndTimeMinutes']=deltaEndTime
        newItin['walkDistance']=it['walkDistance']
        points=[]
        for leg in it['legs']:
            points+=PolylineCodec().decode(leg['legGeometry']['points'])
        newItin['points']=points
        itin.append(newItin)
        print "Puoi partire alle %s arrivando con %s minuti di anticipo e facendo %d cambi, camminando per %s metri" % (startTime.strftime('%H:%M'),floor(newItin['deltaEndTimeMinutes']),newItin['transfers'],int(newItin['walkDistance']))

    return itin


from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer

class S(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        #query = urlparse(self.path).query
        #query_components = dict(qc.split("=") for qc in query.split("&"))

        query_components = parse_qs(urlparse(self.path).query)
        self._set_headers()

        if query_components.has_key('toDate'):
            resp=getTrip(query_components['fromAddr'],query_components['toAddr'],query_components['toDate'],query_components['toTime'])
            self.wfile.write("%s"%(json.dumps(resp),))

        #self.wfile.write("<html><body>%s</body></html>"%(resp,))

    def do_HEAD(self):
        self._set_headers()
        
def run(server_class=HTTPServer, handler_class=S, port=8090):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print 'Starting httpd...'
    httpd.serve_forever()

if __name__ == "__main__":
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()

