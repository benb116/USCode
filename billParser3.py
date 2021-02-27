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

currentLevel = 0
ref = ''
gointoquote = False

def iterate(div, ret):
    global currentLevel
    # print(currentLevel)
    currentLevel += 1
    
    if div.nodeName == 'external-xref':
        ref = div.childNodes[0].nodeValue
        nsns = xmldoc.createTextNode(ref)
        par = div.parentNode
        par.insertBefore(nsns, div)
        par.removeChild(div)
        # return

    print(currentLevel, div.nodeName, div.nodeValue)

    if len(div.childNodes) == 0:
        if "is amended" in div.nodeValue:
            print('amamama')


    if div.childNodes:
        # print(div.childNodes)
        for div1 in div.childNodes:
            if div1.nodeName != "quoted-block":
                iterate(div1, False)
            else:
                print('QB')

    currentLevel -= 1

for div in legisbody.childNodes:
    iterate(div, False)

for div in legisbody.childNodes:
    iterate(div, False)
