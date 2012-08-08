import inflect
from functools import cmp_to_key

p = inflect.engine()

def dict2list(d):
    l = []
    for k,v in d.items():
        l.append(u'%s=%s' % (k,v))
    return l

def compare_precision(a, b):
    return b.precision - a.precision

class Feature:
    def __init__(self, name):
        self.name = name
        self.tags = []
        self.categories = []
        self.types = None
        self.use_name = True

    @property
    def plural(self):
        return p.plural(self.name)

    @property
    def precision(self):
        return len(self.tags)

    def match(self, element):
        if self.types:
            if not element['type'] in self.types:
                return False
        for tag in self.tags:
            if not tag in element['_tags']:
                return False
            return True
        else:
            return False

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return self.name

class Category(Feature):
    def __init__(self,  name):
        self.name = name
        self.features = []
        self.index = {}
        self.precision = 0

    def register(self, feature):
        if not self.index.has_key(feature.name):
            self.index[feature.name] = feature
            self.features.append(feature)
        
    def match(self, element):
        for feature in self.features:
            if feature.match(element):
                return True
        return False

def makeMagicFeatures():
    l = []
    utag_node = Feature("untagged node")
    utag_node.precision = 0
    def match(e):
        if e['type'] == 'node' and len(e['tags']) == 0:
            return True
    utag_node.match = match
    l.append(utag_node)

    utag_way = Feature("untagged way")
    utag_way.precision = 0
    def match(e):
        if e['type'] == "way" and len(e['tags']) == 0:
            return True
    utag_way.match = match
    l.append(utag_way)

    utag_rel = Feature("untagged relation")
    utag_rel.precision = 0
    def match(e):
         if e['type'] == "relation" and len(e['tags']) == 0:
             return True
    utag_way.match = match
    l.append(utag_rel)

    node = Feature("unidentified node")
    node.precision = -1
    def match(e):
        if e['type'] == "node":
            return True
    node.match = match
    l.append(node)

    way = Feature("unidentified way")
    way.precision = -1
    def match(e):
        if e['type'] == "way":
            return True
    way.match = match
    l.append(way)

    rel = Feature("unidentified relation")
    rel.precision = -1
    def match(e):
        if e['type'] == "relation":
            return True
    rel.match = match
    l.append(rel)

    return l

class FeatureDB:
    def __init__(self):
        self._magic = makeMagicFeatures()
        self._categories = []
        self._categories_index = {}
        self._features = []
        self._node_features = []
        self._way_features = []
        self._rel_features = []

    def addCategory(self, category):
        self._categories_index[category.name] = category
        self._categories.append(category)

    def addFeature(self, feature):
        self._features.append(feature)
        if feature.types:
            if "node" in feature.types:
                self._node_features.append(feature)
            if "way" in feature.types:
                self._way_features.append(feature)
            if "relation" in feature.types:
                self_rel_features.append(feature)
        else:
            # A feature with no listed types is applicable to all types
            self._node_features.append(feature)
            self._way_features.append(feature)
            self._rel_features.append(feature)

        for category_name in feature.categories:
            if self._categories_index.has_key(category_name):
                self._categories_index[category_name].register(feature)
            else:
                cat = Category(category_name)
                cat.register(feature)
                self.addCategory(cat)

    def _getFeatureList(self, ele_type):
        if ele_type == 'node':
            return self._node_features
        elif ele_type == 'way':
            return self._way_features
        elif ele_type == 'relation':
            return self._rel_features

    def matchBestSolo(self, ele):
        features = self._getFeatureList(ele['type'])
        match = None
        match_val = -10
        if not ele.has_key('_tags'):
            ele['_tags'] = dict2list(ele['tags'])
        for feature in features:
            print "%d %s %f" % (match_val, feature.name, feature.precision)
            if feature.precision > match_val and feature.match(ele):
                print "Matched"
                match = feature
                match_val = feature.precision
        if match:
            return match
        else:
            for feature in self._magic:
                if feature.precision > match_val and feature.match(ele):
                    return feature

    def matchAllSolo(self, ele):
        if not ele.has_key('_tags'):
            ele['_tags'] = dict2list(ele['tags'])
        r = []
        features = self._getFeatureList(ele['type'])
        r.extend([f for f in features if f.match(ele)])
        r.extend([c for c in self._categories if c.match(ele)])
        r.extend([f for f in self._magic if f.match(ele)])
        return sorted(r, cmp=compare_precision)

    def matchEach(self, coll):
        return [self.matchAllSolo(ele) for ele in coll]

