# -*- coding: utf-8 -*-
"""
@author: Adrián Revuelta Cuauhtli
"""
import re
import Tkinter as tk
import ttk
import tkMessageBox

_INT_REGEX = re.compile('^(-[1-9])?[0-9]+$')
_POSITIVE_INT_REGEX = re.compile('^[1-9][0-9]*$')
_NON_NEGATIVE_INT_REGEX = re.compile('[0-9]+$')

_FLOAT_REGEX = re.compile('^-?[0-9]+(\.[0-9]+)?$')
_POSITIVE_FLOAT_REGEX = re.compile('^[0-9]+(\.[0-9]+)?$')

class InputDialog(object):
    
    def __init__(self, title, text, label, regex = re.compile('^[a-zA-Z0-9_-][a-zA-Z0-9_ -]*$'), value = '', error_message = 'Please input a non-empty string, preferably composed of only alphanumeric characters, dashes, underscores, and possibly spaces.', entry_length = 10):
        super(InputDialog, self).__init__()
        
        self.value_set = False
        self.regex = regex
        self.error_message = error_message
        
        self.window = tk.Toplevel()#takefocus = True)
        self.window.title(title)
        
        self.window.bind('<KeyPress-Escape>', self.cancel_callback)
        self.window.bind('<KeyPress-Return>', self.ok_callback)
        
        self.text = tk.Label(self.window, text = text)
        self.text.grid(row = 0, column = 0, sticky = tk.NW)
        
        self.input_frame = tk.Frame(self.window, pady = 10)
        self.input_frame.grid(row = 1, column = 0, sticky = tk.E+tk.W)
        
        self.input_var = tk.StringVar()
        self.input_label = tk.Label(self.input_frame, text = label + ': ')
        self.input_entry = tk.Entry(self.input_frame, width = entry_length, textvariable = self.input_var)
        self.input_var.set(value)
        self.input_entry.selection_range(0, tk.END)
        self.input_entry.focus_set()
        
        
        self.input_label.grid(row = 0, column = 0)
        self.input_entry.grid(row = 0, column = 1)
        
        self.button_frame = tk.Frame(self.window)
        self.button_frame.grid(row = 2, column = 0, sticky = tk.N)
        
        self.cancel_button = tk.Button(self.button_frame, text = 'Cancel', command = self.cancel_callback)
        self.ok_button = tk.Button(self.button_frame, text = 'Ok', command = self.ok_callback)
        
        self.cancel_button.grid(row = 0, column = 0)
        self.ok_button.grid(row = 0, column = 1)
        
        self.window.grab_set()
        self.window.focus_set()
        
    def cancel_callback(self, event = None):
        self.window.destroy()
    
    def ok_callback(self, event = None):
        if not self.regex.match(self.input_var.get()):
            tkMessageBox.showerror('Invalid entry', self.error_message)
            return
        self.value_set = True
        self.window.destroy()
    
def IntDialog(title, text, label, init_value = 0):
    return InputDialog(title, text, label, _INT_REGEX, str(init_value), 'Please enter a valid integer.')

def PositiveIntDialog(title, text, label, init_value = 1):
    return InputDialog(title, text, label, _POSITIVE_INT_REGEX, str(init_value), 'Please enter a positive integer (greater than zero).')

def NonNegativeIntDialog(title, text, label, init_value = 0):
    return InputDialog(title, text, label, _NON_NEGATIVE_INT_REGEX, str(init_value), 'Please enter a non-negative integer.')

def FloatDialog(title, text, label, init_value = 0.0):
    return InputDialog(title, text, label, _FLOAT_REGEX, str(init_value), 'Please enter a valid decimal number.')

def NonNegativeFloatDialog(title, text, label, init_value = 0.0):
    return InputDialog(title, text, label, _POSITIVE_FLOAT_REGEX, str(init_value), 'Please enter a valid positive decimal number.')

class MoveDialog(object):
    
    def __init__(self, src_tree, item, root):
        
        self.destination = None
        
        self.window = tk.Toplevel()
        self.window.title('Select target...')
        
        self.tree = ttk.Treeview(self.window, height = 10, selectmode = 'browse')
        self.tree.column('#0', minwidth = src_tree.column('#0', 'minwidth'), stretch = True)
        self.tree.heading('#0', text='Move element to...', anchor=tk.W)
        self.tree.grid(row = 0, column = 0, sticky = tk.NSEW)
        
        ysb = ttk.Scrollbar(self.window, orient='vertical', command=self.tree.yview)
        xsb = ttk.Scrollbar(self.window, orient='horizontal', command=self.tree.xview)
        self.tree.configure(xscroll = xsb.set, yscroll = ysb.set)
        ysb.grid(row = 0, column = 1, sticky = tk.NS)
        xsb.grid(row = 1, column = 0, sticky = tk.EW)
        
        elements_queue = [root]
        while elements_queue:
            current = elements_queue.pop(0)
            element_tags = src_tree.item(current, 'tags')
            if 'folder' not in element_tags or current == item:
                continue
            elements_queue += src_tree.get_children(current)
            self.tree.insert(src_tree.parent(current),
                        'end',
                        current,
                        text = src_tree.item(current, 'text'),
                        tags = element_tags,
                        open = True)
        
        self.tree.tag_bind('folder', '<Double-1>', self.ok_callback)
        
        button_frame = tk.Frame(self.window)
        button_frame.grid(row = 2, column = 0, sticky = tk.N)
        
        self.window.bind('<KeyPress-Escape>', self.cancel_callback)
        self.window.bind('<KeyPress-Return>', self.ok_callback)
        
        cancel_button = tk.Button(button_frame, text = 'Cancel', command = self.cancel_callback)
        ok_button = tk.Button(button_frame, text = 'Ok', command = self.ok_callback)
        
        cancel_button.grid(row = 0, column = 0)
        ok_button.grid(row = 0, column = 1)
        
        self.window.grab_set()
        self.window.focus_set()
        
    def cancel_callback(self, event = None):
            self.window.destroy()
        
    def ok_callback(self, event = None):
        if not self.tree.selection():
            tkMessageBox.showwarning('No option selected.', 'Please select a new destination before pressing ok.')
            return
        
        self.destination = self.tree.selection()[0]
        self.window.destroy()

if __name__ == '__main__':
    w = PositiveIntDialog('test', 'test text', 'test value', 1)
    tk.mainloop()
