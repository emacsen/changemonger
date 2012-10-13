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

"""Functions related to working with elements and collections of elements"""
import inflect
import osmapi
import xml.etree.ElementTree as et
import parser
import features
p = inflect.engine()

import logging
from pprint import pformat

#logging.basicConfig(level=logging.DEBUG)

def retrieve(coll, type, id, version = None):
    for item in coll:
        if type == item['type'] and id == item['id']:
            if version:
                if version == item['version']:
                    return item

def common_name(ele):
    """Take an element and return its common name"""
    if ele['tags'].has_key('brand'):
        a = p.a(ele['tags']['brand'])
        return("%u %u" % (a, ele['tags']['brand']))
    elif ele['tags'].has_key('operator'):
        a = p.a(ele['tags']['operator'])
        return("%u %u" % (a, ele['tags']['operator']))
    elif ele['tags'].has_key('name'):
        return ele['tags']['name']
    else:
        return u'unnamed'

def display_name(ele, feature):
    """Takes an element and feature and returns it's displayable
    name

    """
    if not ele.get('tags') or not feature.named:
        return u"%s" % (p.a(feature.name))
    elif ( 'name' in ele['tags'].keys() or
         'brand' in ele['tags'].keys() or
         'operator' in ele['tags'].keys()):
        return common_name(ele)
    else:
        return u"an unnamed " + feature.name

def get_user(ele):
    """Takes an element and returns a displable username"""
    if ele.has_key('user'):
        return ele['user']
    else:
        return 'User %s' % (str(ele['uid']))

def sort_by_num_features(coll):
    """Takes a collection of (features, [elements] and returns them in
    order of quantity of elements

    """
    def sort_num_features(a, b):
        return len(b[1]) - len(a[1])
    return sorted(coll, cmp=sort_num_features)

def feature_grouper(coll):
    """Takes in a collection of elements and features and groups them
    by feature in the supplied order
    """
    # This function isn't very efficient and should likely be
    # rewritten
    grouped = []
    while coll:
        feature = coll[0][1][0]
        eles = [f[0] for f in coll if feature in f[1]]
        grouped.append( (eles, feature) )
        coll = [f for f in coll if feature not in f[1]]
    return grouped

def sort_grouped(coll):
    """Sort a grouped collection (from feature_grouper)"""
    def sort_num_elements(a, b):
        return len(b[0]) - len(a[0])
    return sorted(coll, cmp=sort_num_elements)

def grouped_to_english(coll):
    """Take a grouped collection (from feature_grouper) and return it
    as a human readable string
    """
    l = []
    for elements, feature in coll:
        if len(elements) > 1:
            l.append("%s %s" % (p.number_to_words(len(elements)),
                                feature.plural))
        else:            
            l.append(display_name(elements[0], feature))
    return p.join(l)

def sort_elements(coll):
    """Take a collection of elements and sort them in a way that's
    suitable for uniquing, and reverse referencing
    """
    relations = [e for e in coll if e['type'] == 'relation']
    ways = [e for e in coll if e['type'] == 'way']
    nodes = [e for e in coll if e['type'] == 'node']
    l = []
    def sortfn(a, b):
        if a['id'] < b['id']:
            r = -1
        elif a['id'] > b['id']:
            r = 1
        else:
            r = 0
        if r == 0:
            return int(a['version']) - int(b['version'])
        else:
            return r
    l.extend(sorted(nodes, cmp=sortfn))
    l.extend(sorted(ways, cmp=sortfn))
    l.extend(sorted(relations, cmp=sortfn))
    return l


def remove_unnecessary_items(coll):
    """Takes a collection of elements and removes those which are
    tagless but have either a way reference or a relation reference
    """
    l = []
    n = 0
    for ele in coll:
        if not ele['tags']:
            if ele.has_key('_ways') or ele.has_key('_relations'):
                n = n + 1
                continue
        else:
            l.append(ele)
    return l

def add_local_way_references(coll):
    """Takes a collection of elements and adds way callbacks to the
    nodes

    """
    logging.debug("Adding local way references")
    # This isn't the most efficient way to do this
    nodes = [ele for ele in coll if ele['type'] == 'node']
    ways = [ele for ele in coll if ele['type'] == 'way']
    for way in ways:
        nd = way['nd']
        for node in [node for node in nodes if node['id'] in nd]:
            logging.debug("Adding way reference for way %s to node %s" % (
                str(way['id']), str(node['id'])))
            if node.has_key('_ways'):
                node['_ways'].append(way['id'])
            else:
                node['_ways'] = [way['id']]

