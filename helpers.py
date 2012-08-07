import xml.etree.ElementTree as et
from flask import abort
import osmapi
import parser
import urllib2
import yaml
from features import Feature
import inflect
from pprint import pprint
p = inflect.engine()


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
    if not ele['tags'] or not feature.use_name:
        return u"%s %" % (p.a(feature.name), feature.name)
    elif ( 'name' in ele['tags'].keys() or
         'brand' in ele['tags'].keys() or
         'operator' in ele['tags'].keys()):
        return common_name(ele)
    else:
        return u"an unnamed " + feature.name


def dict2feature(d):
    """Takes a dictionary in (from yaml) and returns a Feature"""
    f = Feature(d['feature'])
    f.tags = d.get('tags', [])
    f.categories = d.get('categories', [])
    f.types = d.get('types', None)
    # These are functions by default, so don't use the get method
    if d.has_key('plural'):
        f.plural = d['plural']
    if d.has_key('precision'):
        f.precision = d['precision']
    return f
    if d.has_key['use_name']:
        f.use_name = d['use_name']

def get_user(ele):
    """Takes an element and returns a displable username"""
    if ele.has_key('user'):
        return ele['user']
    else:
        return 'User %s' % (str(changeset['uid']))

def populate_features_in_yaml(database, yamlfile):
    with open(yamlfile) as fd:
        data = fd.read()
        yamldata = yaml.load(data)
        for item in yamldata:
            feature = dict2feature(item)
            database.addFeature(feature)

def get_feature_or_404(element_id):
    try:
        o_type, oid = element_id.split(':')
    except ValueError:
        abort(404, 'Element identifier not valid')
    api = { 'node': osmapi.getNode,
            'way': osmapi.getWay,
            'relation': osmapi.getRelation}
    parsers = { 'node': parser.parseNode,
                'way': parser.parseWay,
                'relation': parser.parseRelation}
    try:
        data = api[o_type](oid)
        xml = et.XML(data)
        root = xml.find(o_type)
        return parsers[o_type](root)
    except urllib2.HTTPError, e:
        abort(404, e)
    except urllib2.URLError, e:
        abort(501, e)
    except KeyError, e:
        abort(404, "Element type not valid")

def get_changeset_or_404(changesetid):
    # A changeset actually needs information from both the changeset
    # and from the osmchange
    try:
        changeset_raw = osmapi.getChangeset(changesetid)
        xml = et.XML(changeset_raw)
        changeset = parser.parseChangeset(xml.find('changeset'))
        change_raw = osmapi.getChange(changesetid)
        xml = et.XML(change_raw)
        change = parser.parseChange(xml)
        changeset['actions'] = change
        return changeset
    except urllib2.HTTPError, e:
        abort(404, e)
    except urllib2.URLError, e:
        abort(501, e)

def get_user(changeset):
    if changeset.has_key('user'):
        return changeset['user']
    else:
        return 'User %s' % (str(changeset['uid']))

def sort_by_num_features(coll):
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

def unique_elements(coll):
    """Takes a sorted collection of elements. Returns those elements
    uniqued by version. Also removes dupes.
    """
    ### UNUSED BECAUSE BROKEN!
    if not coll:
        return
    i = 0
    while i <= (len(coll) - 1):
        ele = coll[i]
        next_ele = coll[i + 1]
        if ( ele['type'] == next_ele['type'] and
             ele['id'] == next_ele['id'] and
             ele['version'] <= next_ele['version']):
            coll.pop(i)
        else:
            i += 1
        
def unique_elements2(coll):
    """Takes a sorted collection of elements. Returns those elements
    uniqued by version. Also removes dupes.
    """
    prev = None
    l = []
    for idx, ele in enumerate(coll):
        try:
            if not prev:
                continue
            if ( ele['type'] == prev['type'] and
                 ele['id'] == prev['id'] and
                 prev['version'] <= ele['version']):
                pass
            else:
                l.append(ele)
                prev = ele
        except IndexError:
            # This is fine, we'll exit out the next go
            pass
    return l

