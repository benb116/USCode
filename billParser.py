from xml.dom import minidom
import os

billdir = 'Bills/'
name = 'BILLS-117hr27ih.xml'

xmldoc = minidom.parse(billdir+name)
congressNum = xmldoc.getElementsByTagName('congress')[0].firstChild.nodeValue.split(' ')[0][:-2]
billID = xmldoc.getElementsByTagName('legis-num')[0].firstChild.nodeValue.replace('.', '').replace(' ','')
print(congressNum+'-'+billID)

officialTitle = xmldoc.getElementsByTagName('official-title')[0].firstChild.nodeValue
shortTitle = xmldoc.getElementsByTagName('short-title')[0].firstChild.nodeValue
print(shortTitle)

legisbody = xmldoc.getElementsByTagName('legis-body')[0]

def extractVal(node):
    print(node.nodeName)
    if node.nodeName in ['term', 'quote', 'short-title']:
        print('aa')
        out = ('' if node.nodeValue == None else node.nodeValue)
        for cn in node.childNodes:
            print('c')
            print(cn)
            out += extractVal(cn)

        return out

    if node.attributes:
        keys = list(node.attributes.keys()) if node.attributes else []
        for attribute in keys:
            if attribute == 'parsable-cite':
                return node.getAttribute('parsable-cite')

    return node.nodeValue

def iterate(div, path):
    # print(div.nodeName, path)

    # if div.nodeName == 'external-xref':
        # ref = div.getAttribute('parsable-cite')
        # print(ref)

    if div.nodeName == 'text':
        # print(div.childNodes)
        ooot = ''
        for div1 in div.childNodes:
            print(div1.nodeName)
            if div1.nodeName != '#text':
                ooot += extractVal(div1)
                # print('bb')
            else:
                ooot += div1.nodeValue
            div.removeChild(div1)
        print('ooot', ooot)
        div.nodeValue = ooot
    # if (div.nodeName == '#text') and ("is amended" in div.nodeValue):
        # print('t', div.nodeValue)
    else:
        for div1 in div.childNodes:
            iterate(div1, path+div.nodeName+'/')

def iterate2(div, path):
    # print(div.nodeName, path)

    if div.nodeName == 'text':
        print(div.nodeValue)
    # if (div.nodeName == '#text') and ("is amended" in div.nodeValue):
        # print('t', div.nodeValue)
    else:
        for div1 in div.childNodes:
            iterate2(div1, path+div.nodeName+'/')

iterate(legisbody, '/')
print('qwqewq')
iterate2(legisbody, '/')