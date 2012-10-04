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

"""The core functionality of changemonger in a simple library"""
import osmapi

from features import FeatureDB
import xml.etree.ElementTree as et
import parser
import os
import elements
from sets import Set

db = FeatureDB()

def features(element):
    """Takes a node element and returns the features it matches"""
    return db.matchAllSolo(element)

def node(id, version = None):
    """Gets a node from the OSM API and returns it as a complete element"""
    data = osmapi.getNode(id, version)
    xml = et.XML(data.encode('utf-8'))
    root = xml.find('node')
    return parser.parseNode(root)

def way(id, version = None):
    """Gets a way from the OSM API and returns it as a complete element"""
    data = osmapi.getWay(id, version)
    xml = et.XML(data.encode('utf-8'))
    root = xml.find('way')
    return parser.parseWay(root)

def relation(id, version = None):
    """Gets a relation from the OSM API and returns it as a complete element"""
    data = osmapi.getRelation(id, version)
    xml = et.XML(data.encode('utf-8'))
    root = xml.find('relation')
    return parser.parseRelation(root)

def changeset(id):
    """Gets a changeset from the OSM API and returns it in a complete
    form ready to use

    """
    # First get the changeset metadata
    data = osmapi.getChangeset(id)
    xml = et.XML(data.encode('utf-8'))
    root = xml.find('changeset')
    changeset = parser.parseChangeset(root)
    # Now get the OSM change for it
    data = osmapi.getChange(id)
    xml = et.XML(data.encode('utf-8'))
    change = parser.parseChange(xml)
    changeset['actions'] = change
    # Now collect all the objects in this changeset for processing
    eles = []
    for i in changeset['actions']:
        eles.extend(i[1])
    # Add changeset tags to objects
    for ele in eles:
        ele['_changeset_tags'] = change['tags']
    # Make internal references based on info we already have
    elements.add_local_way_references(eles)
    elements.add_local_relation_references(eles)
    # Now collect the rest from remote data
    elements.add_remote_ways(eles)
    elements.add_remote_relations(eles)
    # Remove tagless items we have parent objects for
    elements.remove_unnecessary_items(eles)
    # Sort elements
    elements.sort_elements(eles)
    return changeset

def changeset_sentence(cset):
    """Take a changeset object and return a sentence"""
    action_hash = {
        'create': 'added',
        'modify': 'modified',
        'delete': 'deleted'}
    # Future versions will be able to handle multiple users
    user = elements.get_user(cset)
    # A future version will do more complex action grouping
    eles = []
    for i in cset['actions']:
        eles.extend(i[1])
    actions = Set()
    for ele in eles:
        actions.add(ele['_action'])
    if len(actions) == 1:
        action = action_hash[actions.pop()]
    else:
        action = 'edited'

    for i in cset['actions']:
        eles.extend(i[1])    
    ele_features = zip(eles, db.matchEach(eles))
    sorted_ef = elements.sort_by_num_features(ele_features)
    grouped_features = elements.feature_grouper(sorted_ef)
    sorted_features = elements.sort_grouped(grouped_features)
    english_list =  elements.grouped_to_english(sorted_features)
    return "%s %s %s" % (user, action, english_list)

