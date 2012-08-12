import yaml
from pymongo import Connection
connection = Connection()

db = connection.changemonger

features = db.features

def dump_yaml(fname="dump.yml"):
    dicts = []
    for feature in features.find():
        category_names = [features.find_one({'_id': cat})['name']
                          for cat in feature['categories']]
        feature['categories'] = category_names
        dicts.append(feature)
    fd = open(fname, 'w')
    yaml.dump(dicts, fd)

if __name__ == '__main__':
    dumpyaml()
