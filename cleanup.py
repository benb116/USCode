from xml.dom import minidom
import os

codedir = 'Code/'
titles = [
  'usc01.xml',  'usc02.xml',  'usc03.xml',  'usc04.xml',
  'usc05.xml',  'usc05A.xml', 'usc06.xml',  'usc07.xml',
  'usc08.xml',  'usc09.xml',  'usc10.xml',  'usc11.xml',
  'usc11a.xml', 'usc12.xml',  'usc13.xml',  'usc14.xml',
  'usc15.xml',  'usc16.xml',  'usc17.xml',  'usc18.xml',
  'usc18a.xml', 'usc19.xml',  'usc20.xml',  'usc21.xml',
  'usc22.xml',  'usc23.xml',  'usc24.xml',  'usc25.xml',
  'usc26.xml',  'usc27.xml',  'usc28.xml',  'usc28a.xml',
  'usc29.xml',  'usc30.xml',  'usc31.xml',  'usc32.xml',
  'usc33.xml',  'usc34.xml',  'usc35.xml',  'usc36.xml',
  'usc37.xml',  'usc38.xml',  'usc39.xml',  'usc40.xml',
  'usc41.xml',  'usc42.xml',  'usc43.xml',  'usc44.xml',
  'usc45.xml',  'usc46.xml',  'usc47.xml',  'usc48.xml',
  'usc49.xml',  'usc50.xml',  'usc50A.xml', 'usc51.xml',
  'usc52.xml',  'usc54.xml'
]

removeTags = ['note', 'notes', 'sourceCredit', 'doc', 'dc', 'meta', 'property', 'ref']
removeAttr = ['style', 'class', 'id', 'role', 'value', 'border', 'xmlns', 'width', 'xmlns:xsi', 'xml:lang', 'xmlns:dcterms', 'xsi:schemaLocation', 'xmlns:dc']
removeStatus = ['repealed', 'omitted', 'transferred', 'reserved', 'renumbered']

def cleanTitle(name):
    print(name)
    xmldoc = minidom.parse(codedir+name)
    nodes = []

    # Find all nodes with bad tags
    for t in removeTags:
        tagnodes = xmldoc.getElementsByTagName(t)
        if t == 'ref':
            # Remove only ref tags with the idref attributes
            tagnodes = [x for x in tagnodes if ('idref' in x.attributes.keys())]

        nodes = nodes + tagnodes

    # Remove them
    for node in nodes:
        parent = node.parentNode
        parent.removeChild(node)

    # Remove all bad attributes
    # Also remove any sections with a bad status
    stripAttr(xmldoc)

    # Pretty print
    out = os.linesep.join([s for s in xmldoc.toprettyxml().strip().splitlines(True) if s.strip()])
    out2 = os.linesep.join([s for s in out.splitlines() if s])

    f = open(codedir+name, "w")
    f.write(out2.encode('utf-8'))
    f.close()

def stripAttr(node):
    if node.attributes:
        keys = list(node.attributes.keys()) if node.attributes else []
        for attribute in keys:
            if attribute == 'status':
                if node.getAttribute('status') in removeStatus:
                    parent = node.parentNode
                    parent.removeChild(node)
            elif attribute in removeAttr:
                node.removeAttribute(attribute)
    for child in node.childNodes:
        stripAttr(child)


for fn in titles:
    cleanTitle(fn)
# cleanTitle(titles[3])


