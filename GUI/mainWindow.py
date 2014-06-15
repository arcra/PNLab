# -*- coding: utf-8 -*-
'''
@author: Adrián Revuelta Cuauhtli
'''

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import Tkinter as tk
import ttk

from PNEditorWidget import PNEditor

class PNLab(object):
    
    WORKSPACE_WIDTH = 600
    WORKSPACE_HEIGHT = 600
    
    EXPLORER_WIDTH = 250
    
    def __init__(self):
        super(PNLab, self).__init__()
        
        self.root = tk.Tk()
        self.root.wm_title('PetriNet Lab')
        #Necessary in order for the children to expand to the real size of the window id resized:
        self.root.rowconfigure(0, weight = 1)
        self.root.columnconfigure(2, weight = 1)
        
        
        ###############
        # SEPARATOR (FIXED WIDTH)
        ###############
        self.project_frame = tk.Frame(self.root, width = PNLab.EXPLORER_WIDTH)
        self.project_frame.grid(row = 0, column = 0, sticky = tk.NS)
        sep = ttk.Separator(self.root, orient = tk.VERTICAL)
        sep.grid(row = 0, column = 1, sticky = tk.NS)
        self.workspace_frame = tk.Frame(self.root, width = PNLab.WORKSPACE_WIDTH, height = PNLab.WORKSPACE_HEIGHT)
        self.workspace_frame.grid(row = 0, column = 2, sticky = tk.NSEW)
        #Necessary in order for the children to expand to the real size of the window id resized:
        self.workspace_frame.rowconfigure(0, weight = 1)
        self.workspace_frame.columnconfigure(0, weight = 1)
        
        '''
        ###############
        # PANED WINDOW (RESIZABLE)
        ###############
        self.paned_window = ttk.Panedwindow(self.root, orient = tk.HORIZONTAL)
        self.paned_window.grid(row = 0, column = 0, sticky = tk.NSEW)
        
        self.project_frame = tk.Frame(self.paned_window, width = 250)
        self.workspace_frame = tk.Frame(self.paned_window, width = 600, height = 600)
        
        self.paned_window.add(self.project_frame)
        self.paned_window.add(self.workspace_frame)
        '''
        
        self.project_tree = ttk.Treeview(self.project_frame)#, height = 29)
        self.project_tree.column('#0', minwidth = 30, stretch = True)
        ysb = ttk.Scrollbar(self.project_frame, orient='vertical', command=self.project_tree.yview)
        xsb = ttk.Scrollbar(self.project_frame, orient='horizontal', command=self.project_tree.xview)
        self.project_tree.configure(yscroll=ysb.set, xscroll=xsb.set)
        self.project_tree.heading('#0', text='Project Explorer', anchor=tk.W)
        
        self.project_tree.grid(row = 0, column = 0, sticky = tk.NSEW)
        ysb.grid(row = 0, column = 1, sticky = tk.NS)
        xsb.grid(row = 1, column = 0, sticky = tk.EW)
        
        
        self.notebook = ttk.Notebook(self.workspace_frame,
                                     width = PNLab.WORKSPACE_WIDTH,
                                     height = PNLab.WORKSPACE_HEIGHT)
        
        pne1 = PNEditor(self.workspace_frame,
                            name = 'empty',
                            width = PNLab.WORKSPACE_WIDTH,
                            height = PNLab.WORKSPACE_HEIGHT)
        pne2 = PNEditor(self.workspace_frame,
                            name = 'test',
                            width = PNLab.WORKSPACE_WIDTH,
                            height = PNLab.WORKSPACE_HEIGHT)
        self.notebook.add(pne1, text = pne1.petri_net.name)
        self.notebook.add(pne2, text = pne2.petri_net.name)
        self.notebook.grid(row = 0, column = 0, sticky = tk.NSEW)
        

if __name__ == '__main__':
    w = PNLab()
    
    tk.mainloop()