import xml.etree.ElementTree as et
from flask import abort

import osmapi
import parser
import requests

import yaml
import inflect
import changemonger

p = inflect.engine()

import elements

def get_node_or_404(id, version = None):
    try:
        r = changemonger.node(id, version)
        return r
    except requests.exceptions.HTTPError, msg:
        abort(401, "Error retrieving node %s: %s" % (str(id), msg))
            
def get_way_or_404(id, version = None):
    try:
        return changemonger.way(id, version)
    except requests.exceptions.HTTPError, msg:
        abort(401, "Error retrieving way %s: %s" % (str(id), msg))

def get_relation_or_404(id, version = None):
    try:
        return changemonger.relation(id, version)
    except requests.exceptions.HTTPError, msg:
        abort(401, "Error retrieving relation %s: %s" % (str(id), msg))

def get_changeset_or_404(id):
    # A changeset actually needs information from both the changeset
    # and from the osmchange
    return changemonger.changeset(id)

def get_feature_or_404(id):
    try:
        return changemonger.db.get(id)
    except KeyError:
        abort(404)

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
            l.append(elements.display_name(elements[0], feature))
    return p.join(l)

def sentence_from_changeset(cset):
    """Take a changeset object and return a sentence"""
    user = elements.get_user(cset)
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
    elements.add_local_way_references(eles)
    elements.add_local_relation_references(eles)
    elements.add_remote_ways(eles)
    elements.add_remote_relations(eles)
    eles = elements.remove_unnecessary_items(eles)
    eles = elements.sort_elements(eles)
    ele_features = zip(eles, db.matchEach(eles))
    sorted_ef = elements.sort_by_num_features(ele_features)
    grouped_features = elements.feature_grouper(sorted_ef)
    sorted_features = elements.sort_grouped(grouped_features)
    english_list =  grouped_to_english(sorted_features)
    return "%s %s %s" % (user, action, english_list)
