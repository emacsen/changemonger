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
from features import precision
import helpers
from elements import common_name, display_name
from werkzeug import ImmutableDict
import changemonger

class FlaskWithHamlish(Flask):
    jinja_options = ImmutableDict(
        extensions=['jinja2.ext.autoescape', 'jinja2.ext.with_',
                    'hamlish_jinja.HamlishExtension'] )
 
app = FlaskWithHamlish(__name__)
app.jinja_env.hamlish_mode = 'indented' # if you want to set hamlish settings
app.jinja_env.globals.update(precision=precision)

@app.route('/')
def index():
    return render_template('index.haml')

@app.route('/api.html')
def display_api_docs():
    return render_template('api.haml')

@app.route('/node')
def display_node():
    if request.args.has_key('id'):
        id = request.args['id']
        ele = helpers.get_node_or_404(id)
        features = changemonger.features(ele)
        return render_template('node_details.haml',
                               name = display_name(ele, features[0]),
                               node = ele,
                               features = features)
    else:
        return render_template('node.haml', title="Bad Node")

@app.route('/way')
def display_way():
    if request.args.has_key('id'):
        id = request.args['id']
        ele = helpers.get_way_or_404(id)
        features = changemonger.features(ele)
        return render_template('way_details.haml',
                               name = display_name(ele, features[0]),
                               node = ele,
                               features = features)
    else:
        return render_template('way.haml', title="Bad Way")

@app.route('/relation')
def display_relation():
    if request.args.has_key('id'):
        id = request.args['id']
        ele = helpers.get_relation_or_404(id)
        features = changemonger.features(ele)
        return render_template('relation_details.haml',
                               name = display_name(ele, features[0]),
                               node = ele,
                               features = features)
    else:
        return render_template('relation.haml', title="Bad Way")

@app.route('/changeset')
def display_changeset():
    if request.args.has_key('id'):
        id = request.args['id']
        cset = helpers.get_changeset_or_404(id)
        sentence = changemonger.changeset_sentence(cset)
        return render_template('changeset_details.haml',
                               changeset = cset,
                               sentence = sentence)
    else:
        return render_template('changeset.haml', title="Bad Changeset")

@app.route('/features')
def show_features():
    return render_template('features.haml',
                           features = changemonger.db._features)

@app.route('/dbstats')
def show_stats():
    return jsonify(features=len(changemonger.db._features),
                   categories=len(changemonger.db._categories))

@app.route('/api/features/node/<id>')
def api_node(id):
    ele = helpers.get_node_or_404(id)
    features = changemonger.features(ele)
    features_names = [f.name for f in features]
    return jsonify(cn=common_name(ele),
                   features=features_names)

@app.route('/api/features/way/<id>')
def api_way(id):
    ele = helpers.get_way_or_404(id)
    features = changemonger.features(ele)
    features_names = [f.name for f in features]
    return jsonify(cn=common_name(ele),
                   features=features_names)

@app.route('/api/features/relation/<id>')
def api_relation(id):
    ele = helpers.get_relation_or_404(id)
    features = changemonger.features(ele)
    features_names = [f.name for f in features]
    return jsonify(cn=common_name(ele),
                   features=features_names)

@app.route('/api/changeset/<id>')
def show_changeset(id):
    cset = helpers.get_changeset_or_404(id)
    sentence = changemonger.changeset_sentence(cset)
    return jsonify(sentence=sentence)

if __name__ == '__main__':
    app.debug = True
    app.run()
