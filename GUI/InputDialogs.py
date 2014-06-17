# -*- coding: utf-8 -*-
"""
@author: Adrián Revuelta Cuauhtli
"""
import re
import Tkinter as tk
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

if __name__ == '__main__':
    w = PositiveIntDialog('test', 'test text', 'test value', 1)
    tk.mainloop()
