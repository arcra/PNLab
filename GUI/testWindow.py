# -*- coding: utf-8 -*-
"""
@author: Adrián Revuelta Cuauhtli
"""

import Tkinter

from PetriNets import PetriNet, Place, PlaceTypes, Transition, TransitionTypes, Vec2
from GUI.PNEditorWidget import PNEditor

class testWindow(object):
    
    def __init__(self):
        super(testWindow, self).__init__()
        self.root = Tkinter.Tk()
        self.pn = PetriNet(name = 'test')
        p1 = Place('myAction', PlaceTypes.ACTION, Vec2(150, 250))
        t = Transition('transition1', TransitionTypes.IMMEDIATE, Vec2(250, 250), False)
        p2 = Place('result', PlaceTypes.PREDICATE, Vec2(500, 250))
        self.pn.add_place(p1)
        self.pn.add_place(p2)
        self.pn.add_transition(t)
        self.pn.add_arc(p1, t)
        self.pn.add_arc(t, p2)
    
        self.pne = PNEditor(self.root, width=600, height=400, grid = True, PetriNet = self.pn)
        self.pne.grid({'row': 0, 'column': 0})
    
        self.btn = Tkinter.Button(self.root, text = 'Reload Petri Net', command = self.btnCallback)
        self.btn.grid({'row': 1, 'column': 0})
    
    def btnCallback(self):
        self.pn = self.pne.petri_net
        self.pne.set_petri_net(self.pn)
    
if __name__ == '__main__':
    w = testWindow()
    
    Tkinter.mainloop()