# -*- coding: utf-8 -*-
"""
@author: Adrián Revuelta Cuauhtli
"""
'''
Based on a demo found at: 
http://svn.python.org/projects/python/branches/pep-0384/Demo/tk/ttk/notebook_closebtn.py
'''

import os
import Tkinter as tk
import ttk

class TabManager(ttk.Notebook):

    def __init__(self, parent, *args, **kwargs):
        
        _img_dir = kwargs.pop('img_dir', os.path.join(os.path.dirname(__file__), 'img'))
        _img_close_path = kwargs.pop('img_close', os.path.join(_img_dir, 'close.gif'))
        _img_active_path = kwargs.pop('img_active', os.path.join(_img_dir, 'close_active.gif'))
        _img_pressed_path = kwargs.pop('img_pressed', os.path.join(_img_dir, 'close_pressed.gif'))
        
        ttk.Notebook.__init__(self, parent, *args, **kwargs)
        
        self._img_close = tk.PhotoImage("img_close", file = _img_close_path)
        self._img_active = tk.PhotoImage("img_closeactive",
                           file = _img_active_path)
        self._img_pressed = tk.PhotoImage("img_closepressed",
                           file = _img_pressed_path)
        
        self.widget_dict = {}

        style = ttk.Style()

        style.element_create("close", "image", "img_close",
            ("active", "pressed", "!disabled", "img_closepressed"),
            ("active", "!disabled", "img_closeactive"), border = 8, sticky='')

        style.layout("TabManager.TNotebook", [("ButtonNotebook.client", {"sticky": "nswe"})])
        style.layout("TabManager.TNotebook.Tab", [
            ("TabManager.TNotebook.tab", {"sticky": "nswe", "children":
                [("TabManager.TNotebook.padding", {"side": "top", "sticky": "nswe",
                                             "children":
                    [("TabManager.TNotebook.focus", {"side": "top", "sticky": "nswe",
                                               "children":
                        [("TabManager.TNotebook.label", {"side": "left", "sticky": ''}),
                         ("TabManager.TNotebook.padding", {"side": "left", "sticky": ''}),
                         ("TabManager.TNotebook.close", {"side": "right", "sticky": 'e'})]
                    })]
                })]
            })]
        )
        
        self.config(style = "TabManager.TNotebook")
        
        self.bind_class("TNotebook", "<ButtonPress-1>", self.btn_press, True)
        self.bind_class("TNotebook", "<ButtonRelease-1>", self.btn_release)
        
        self.pressed_index = None

    def btn_press(self, event):
        x, y = event.x, event.y
        elem = self.identify(x, y)
        index = self.index("@%d,%d" % (x, y))
    
        if "close" in elem:
            self.state(['pressed'])
            self.pressed_index = index

    def btn_release(self, event):
        x, y = event.x, event.y
    
        if not self.instate(['pressed']):
            return
    
        elem =  self.identify(x, y)
        index = self.index("@%d,%d" % (x, y))
    
        if "close" in elem and self.pressed_index == index:
            del self.widget_dict[self.tabs()[index]]
            self.forget(index)
            self.event_generate("<<NotebookClosedTab>>")
    
        self.state(["!pressed"])
        self.pressed_index = None
    
    def add(self, widget, **kwargs):
        
        ttk.Notebook.add(self, widget, **kwargs)
        self.select(widget)
        self.widget_dict[self.select()] = widget

if __name__ == '__main__':
    root = tk.Tk()
    
    nb = TabManager(root)
    f1 = tk.Frame(nb, background="red")
    f2 = tk.Frame(nb, background="green")
    f3 = tk.Frame(nb, background="blue")
    nb.add(f1, text='Red', padding=3)
    nb.add(f2, text='Green', padding=3)
    nb.add(f3, text='Blue', padding=3)
    nb.pack(expand=1, fill='both')
    
    root.mainloop()
