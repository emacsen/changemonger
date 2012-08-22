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
import os.path
import imp

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
    def __init__(self, directory = 'features'):
        """Initialize feature database, use the argument as the directory"""
        self._features = []
        self._magic = []
        # We almost never iterate through categories, but we do call
        # them by name a lot
        self._categories = {}
        # This is only used for external apps (like the web app) to
        # look for features by ID
        self._index = {}

        # Now load the actual features
        if not os.path.isabs(directory):
            directory = os.path.abspath(directory)
        # We're going to just assume the directory exists for now
        
        if os.path.exists(os.path.join(directory, 'features.yaml')):
            db._load_yaml_simple_features(
                os.path.join(directory, 'simple.yaml'))
        elif os.path.isdir(os.path.join(directory, 'simple')):
            self._load_simple_directory(os.path.join(directory, 'simple'))
        
        if os.path.exists(os.path.join(directory, 'categories.yaml')):
                self._load_yaml_categories(os.path.join(directory,
                                                        'categories.yaml'))

        if os.path.exists(os.path.join(directory, 'magic.py')):
            self._load_magic_file(directory)

    def _load_magic_file(self, directory):
        fp, pathname, description = imp.find_module('magic', [directory])
        try:
            module = imp.load_module('magic', fp, pathname, description)
            features = module.magic()
            for feature in features:
                feature['id'] = feature.get('id', id(feature))
                feature['id'] = unicode(feature['id'])
                self._magic.append(feature)
                self._index[feature['id']] = feature
        finally:
            if fp:
                fp.close()

    def _load_simple_directory(self, dirname):
        for subdir, dirs, files in os.walk(dirname):
            for fname in files:
                name, ext = os.path.splitext(fname)
                if ext == '.yaml' and name[0] != '.':
                    self._load_yaml_simple_features(
                        os.path.join(dirname, fname))

    def _get_or_make_category(self, category_name):
        """Either retrieve a category or create one as necessary"""
        category = self._categories.get(category_name)
        if not category:
            category = {'name': category_name, 'ama': 'category',
                        'features': []}
            category['id'] = unicode(id(category))
            self._categories[category_name] = category
            self._index[category['id']] = category
        return category

    def _yaml_dict_to_feature(self, item):
        """Convert yaml item to feature"""
        feature = item
        feature['ama'] = 'simple'
        tags = item.get('tags', [])
        if isinstance(tags, basestring):
            feature['tags'] = tags = [tags]
        category_names = item.get('categories', [])
        if isinstance(category_names, basestring):
            category_names = [category_names]
        categories = []
        for cat_name in category_names:
            category = self._get_or_make_category(cat_name)
            category['features'].append(feature)
            categories.append(category)
        feature['categories'] = categories
        if item.has_key('precision'):
            feature['precision'] = int(item['precision'])
        return feature

    def _load_yaml_categories(self, fname):
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
                
    def _load_yaml_simple_features(self, fname):
        """Load a yaml of features file into the database"""
        with open(fname) as fd:
            data = fd.read()
            yamldata = yaml.safe_load(data)
            for item in yamldata:
                feature = self._yaml_dict_to_feature(item)
                feature['id'] = feature.get('id', id(feature))
                feature['id'] = unicode(feature['id'])
                self._features.append(feature)
                self._index[feature['id']] = feature

    def matchFeature(self, feature, ele):
        """Check if element matches feature"""
        if feature.has_key('types'):
            if not ele['type'] in feature['types']:
                return False
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

    def get(self, id):
        return self._index[id]
