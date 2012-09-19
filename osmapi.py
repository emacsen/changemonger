##  Changemonger: An OpenStreetMap change analyzer
##  Copyright (C) 2012 Serge Wroclawski
##
##  This program is free software: you can redistribute it and/or modify
##  it under the terms of the GNU Affero General Public License as
##  published by the Free Software Foundation, either version 3 of the
##  License, or (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU Affero General Public License for more details.
##
##  You should have received a copy of the GNU Affero General Public License
##  along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Provides a simple abstraction against the OSM API"""

import requests
import requests_cache
import logging

logging.basicConfig(level=logging.DEBUG)

rs = requests.session(headers={'user-agent': 'changemonger/0.0.1'})
requests_cache.configure('osm_cache')

server = 'api.openstreetmap.org'

def getNode(id, version = None):
    id = str(id)
    if version:
        url = "http://%s/api/0.6/node/%s/%s" % (server, id, str(version))
    else:
        url = "http://%s/api/0.6/node/%s" % (server, id)
    logging.debug("Retrieving %s for node %s version %s" % (
        url, id, version))
    r = rs.get(url)
    r.raise_for_status()
    return r.text

def getWay(id, version = None):
    id = str(id)
    if version:
        url = "http://%s/api/0.6/way/%s/%s" % (server, id, str(version))
    else:
        url = "http://%s/api/0.6/way/%s" % (server, id)
    logging.debug("Retrieving %s for way %s version %s" % (
        url, id, version))
    r = rs.get(url)
    r.raise_for_status()
    return r.text

def getRelation(id, version = None):
    id = str(id)
    if version:
        url = "http://%s/api/0.6/relation/%s/%s" % (server, id, str(version))
    else:
        url = "http://%s/api/0.6/relation/%s" % (server, id)
    logging.debug("Retrieving %s for relation %s version %s" % (
        url, id, version))
    r = rs.get(url)
    r.raise_for_status()
    return r.text

def getChangeset(id):
    id = str(id)
    url = "http://%s/api/0.6/changeset/%s" % (server, id)
    logging.debug("Retrieving %s for changeset %s metadata" % (
        url, id))
    r = rs.get(url)
    r.raise_for_status()
    return r.text

def getChange(id):
    id = str(id)
    url = "http://%s/api/0.6/changeset/%s/download" % (server, id)
    logging.debug("Retrieving %s for changeset %s data" % (
        url, id))
    r = rs.get(url)
    r.raise_for_status()
    return r.text

def getWaysforNode(id):
    id = str(id)
    url = "http://%s/api/0.6/node/%s/ways" % (server, id)
    logging.debug("Retrieving %s for node %s ways" % (url, id))
    r = rs.get(url)
    r.raise_for_status()
    return r.text

def getRelationsforElement(type, id):
    type = str(type)
    id = str(id)
    url = "http://%s/api/0.6/%s/%s/relations" % (server, type, id)
    logging.debug("Retrieving %s for %s %s relations" % (url, type, id))
    r = rs.get(url)
    r.raise_for_status()
    return r.text

