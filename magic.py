##
## This file is essentially a configuration file, so is not licensed
## with the AGPL.
##
"""This file contains the magic_features function, which returns a
list of magic features

"""
def magic_features():
    """Create the magic feature set"""
    features = []
    # Pythonistias will complain about using lambda this way- oh well.
    untagged = lambda ele: (len(ele['tags']) == 0)
    always = lambda ele: True
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
