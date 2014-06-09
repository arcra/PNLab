# -*- coding: utf-8 -*-
"""
@author: Adrián Revuelta Cuauhtli
"""
import lxml.etree as ET
from PetriNets import PetriNet

pn = PetriNet.from_pnml_file('/home/arcra/Desktop/test.pnml')[0]
p = pn.places['a.myAction']
pn.rename_place(p, 'test')
p = pn.places['p.result']
pn.rename_place(p, 'other test')

p._merge_treeElement()

ET.dump(pn._tree.getroot())

