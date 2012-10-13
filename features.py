##  Changemonger: An OpenStreetMap change analyzer
##  Copyright (C) 2012 Serge Wroclawski
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
import yaml
import os.path
import imp

inflection = inflect.engine()

class BaseFeature:
    """The base feature class"""
    def __init__(self, name):
        "Init the object"
        self.name = name
        self.types = []
        self.categories = []
        self.named = True
        self.id = unicode(id(self))
        self._prominence = 0

    @property
    def prominence(self, ele):
        """How important a feature is"""
        score = 0
        tags = ele['tags']
        if len(ele['tags']) > 0:
            score += 1
        if ( tags.get('name') or tags.get('brand') or tags.get('operator') ):
            score += 2
        if tags.get('historical') or tags.get('wikipedia'):
            score += 3

        return score + self._prominence

    def _typecheck(self, ele):
        "Check that the element matches this feature's type"
        if self.types:
            if ele['type'] in self.types:
                return True
            else:
                return False
        else:
            return True

    def category(self, cat):
        "Add a category to this feature"
        self.categories.append(cat)
    
    def match(self, element):
        "Generic function"
        # Never use this directly
        return True

    @property
    def plural(self):
        "Returns the plural version of the feature's name"
        return inflection.plural(self.name)

    @property
    def precision(self):
        "Returns the precision of the object. This should be set"
        return 0

class SimpleFeature(BaseFeature):
    """A simple feature (most objects in the yaml files are SimpleFeatures"""
    def __init__(self, name):
        "Init simple feature"
        self.tags = []
        BaseFeature.__init__(self, name)

    def tag(self, tg):
        "Add a tag to object's tags"
        self.tags.append(tg)

    def match(self, element):
        "Matches for simple features uses tags"
        if self._typecheck(element):
            for tag in self.tags:
                if not tag in element['_tags']:
                    return False
            else:
                return True
        else:
            return False

    @property
    def precision(self):
        "Simple features have a precision of 10 + # of tags by default"
        return 10 + len(self.tags)

class Category(BaseFeature):
    "Feature categories"
    def __init__(self, name):
        "Init a category"
        self.features = []
        BaseFeature.__init__(self, name)

    def register(self, feature):
        "Register a feature to this category"
        self.features.append(feature)
    
    def match(self, element):
        "The category checks all features for matches"
        for feature in self.features:
            if feature.match(element):
                return True
        return False

    @property
    def precision(self):
        "Categories are precision 3 by default"
        return 3

def compare_precision(a, b):
    """Compare the precision of two features"""
    return b.precision - a.precision