def add_way_reference(coll, way):
    "Adds way references for a specific way and a collection of element"
    nodes = [ele for ele in coll if ele['type'] == 'node']
    for nd in way['nd']:
        node = retrieve(coll, 'node', nd)
        if node:
            logging.debug("Adding way reference for way %s to node %s" % (
                str(way['id']), str(node['id'])))
            if node.has_key('_ways'):
                node['_ways'].append(way['id'])
            else:
                node['_ways'] = [way['id']]

def add_relation_references(coll, relation):
    "Add relation references for a specific relation and collection of elements"
    members = relation['members']
    for member in members:
        id = member['ref']
        type = member['type']
        obj = None
        for element in coll:
            if element['type'] == type and element['id'] == id:
                obj = element
                break
        if obj:
            logging.debug("Adding relation reference for relation %s to %s %s"
                          % (str(relation['id']), obj['type'], obj['id']))
            if obj.get('_relations'):
                obj['_relations'].append(relation)
            else:
                obj['_relations'] = [relation]


def add_local_relation_references(coll):
    """Takes a collection of elements and makes connections between
    the elenments for relations as necessary

    """
    logging.debug("Adding local relation references")
    # Same here about inefficiency
    relations = [ele for ele in coll if ele['type'] == 'relation']
    for rel in relations:
        members = [ (i['type'], i['ref']) for i in rel['members']]
        for member in members:
            type = member[0]
            id = member[1]
            # We'll use a list comprehension here even though it
            # should only return a single element
            for ele in [e for e in coll if (e['type'] == type
                                            and e['id'] == id)]:
                logging.debug("Adding relation reference for relation %s to %s %s" % ( str(rel['id']), e['type'], str(e['id'])))
                if ele.has_key('_relations'):
                    ele['_relations'].append(rel['id'])
                else:
                    ele['_relations'] = [rel['id']]

def add_remote_ways(coll):
    """Takes a collection of elements and adds way references for
    nodes if they don't have tags, or existing ways
    """
    logging.debug("Adding remote way references. %d items in the collection."
                  % (len(coll)))
    nodes = [ele for ele in coll if (ele['type'] == 'node'
                                     and not ele.get('tags')
                                     and not ele.get('_ways')
                                     and not ele.get('_relations'))]
    logging.debug("%d nodes to consider"
                  % (len(nodes)))
    logging.debug("Nodes: \n%s" % pformat(nodes))
    for node in nodes:
        if node['tags'] or node.get('_ways') or node.get('_relations'):
            # It only needs to have one way for us to care. We're not
            # looking at all the object relationships, just the first
            # right now
            continue
        logging.debug("Node %s has no remote ways or relations. Retrieving." %
                      str(node['id']))
        data = osmapi.getWaysforNode(node['id'])
        xml = et.XML(data.encode('utf-8'))
        ways = [parser.parseWay(way) for way in xml.findall('way')]
        for way in ways:
            logging.debug("Adding new way %s to collection" % way['id'])
            logging.debug(pformat(way))
            coll.append(way)
            target_nodes = [retrieve(coll, 'node', node_id) for node_id in way['nd']]
            target_nodes = [node for node in target_nodes if node]
            logging.debug("%d nodes potentially effected" % len(target_nodes))
            for node in target_nodes:
                logging.debug("Adding way reference for way %s to node %s" % (
                    str(way['id']), str(node['id'])))
                if node.has_key('_ways'):
                    node['_ways'].append(way['id'])
                else:
                    node['_ways'] = [way['id']]
            logging.debug("Done adding references for way %s" % way['id'])

def add_remote_relations(coll):
    """Takes an element of collections and fetches relations as necessary"""
    logging.debug("Adding remote relations")
    elements = [ele for ele in coll if (not ele['tags']
                                        and not ele.has_key('_relations'))]
    nodes = [ele for ele in coll if ele['type'] == 'node']
    ways = [ele for ele in coll if ele['type'] == 'way']
    relations = [ele for ele in coll if ele['type'] == 'relation']
    for ele in elements:
        # We keep changing the elmements in place, so we must keep
        # checking them
        if ele['tags'] or ele.get('_ways') or ele.get('_relations'):
            continue
        data = osmapi.getRelationsforElement(ele['type'], ele['id'])
        xml = et.XML(data.encode('utf-8'))
        rels = [parser.parseRelation(rel) for rel in xml.findall('relation')]
        for rel in rels:
            logging.debug("Adding relation %s to collection" % str(rel['id']))
            coll.append(rel)
            add_relation_references(coll, rel)

