# -*- coding: utf-8 -*-
"""
@author: Adrián Revuelta Cuauhtli
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import Tkinter
import tkFileDialog
import tkMessageBox

from PetriNets import PetriNet
from PNEditor import PNEditor

class testWindow(object):
    
    def __init__(self):
        super(testWindow, self).__init__()
        self.root = Tkinter.Tk()
        self.root.wm_title('PetriNet Lab - Test window')
        self.root.rowconfigure(0, weight = 1)
        self.root.columnconfigure(0, weight = 1)
        
#        self.pn = PetriNet(name = 'test')
#        p1 = Place('myAction', PlaceTypes.ACTION, Vec2(150, 250))
#        t = Transition('transition1', TransitionTypes.IMMEDIATE, Vec2(250, 250))
#        p2 = Place('result', PlaceTypes.PREDICATE, Vec2(500, 250))
#        self.pn.add_place(p1)
#        self.pn.add_place(p2)
#        self.pn.add_transition(t)
#        self.pn.add_arc(p1, t)
#        self.pn.add_arc(t, p2)
    
        self.pne = PNEditor(self.root, width=600, height=400, grid = True, name = 'test')
        #self.pne.disable()
        self.pne.bind('<Motion>', self.cursor_callback)
        self.pne.grid(row = 0, column = 0, sticky = Tkinter.NSEW)
        
        self.buttons_frame = Tkinter.Frame(self.root, height = 50)
        self.buttons_frame.grid(row = 1, column = 0)
    
        self.reload_btn = Tkinter.Button(self.buttons_frame, text = 'Reload Petri Net', command = self.btnCallback)
        self.reload_btn.grid(row = 0, column = 0)
        
        self.open_btn = Tkinter.Button(self.buttons_frame, text = 'Open PNML file', command = self.open_PNML)
        self.open_btn.grid(row = 0, column = 1)
        
        self.save_btn = Tkinter.Button(self.buttons_frame, text = 'Save PNML file', command = self.save_PNML)
        self.save_btn.grid(row = 0, column = 2)
        
        self.status_bar = Tkinter.Frame(self.root, height = 20)
        self.status_bar.grid(row = 2, column = 0, sticky = Tkinter.E+Tkinter.W)
        
        self.cursor_var = Tkinter.StringVar()
        self.status_label = Tkinter.Label(self.status_bar, textvariable = self.cursor_var)
        self.status_label.grid(row = 0, column = 0, sticky = Tkinter.W)
        
        self.action_label = Tkinter.Label(self.status_bar, textvariable = self.pne.status_var)
        self.action_label.grid(row = 0, column = 1, sticky = Tkinter.W)
        
    
    def cursor_callback(self, event):
        self.cursor_var.set('(' + str(event.x) + ', ' + str(event.y) + ')')
    
    def btnCallback(self):
        self.pn = self.pne.petri_net
        self.pne.set_petri_net(self.pn)
    
    def open_PNML(self):
        filename = tkFileDialog.askopenfilename(
                                              defaultextension = '.pnml',
                                              filetypes=[('PNML file', '*.pnml'), ('PNML file', '*.pnml.xml')],
                                              title = 'Open PNML file...',
                                              initialdir = '~/Desktop'
                                              )
        if not filename:
            return
        try:
            petri_nets = PetriNet.from_pnml_file(filename)
        except Exception as e:
            tkMessageBox.showerror('Error reading PNML file.', 'An error occurred while reading the PNML file.\n\n' + str(e))
            return
        
        if len(petri_nets) > 1:
            print 'More than 1 petri net loaded.'
        
        try:
            self.pne.set_petri_net(petri_nets[0])
        except Exception as e:
            tkMessageBox.showerror('Error loading PetriNet.', 'An error occurred while loading the PetriNet object.\n\n' + str(e))
    
    def save_PNML(self):
        filename = tkFileDialog.asksaveasfilename(
                                                  defaultextension = '.pnml',
                                                  filetypes=[('PNML file', '*.pnml'), ('PNML file', '*.pnml.xml')],
                                                  title = 'Save as PNML file...',
                                                  initialdir = '~/Desktop'
                                                  )
        if not filename:
            return
        
        try:
            self.pne.petri_net.to_pnml_file(filename)
        except Exception as e:
            tkMessageBox.showerror('Error saving PNML file.', 'An error occurred while saving the PNML file.\n\n' + str(e))
    
if __name__ == '__main__':
    w = testWindow()
    
    Tkinter.mainloop()
