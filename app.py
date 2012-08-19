##  Changemonger: An OpenStreetMap change analyzer
##  Copyright (C) 2012 Serge Wroclawki
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

from flask import Flask, jsonify, request, render_template
app = Flask(__name__)
app.debug = True
from helpers import get_element_or_404, get_changeset_or_404, \
    sentence_from_changeset
from elements import common_name, display_name
from features import FeatureDB
from werkzeug import ImmutableDict
from features import pluralize
import os

class FlaskWithHamlish(Flask):
    jinja_options = ImmutableDict(
        extensions=['jinja2.ext.autoescape', 'jinja2.ext.with_',
                    'hamlish_jinja.HamlishExtension'] )
 
app = FlaskWithHamlish(__name__)
app.jinja_env.hamlish_mode = 'indented' # if you want to set hamlish settings

db = FeatureDB()
for subdir, dirs, files in os.walk('features/'):
    for fname in files:
        name, ext = os.path.splitext(fname)
        if ext == '.yaml':
            db.load_yaml_features('features/' + fname)
### db.load_yaml_features('features/highway.yaml')

############
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
    remove_unnecessary_items

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
                                pluralize(feature)))
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





############




@app.route('/')
def index():
    return render_template('index.haml')

@app.route('/node')
def display_node():
    if request.args.has_key('oid'):
        oid = request.args['oid']
        ele = get_element_or_404('node', oid)
        features = db.matchAllSolo(ele)
        return render_template('node_details.haml',
                               name = display_name(ele, features[0]),
                               node = ele,
                               features = features)
    else:
        return render_template('node.haml', title="Node Bad bad")

@app.route('/changeset')
def display_changeset():
    if request.args.has_key('oid'):
        oid = request.args['oid']
        cset = get_changeset_or_404(oid)
        sentence = sentence_from_changeset(cset)
        return render_template('changeset_details.haml',
                               changeset = cset,
                               sentence = sentence)
    else:
        return render_template('node.haml', title="Node")

@app.route('/features')
def show_features():
    return render_template('features.haml', features = db._features)

@app.route('/dbstats')
def show_stats():
    return jsonify(features=len(db._features),
                   categories=len(db._categories))

@app.route('/api/feature/<element_type>/<oid>')
def show_best_feature(element_type, oid):
    ele = get_element_or_404(element_type, oid)
    feature = db.matchBestSolo(ele)
    return jsonify(cn=common_name(ele),
                   feature=feature.name)

@app.route('/api/allfeatures/<element_type>/<oid>')
def show_all_feature(element_type, oid):
    ele = get_element_or_404(element_type, oid)
    features = db.matchAllSolo(ele)
    features_names = [f.name for f in features]
    return jsonify(cn=common_name(ele),
                   features=features_names)

@app.route('/api/changeset/<changesetid>')
def show_changeset(changesetid):
    cset = get_changeset_or_404(changesetid)
    sentence = sentence_from_changeset(cset)
    return sentence

if __name__ == '__main__':
    app.debug = True
    app.run()
