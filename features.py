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

"""Contains functions related to Changemonger features for a yaml backend"""

import inflect
from sets import Set
import yaml
from magic import magic_features

inflection = inflect.engine()

def compare_precision(a, b):
    """Compare the precision of two features"""
    return precision(b) - precision(a)

def pluralize(feature):
    """Pluralize a feature (or category)"""
    return feature.get('plural', inflection.plural(feature['name']))

def precision(feature):
    """Get the precision of a feature"""
    ### Either use the explicit precision value or the number of tags * 2
    ### (this way we know that odd numbers are automatically set, ie
    ### building=yes is 1
    ama = feature.get('ama')
    if ama == 'category':
        return feature.get('precision', 3)
    elif ama == 'magic':
        return feature.get('precision', 2)
    else:
        # Assume it's a plain feature
        return feature.get('precision', len(feature['tags']) + 10)
class FeatureDB:
    """This is the abstraction against using the features"""
    def __init__(self):
        """Initialize feature database, use the argument as the filename"""
        self._features = []
        self._magic = magic_features()
        self._categories = {}

    def _get_or_make_category(self, category_name):
        """Either retrieve a category or create one as necessary"""
        category = self._categories.get(category_name)
        if not category:
            category = {'name': category_name, 'ama': 'category',
                        'features': []}
            self._categories[category_name] = category
        return category

    def _yaml_dict_to_feature(self, item):
        """Convert yaml item to feature"""
        feature = item
        tags = item.get('tags', [])
        if isinstance(tags, basestring):
            feature['tags'] = tags = [tags]
        category_names = item.get('categories', [])
        if isinstance(category_names, basestring):
            category_names = [category_names]
        feature['categories'] = [self._get_or_make_category(name)
                                 for name in category_names]
        if item.has_key('precision'):
            feature['precision'] = int(item['precision'])
        return feature

    def load_yaml_categories(self, fname):
        """Load a yaml file full of categories into the database"""
        with open(fname) as fd:
            data = fd.read()
            yamldata = yaml.safe_load(data)
            for item in yamldata:
                name = item.get('name')
                if not name:
                    continue
                category = self._get_or_make_category(name)
                if item.has_key('precision'):
                    category['precision'] = int(item['precision'])
                
    def load_yaml_features(self, fname):
        """Load a yaml of features file into the database"""
        with open(fname) as fd:
            data = fd.read()
            yamldata = yaml.safe_load(data)
            for item in yamldata:
                feature = self._yaml_dict_to_feature(item)
                self._features.append(feature)

    def matchFeature(self, feature, ele):
        """Check if element matches feature"""
        if feature.has_key('types'):
            if not ele['type'] in feature['types']:
                return False
        if not feature.has_key('tags'):
            print "WAIT!!!!!!!!!!! " + feature['name'] + " has no tags\n\n"
        for tag in feature['tags']:
            if not tag in ele['_tags']:
                return False
            return feature
        return False

    def matchMagic(self, feature, ele):
        """Check if element matches magic feature"""
        # magic features act like normal features, but they have a
        # match function stored as an anonymous function in their
        # 'match' key
        if feature.has_key('types'):
            if not ele['type'] in feature['types']:
                return False
        if feature['match'](ele):
            return feature

    def matchCategory(self, category, ele):
        """Check if element matches category"""
        for feature in category['features']:
            if self.matchFeature(feature, ele):
                return category

    def matchBestSolo(self, ele):
        """Returns the best matching feature for an element"""
        # This function is not optimized in any way. Ideally it should
        # run in mongodb or maybe even some other way, but it's quick
        # and dirty and it works.
        match = None
        match_val = -10
        for feature in self._features:
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
        features = [feature for feature in self._features
                    if self.matchFeature(feature, ele)]
        cat_names = Set()
        for feature in features:
            for category in feature['categories']:
                cat_names.add(category['name'])
        categories = [self._categories[name] for name in cat_names]
        magic = [mag for mag in self._magic if self.matchMagic(mag, ele)]
        features.extend(categories)
        features.extend(magic)
        return(sorted(features, cmp=compare_precision))

    def matchEach(self, coll):
        """Returns all the matches for all the elements in the collection"""
        return [self.matchAllSolo(ele) for ele in coll]
