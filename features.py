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

"""Contains functions related to Changemonger features for a mongodb backend"""

import inflect
from sets import Set
from pymongo import Connection
connection = Connection()

p = inflect.engine()

def dict2list(d):
    """Function that turns a dictionary into a list of key=value strings"""
    l = []
    for k, v in d.items():
        l.append(u'%s=%s' % (k, v))
    return l

def compare_precision(a, b):
    return precision(b) - precision(a)

def pluralize(feature):
    """Pluralize a feature (or category)"""
    return feature.get('plural', p.plural(feature['name']))

def precision(feature):
    ### Either use the explicit precision value or the number of tags * 2
    ### (this way we know that odd numbers are automatically set, ie
    ### building=yes is 1
    ama = feature.get('ama', 'feature')
    if ama == 'magic':
        return feature.get('precision', 2)
    elif ama == 'category':
        return feature.get('precision', 2)
    else:
        return feature.get('precision', 10 + len(feature['tags']))

def makeMagicFeatures():
    features = []
    def untagged(ele):
        return (len(ele['tags']) == 0)
    def always(ele):
        return True
    features.append({'name': 'untagged node',
                     'ama': 'magic',
                     'types': ['node'],
                     'precision': 0,
                     'match': untagged})
    features.append({'name': 'untagged way',
                     'types': ['way'],
                     'ama': 'magic',
                     'precision': 0,
                     'match': untagged})
    features.append({'name': 'untagged relation',
                     'types': ['relation'],
                     'ama': 'magic',
                     'precision': 0,
                     'match': untagged})
    features.append({'name': 'unidentified node',
                     'types': ['node'],
                     'ama': 'magic',
                     'precision': -1,
                     'match': always})
    features.append({'name': 'unidentified way',
                     'types': ['way'],
                     'ama': 'magic',
                     'precision': -1,
                     'match': always})
    features.append({'name': 'unidentified relation',
                     'types': ['relation'],
                     'ama': 'magic',
                     'precision': -1,
                     'match': always})
    features.append({'name': 'building',
                     'ama': 'magic',
                     'precision': 2,
                     'match': lambda ele: ele['tags'].has_key('building')})
    features.append({'name': 'shop',
                     'ama': 'magic',
                     'precision': 5,
                     'match': lambda ele: ele['tags'].has_key('shop')})
    features.append({'name': 'man made feature',
                     'ama': 'magic',
                     'precision': 3,
                     'match': lambda ele: ele['tags'].has_key('man_made')})
    return features

class FeatureDB:
    """This is the abstraction against using the features"""
    def __init__(self, db = connection['changemonger']):
        self._db = db
        self._features = db.features
        self._magic = makeMagicFeatures()

    def matchFeature(self, feature, ele):
        if feature.has_key('types'):
            if not ele['type'] in feature['types']:
                return False
        for tag in feature['tags']:
            if not tag in ele['_tags']:
                return False
            return feature
        return False

    def matchMagic(self, feature, ele):
        # magic features act like normal features, but they have a
        # match function stored as an anonymous function in their
        # 'match' key
        if feature.has_key('types'):
            if not ele['type'] in feature['types']:
                return False
        if feature['match'](ele):
            return feature

    def matchCategory(self, category, ele):
        for feature_id in category['features']:
            feature = self._features({'_id': feature_id})
            if self.matchFeature(feature, ele):
                return category

    def addCategory(self, name):
        category = self._features.find_one({'name': name,
                                            'ama': 'category'})
        if category:
            return category
        else:
            return self._features.insert({'name': name,
                                          'ama': 'category',
                                          'precision': 0,
                                          'features': []})

    def registerFeaturetoCategory(self, category, feature):
        if category.has_key('features'):
            if feature['_id'] in category['features']:
                return
            else:
                category['features'].append(feature['_id'])
        else:
            category['features'] = [feature['_id']]
        self._features.save(category)

    def modifyCategory(self, category):
        return self._features.save(category)

    def addFeature(self, name, tags, category_names = []):
        categories = [self.addCategory(cat_name) for cat_name in category_names]
        feature = {'name': name,
                   'tags': tags,
                   'categories': categories}
        feature_id = self._features.insert(feature)
        for cat_id in categories:
            category = self._features.find_one({'_id': cat_id})
            if category.has_key('features'):
                category['features'].append(feature_id)
            else:
                category['features'] = [feature_id]
            self._features.save(category)
    
    def matchBestSolo(self, ele):
        """Returns the best matching feature for an element"""
        # This function is not optimized in any way. Ideally it should
        # run in mongodb or maybe even some other way, but it's quick
        # and dirty and it works.
        match = None
        match_val = -10
        for feature in self._features.find():
            if (precision(feature) > match_val
                and self.matchFeature(feature, ele)):
                match = feature
                match_val = precision(feature)
        for feature in self._magic:
            if (precision(feature) > match_val
                and self.matchMagic(feature, ele)):
                match = feature
                match_val = precision(feature)
        return match

    def matchAllSolo(self, ele):
        """Return all the matching features and categories for an
        element, sorted by precision
        """
        category_ids = Set()
        features = [feature for feature in self._features.find()
                    if self.matchFeature(feature, ele)]
        for feature in features:
            category_ids.add(feature['categories'])
        # We don't need to check the categories manually, this is
        # faster
        categories = [self._features.find_one({'_id': cat_id})
                      for cat_id in category_ids]
        magic = [mag for mag in self._magic if self.matchMagic(mag, ele)]
        features.extend(categories)
        features.extend(magic)
        return(sorted(features, cmp=compare_precision))

    def matchEach(self, coll):
        return [self.matchAllSolo(ele) for ele in coll]