def remove_unnecessary_items(coll):
    """Takes a collection of elements and removes those which are
    tagless but have either a way reference or a relation reference
    """
    l = []
    for ele in coll:
        if not ele['tags']:
            if ele.has_key('_ways') or ele.has_key('_relations'):
                continue
        else:
            l.append(ele)
    return l

    """Takes a collection of elements and removes tagless objects
    belonging to another object
    """
    # This is not the most network efficient mechanism to get this,
    # but it'll do for now
    coll_idx = {}
    for ele in coll:
        if ele['tags']:
            continue
        # This element is tagless
        if ele['type'] == 'node':
            raw_ways = osmapi.getWaysforNode(ele['id'])
            root = xml_find('osm')
            ways = [way for way in parseWay(root.findall('way'))]
        relations = [rel for rel in
                     parseRelation(root.findall('relation'))]
        if not ways or not relations:
                    # This is significant
                    l.append(ele)
        for way in ways:
            # We need to be sure that this way isn't already accounted
            # for (because we're adding them
            for relation in relations:
                l.append(relation)
                

def add_local_way_references(coll):
    """Takes a collection of elements and adds way callbacks to the nodes"""
    # This isn't the most efficient way to do this
    nodes = [ele for ele in coll if ele['type'] == 'node']
    ways = [ele for ele in coll if ele['type'] == 'way']
    for way in ways:
        nd = way['nd']
        for node in [node for node in nodes if node['id'] in nd]:
            if node.has_key('_ways'):
                node['_ways'].append(way['id'])
            else:
                node['_ways'] = [way['id']]

def add_local_relation_references(coll):
    # Same here about inefficiency
    relations = [ele for ele in coll if ele['type'] == 'relation']
    for rel in relations:
        members = [ (i['type'], i['ref']) for i in rel['members']]
        for member in members:
            type = ele['type']
            id = ele['id']
            # We'll use a list comprehension here even though it
            # should only return a single element
            for ele in [e for e in coll if (e['type'] == type
                                            and e['id'] == id)]:
                if ele.has_key('_relations'):
                    ele['_relations'].append(rel['id'])
                else:
                    ele['_relations'] = [rel['id']]

def add_remote_ways(coll):
    """Takes a collection of elements and adds way references for
    nodes if they don't have tags, or existing ways
    """
    newways = []
    nodes = [ele for ele in coll if (ele['type'] == 'node'
                                     and not ele['tags']
                                     and not ele.has_key('_ways'))]
    for node in nodes:
        if node['tags'] or node.has_key('_ways'):
            # It only needs to have one way for us to care. We're not
            # looking at all the object relationships, just the first
            # right now
            continue
        data = osmapi.getWaysforNode(node['id'])
        xml = et.XML(data)
        ways = [parser.parseWay(way) for way in xml.findall('way')]
        for way in ways:
            coll.append(way)
            # This is a lot of looping we could avoid if we had an index...
            [addWayCallbackToNode(n, way['id']) for n in nodes if n['id'] in way['nd']]

def add_remote_relations(coll):
    elements = [ele for ele in coll if (not ele['tags']
                                        and not ele.has_key('_relations'))]
    nodes = [ele for ele in coll if ele['type'] == 'node']
    ways = [ele for ele in coll if ele['type'] == 'way']
    relations = [ele for ele in coll if ele['type'] == 'relation']
    for ele in elements:
        if ele['tags'] or ele.has_key('_ways') or ele.has_key('_relations'):
            continue
        data = osmapi.getRelationsforElement(ele['type'], ele['id'])
        xml = et.XML(data)
        root = xml.find('osm')
        rels = [parser.parseRelation(rel) for rel in xml.findall('relation')]
        for rel in rels:
            coll.append(rel)
            for member in rel['members']:
                mid = member['ref']
                mtype = member['type']
                mobj = None
                if mtype == 'node':
                    mobj = [m for m in nodes if m['id'] == mid][0]
                elif mtype == 'way':
                    mobj =  [m for m in nodes if m['id'] == mid][0]
                else:
                    mobj = [m for m in relations if m['id'] == mid][0]
                addRelationCallbackToElement(mobj)

def allRelationCallbackToElement(ele, relid):
    if ele.has_key('_relation'):
        ele['_relations'].append(relid)
    else:
        ele['_ways'] = [relid]

def addWayCallbackToNode(node, wayid):
    if node.has_key('_ways'):
        node['_ways'].append(wayid)
    else:
        node['_ways'] = [wayid]
