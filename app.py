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
 
class FlaskWithHamlish(Flask):
    jinja_options = ImmutableDict(
        extensions=['jinja2.ext.autoescape', 'jinja2.ext.with_',
                    'hamlish_jinja.HamlishExtension'] )
 
app = FlaskWithHamlish(__name__)
app.jinja_env.hamlish_mode = 'indented' # if you want to set hamlish settings

db = FeatureDB()

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
