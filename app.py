from flask import Flask, jsonify, request
app = Flask(__name__)
app.debug = True
from helpers import *
from features import FeatureDB

from flask import Flask, render_template
from werkzeug import ImmutableDict
 
class FlaskWithHamlish(Flask):
    jinja_options = ImmutableDict(
        extensions=['jinja2.ext.autoescape', 'jinja2.ext.with_',
                    'hamlish_jinja.HamlishExtension'] )
 
app = FlaskWithHamlish(__name__)
app.jinja_env.hamlish_mode = 'indented' # if you want to set hamlish settings

db = FeatureDB()
populate_features_in_yaml(db, 'features.yaml')

@app.route('/')
def index():
    return render_template('index.haml')

@app.route('/node/')
def display_node():
    if request.args.has_key('oid'):
        eleid = 'node:' + request.args['oid']
        ele = get_feature_or_404(eleid)
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

@app.route('/api/feature/<eleid>')
def show_best_feature(eleid):
    ele = get_feature_or_404(eleid)
    feature = db.matchBestSolo(ele)
    return jsonify(cn=common_name(ele),
                   feature=feature.name)

@app.route('/api/allfeatures/<eleid>')
def show_all_feature(eleid):
    ele = get_feature_or_404(eleid)
    features = db.matchAllSolo(ele)
    features_names = [f.name for f in features]
    r = {'cn': common_name(ele),
         'features': features_names}
    return json.dumps(r)

@app.route('/api/changeset/<changesetid>')
def show_changeset(changesetid):
    cset = get_changeset_or_404(changesetid)
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
    print "%d elements" % len(eles)
    add_local_way_references(eles)
    print "%d elements after local way references" % len(eles)
    add_local_relation_references(eles)
    print "%d elements after local relation references" % len(eles)
    add_remote_ways(eles)
    print "%d elements after remote way refrences" % len(eles)
    add_remote_relations(eles)
    print "%d elements after remote relation references" % len(eles)
    eles = remove_unnecessary_items(eles)
    print "%d elements after unnecessary items removal" % len(eles)
    eles = sort_elements(eles)
    print "%d elements after sorting" % len(eles)
    ## # We need to unique the features somehow
    ## eles = unique_elements2(eles)
    ## print "%d elements are uniquing elements" % len(eles)
    ele_features = zip(eles, db.matchEach(eles))
    sorted_ef = sort_by_num_features(ele_features)
    grouped_features = feature_grouper(sorted_ef)
    sorted_features = sort_grouped(grouped_features)
    english_list =  grouped_to_english(sorted_features)
    return "%s %s %s" % (user, action, english_list)

if __name__ == '__main__':
    app.debug = True
    app.run()
    
