import yaml
from pprint import pprint
from pymongo import Connection
connection = Connection()

db = connection.changemonger

features = db.features

def get_or_make_category(category_name):
    category = categories.find_one({'name': category_name})
    if category:
        return category
    else:
        cat_id = categories.insert({'name': category_name, 'features': [],
                                    'ama': 'category', 'precision': 0})
        category = categories.find_one({'_id': cat_id})
        return category

def yaml_dict_to_feature(item):
    feature = item
    tags = item.get('tags', [])
    if isinstance(tags, basestring):
        feature['tags'] = tags = [tags]
    category_names = item.get('categories', [])
    if isinstance(category_names, basestring):
        category_names = [category_names]
    feature_categories = [get_or_make_category(name)
                          for name in category_names]
    feature['categories'] = [cat['_id'] for cat in feature_categories]
    return feature

def load_yaml(fname='dump.yaml'):
    with open(fname) as fd:
        data = fd.read()
        yamldata = yaml.safe_load(data)
        for item in yamldata:
            feature = yaml_dict_to_feature(item)
            fid = features.insert(feature)
            for category_id in feature.get('categories', []):
                category = features.find_one({'_id': category_id})
                if category.has_key('features'):
                    category['features'].append(fid)
                else:
                    category['features'] = [fid]
                features.save(category)

if __name__ == '__main__':
    loadyaml()
