"""Contains functions related to Changemonger features"""

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
    return feature.get('precision', len(feature['tags']))

def makeMagicFeatures():
    features = []
    def untagged(ele):
        if len(ele['tags']) == 0:
            return True

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
    return features

class FeatureDB:
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
        if not match:
            # The object doesn't match the normal features, we'll have
            # to test it against the base "magic" features.
            for feature in self._magic:
                if (precision(feature) > match_val
                     and self.matchMagic(feature, ele)):
                    # We rely on the fact that magic features are
                    # always listed in order of precision
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

