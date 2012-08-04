import xml.etree.ElementTree as et
from flask import abort
import osmapi
import parser
import urllib2
import yaml
from features import Feature
import inflect

p = inflect.engine()

def common_name(ele):
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
    if not ele['tags']:
        return u"%s" % (p.a(feature.name))
    elif ( 'name' in ele['tags'].keys() or
         'brand' in ele['tags'].keys() or
         'operator' in ele['tags'].keys()):
        return common_name(ele)
    else:
        return u"an unnamed " + feature.name

def dict2feature(d):
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
