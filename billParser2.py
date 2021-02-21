from xml.dom import minidom
import os

billdir = 'Bills/'
name = 'BILLS-117hr127ih.xml'

xmldoc = minidom.parse(billdir+name)
congressNum = xmldoc.getElementsByTagName('congress')[0].firstChild.nodeValue.split(' ')[0][:-2]
billID = xmldoc.getElementsByTagName('legis-num')[0].firstChild.nodeValue.replace('.', '').replace(' ','')
print(congressNum+'-'+billID)

officialTitle = xmldoc.getElementsByTagName('official-title')[0].firstChild.nodeValue
shortTitle = xmldoc.getElementsByTagName('short-title')[0].firstChild.nodeValue
print(shortTitle)

legisbody = xmldoc.getElementsByTagName('legis-body')[0]

currentLevel = ''
ref = ''
gointoquote = False

def iterate(div):
    print(div.nodeName)
    currentLevel = div.nodeName
    if currentLevel == 'external-xref':
        ref = div.attributes['parsable-cite'].nodeValue
        print(ref)

    if currentLevel == 'quoted-block':
        print('go')
        return

    if len(div.childNodes) == 0:
        print('new')
        print(div.nodeValue)

        if 'is amended by adding at the end the following' in div.nodeValue:
            print('122')
            gointoquote = True

        if 'is amended by inserting after' in div.nodeValue:
            print

        return

    if div.firstChild.nodeValue == None:
        # print(div.childNodes)
        if len(div.getElementsByTagName('short-title')) > 0:
            return
        for div1 in div.childNodes:
            iterate(div1)

for div in legisbody.childNodes:
    iterate(div)
