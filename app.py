from flask import Flask, jsonify
app = Flask(__name__)
app.debug = True
from helpers import *
from features import FeatureDB

db = FeatureDB()
populate_features_in_yaml(db, 'features.yaml')

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
    ele_features = zip(eles, db.matchEach(eles))
    sorted_ef = sort_by_num_features(ele_features)
    grouped_features = feature_grouper(sorted_ef)
    sorted_features = sort_grouped(grouped_features)
    english_list =  grouped_to_english(sorted_features)
    return "%s %s %s" % (user, action, english_list)


if __name__ == '__main__':
    app.run()
    
