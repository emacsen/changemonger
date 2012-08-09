import xml.etree.ElementTree as et
from flask import abort
import osmapi
import parser
import urllib2
import yaml
import inflect

p = inflect.engine()

from elements import display_name, get_user, add_local_way_references, \
    add_local_relation_references, add_remote_ways, add_remote_relations, \
    sort_elements, sort_by_num_features, feature_grouper, sort_grouped, \
    dict2feature

def populate_features_in_yaml(database, yamlfile):
    with open(yamlfile) as fd:
        data = fd.read()
        yamldata = yaml.load(data)
        for item in yamldata:
            feature = dict2feature(item)
            database.addFeature(feature)

def get_element_or_404(o_type, oid):
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

def sentence_from_changeset(cset):
    """Take a changeset object and return a sentence"""
    user = get_user(cset)
    if len(cset['actions']) == 1:
        name,eles = cset['actions'][0]
        if name == 'create':
            action = 'created'
        elif name == 'modify':
            action = 'modified'
        else:
            action = 'deleted'
    else:
        action = 'edited'
        eles = []
        for i in cset['actions']:
            eles.extend(i[1])
    add_local_way_references(eles)
    add_local_relation_references(eles)
    add_remote_ways(eles)
    add_remote_relations(eles)
    eles = remove_unnecessary_items(eles)
    eles = sort_elements(eles)
    ele_features = zip(eles, db.matchEach(eles))
    sorted_ef = sort_by_num_features(ele_features)
    grouped_features = feature_grouper(sorted_ef)
    sorted_features = sort_grouped(grouped_features)
    english_list =  grouped_to_english(sorted_features)
    return "%s %s %s" % (user, action, english_list)
