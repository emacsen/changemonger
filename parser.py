def dict2list(d):
    """Function that turns a dictionary into a list of key=value strings"""
    l = []
    for k, v in d.items():
        l.append(u'%s=%s' % (k, v))
    return l

def parseTags (tags):
    d = {}
    for tag in tags:
        d[tag.attrib['k']] = tag.attrib['v']
    return d

def parseAttribs (attribs):
    d = {}
    for k,v in attribs.items():
        d[k] = v
    return d

def parseNode (node):
    d = {'type': 'node'}
    d.update(parseAttribs(node.attrib))
    d['tags'] = parseTags(node.findall('tag'))
    d['_tags'] = dict2list(d['tags'])
    return d

def parseWay (way):
    d = {'type': 'way', 'nd': []}
    d.update(parseAttribs(way.attrib))
    for nd in way.findall('nd'):
        d['nd'].append(nd.attrib['ref'])
    d['tags'] = parseTags(way.findall('tag'))
    d['_tags'] = dict2list(d['tags'])
    return d

def parseRelation (rel):
    d = {'type': 'relation', 'members': []}
    d.update(parseAttribs(rel.attrib))
    for m in rel.findall('member'):
        d['members'].append({'type': m.attrib['type'],
                             'ref': m.attrib['ref'],
                             'role': m.attrib['role']})
    d['tags'] = parseTags(rel.findall('tag'))
    d['_tags'] = dict2list(d['tags'])
    return d

def parseChange (osmchange):
    c = []
    for action in osmchange.getchildren():
        elements = []
        for element in action.getchildren():
            if element.tag == 'node':
                ele = parseNode(element)
            elif element.tag == 'way':
                ele = parseWay(element)
            elif element.tag == 'relation':
                ele = parseRelation(element)
            ele['_action'] = action.tag
            elements.append(ele)
        c.append((action.tag, elements))
    return c

def parseChangeset (changeset):
    d = {'type': 'changeset'}
    d.update(parseAttribs(changeset.attrib))
    d['tags'] = parseTags(changeset.findall('tag'))
    return d
    