class FeatureDB:
    """This is the abstraction against using the features"""
    def __init__(self, directory = 'features'):
        """Initialize feature database, use the argument as the directory"""
        self._simple = []
        self._magic = []
        # We almost never iterate through categories, but we do call
        # them by name a lot
        self._categories = {}
        # The index contains unique IDs for features
        self._index = {}

        # Now load the actual features
        if not os.path.isabs(directory):
            directory = os.path.abspath(directory)
        # We're going to just assume the directory exists for now
        
        if os.path.exists(os.path.join(directory, 'features.yaml')):
            self._load_yaml_simple_features(
                os.path.join(directory, 'simple.yaml'))
        elif os.path.isdir(os.path.join(directory, 'simple')):
            self._load_simple_directory(os.path.join(directory, 'simple'))
        
        if os.path.exists(os.path.join(directory, 'categories.yaml')):
            self._load_yaml_categories(os.path.join(directory,
                                                    'categories.yaml'))

        if os.path.exists(os.path.join(directory, 'magic.py')):
            self._load_magic_file(directory)
    
    @property
    def all(self):
        """Return all objects in the database"""
        return self._simple + self._categories.values() + self._magic

    def _load_magic_file(self, directory):
        """Load a magic (plain python) features file"""
        fp, pathname, description = imp.find_module('magic', [directory])
        try:
            module = imp.load_module('magic', fp, pathname, description)
            features = module.magic()
            for feature in features:
                self._magic.append(feature)
                self._index[feature.id] = feature
        finally:
            if fp:
                fp.close()

    def _load_simple_directory(self, dirname):
        """Load a directory of feature files"""
        for subdir, dirs, files in os.walk(dirname):
            for fname in files:
                name, ext = os.path.splitext(fname)
                if ext == '.yaml' and name[0] != '.':
                    self._load_yaml_simple_features(
                        os.path.join(dirname, fname))

    def _get_or_make_category(self, name):
        """Either retrieve a category or create one as necessary"""
        category = self._categories.get(name)
        if not category:
            category = Category(name)
            self._categories[name] = category
            self._index[category.id] = category
        return category

    def _yaml_item_to_feature(self, item):
        """Takes a yaml item and returns a Feature object"""
        feature = SimpleFeature(item['name'])
        # type
        if item.has_key('types'):
            if isinstance(item['types'], basestring):
                feature.types = item['types'].split(',')
            else:
                feature.types = item['types']
        # id (virtually unused)
        if item.has_key('id'):
            feature.id = unicode(item['id'])
        # tags
        if isinstance(item['tags'], basestring):
            tags = item['tags'].split(',')
        else:
            tags = item['tags']
        for tag in tags:
            feature.tag(tag)
        # plural
        if item.has_key('plural'):
            feature.plural = item['plural']
        # precision
        if item.has_key('precision'):
            feature.precision = int(item['precision'])
        # categories
        if item.has_key('categories'):
            if isinstance(item['categories'], basestring):
                categories = item['categories'].split(',')
            else:
                categories = item['categories']
            for cat_name in categories:
                category = self._get_or_make_category(cat_name)
                category.register(feature)
                feature.category(category)
        # Named?
        if item.has_key('named'):
            feature.named = item['named']

        # Prominence
        if item.has_key('promience'):
            feature._promience = item['prominence']

        return feature

    def _load_yaml_categories(self, fname):
        """Load a yaml file full of categories into the database"""
        with open(fname) as fd:
            data = fd.read()
            yamldata = yaml.safe_load(data)
            for item in yamldata:
                category = self._get_or_make_category(item['name'])
                
    def _load_yaml_simple_features(self, fname):
        """Load a yaml of features file into the database"""
        with open(fname) as fd:
            data = fd.read()
            yamldata = yaml.safe_load(data)
            for item in yamldata:
                # Make this a feature
                feature = self._yaml_item_to_feature(item)
                self._simple.append(feature)
                self._index[feature.id] = feature
    
    def add_index(self, feature):
        """Add feature id to internal id index"""
        if self.get(feature.id):
            ### We need a real way to handle this...
            print "BAD BAD BAD!!!! ID CONFLICT BETWEEN %s and %s" % (self.get(feature.id).name, feature.name)
        self._index[feature.id] = feature

    def matchBestSolo(self, ele):
        """Returns the best matching feature for an element"""
        # This function is not optimized in any way. Ideally it should
        # run in mongodb or maybe even some other way, but it's quick
        # and dirty and it works.
        match = None
        match_val = -10
        for feature in self.all:
            if feature.precision > match_val and feature.match(ele):
                match = feature
                match_val = feature.precision
        return match

    def matchAllSolo(self, ele):
        """Return all the matching features and categories for an
        element, sorted by precision
        """
        features = []
        for feature in self.features:
            if feature.match(ele):
                features.append(feature)
        return(sorted(features, cmp=compare_precision))

    def matchEach(self, coll):
        """Returns all the matches for all the elements in the collection"""
        return [self.matchAllSolo(ele) for ele in coll]

    def get(self, id):
        "Retrieve an object by index id"
        return self._index[id]

    @property
    def simple(self):
        "Retrieve the simple features"
        return self._simple
    
    @property
    def categories(self):
        "Retrieve the categories"
        return self._categories.values()
    
    @property
    def magic(self):
        "Retrieve the magic features"
        return self._magic

    @property
    def features(self):
        "Return all features"
        return self._simple + self._categories.values() + self._magic
