import urllib2

server = 'api.openstreetmap.org'

def getNode(id):
    url = 'http://' + server + '/api/0.6/node/' + str(id)
    return urllib2.urlopen(url).read()

def getWay(id):
    url = 'http://' + server + '/api/0.6/way/' + str(id)
    return urllib2.urlopen(url).read()

def getRelation(id):
    url = 'http://' + server + '/api/0.6/relation/' + str(id)
    return urllib2.urlopen(url).read()

def getChangeset(id):
    url = 'http://' + server + '/api/0.6/changeset/' + str(id)
    return urllib2.urlopen(url).read()

def getChange(id):
    url = 'http://' + server + '/api/0.6/changeset/' + str(id) + '/download'
    return urllib2.urlopen(url).read()
