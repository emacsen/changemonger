##
## This file is essentially a configuration file, so is not licensed
## with the AGPL.
##
"""This file contains the magic_features function, which returns a
list of magic features

"""
from features import BaseFeature

class OSMElement(BaseFeature):
    def __init__(self):
        BaseFeature.__init__(self, "unidentified object")
        self.precision = 0
        self.plural = "assorted objects"

    def match(self, ele):
        return True

class UnidentifiedElement(BaseFeature):
    def __init__(self, type):
        BaseFeature.__init__(self, "unidentified " + type)
        self.precision = 1
        self.types = [type]

    def match(self, ele):
        return self._typecheck(ele)

class UntaggedElement(BaseFeature):
    def __init__(self, type):
        BaseFeature.__init__(self, "untagged " + type)
        self.precision = 2
        self.types = [type]

    def match(self, ele):
        return self._typecheck(ele) and not ele['tags']

class UnidentifiedPolygon(BaseFeature):
    def __init__(self):
        BaseFeature.__init__(self, "unidentified polygon")
        self.precision = 3
        self.types = ['way']

    def match(self, ele):
        return (self._typecheck(ele) and ele['nd'][0] == ele['nd'][-1])

class Building(BaseFeature):
    def __init__(self):
        BaseFeature.__init__(self, "building")
        self.precision = 5
        self.types = ['way', 'relation']

    def match(self, ele):
        return (self._typecheck(ele) and ele['tags'].has_key('building'))

class ManMade(BaseFeature):
    def __init__(self):
        BaseFeature.__init__(self, "man made feature")
        self.precision = 5
        
    def match(self, ele):
        return ele['tags'].has_key('man_made')
        

class Shop(BaseFeature):
    def __init__(self):
        BaseFeature.__init__(self, "shop")
        self.precision = 6
        
    def match(self, ele):
        return ele['tags'].has_key('shop')

def magic():
    """Create the magic feature set"""
    features = []
    features.append(OSMElement())
    features.append(UnidentifiedElement("node"))
    features.append(UnidentifiedElement("way"))
    features.append(UnidentifiedElement("relation"))
    features.append(UntaggedElement("node"))
    features.append(UntaggedElement("way"))
    features.append(UntaggedElement("relation"))
    features.append(UnidentifiedPolygon())
    features.append(Building())
    features.append(ManMade())
    features.append(Shop())

    return features
