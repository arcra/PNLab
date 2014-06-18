# -*- coding: utf-8 -*-
'''
@author: Adrián Revuelta Cuauhtli
'''

import sys
import os
from PetriNets import PetriNet
import tkMessageBox
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import Tkinter as tk
import ttk
import tkFileDialog
import tkFont

from TabManager import TabManager
from PNEditorWidget import PNEditor
from AuxDialogs import InputDialog, MoveDialog

class PNLab(object):
    
    WORKSPACE_WIDTH = 600
    WORKSPACE_HEIGHT = 600
    
    EXPLORER_WIDTH = 250
    
    def __init__(self):
        super(PNLab, self).__init__()
        
        self.root = tk.Tk()
        self.root.wm_title('PetriNet Lab')
        #Necessary in order for the children to expand to the real size of the window if resized:
        self.root.rowconfigure(0, weight = 1)
        self.root.columnconfigure(2, weight = 1)
        
        self.project_frame = tk.Frame(self.root, width = PNLab.EXPLORER_WIDTH)
        self.project_frame.grid(row = 0, column = 0, sticky = tk.NSEW)
        self.project_frame.rowconfigure(0, weight = 1)
        
        sep = ttk.Separator(self.root, orient = tk.VERTICAL)
        sep.grid(row = 0, column = 1, sticky = tk.NS)
        
        self.workspace_frame = tk.Frame(self.root, width = PNLab.WORKSPACE_WIDTH, height = PNLab.WORKSPACE_HEIGHT)
        self.workspace_frame.grid(row = 0, column = 2, sticky = tk.NSEW)
        #Necessary in order for the children to expand to the real size of the window if resized:
        self.workspace_frame.rowconfigure(0, weight = 1)
        self.workspace_frame.columnconfigure(0, weight = 1)
        
        self.project_tree = ttk.Treeview(self.project_frame, height = int((PNLab.WORKSPACE_HEIGHT - 20)/20), selectmode = 'browse')
        self.project_tree.heading('#0', text='Project Explorer', anchor=tk.W)
        self.project_tree.grid(row = 0, column = 0, sticky = tk.NSEW)
        
        #ysb = ttk.Scrollbar(self.project_frame, orient='vertical', command=self.project_tree.yview)
        xsb = ttk.Scrollbar(self.project_frame, orient='horizontal', command=self.project_tree.xview)
        self.project_tree.configure(xscroll = xsb.set)#, yscroll = ysb.set)
        #ysb.grid(row = 0, column = 1, sticky = tk.NS)
        xsb.grid(row = 1, column = 0, sticky = tk.EW)
        
        self.folder_img = tk.PhotoImage('folder_img', file = os.path.join(os.path.dirname(__file__), 'img', 'TreeView_Folder.gif'))
        self.task_img = tk.PhotoImage('task_img', file = os.path.join(os.path.dirname(__file__), 'img', 'doc.gif'))
        self.project_tree.tag_configure('folder', image = self.folder_img)
        self.project_tree.tag_configure('task', image = self.task_img)
        self.project_tree.insert('', 'end', 'Tasks/', text = 'Tasks/', tags = ['folder'], open = True)
        
        self.tab_manager = TabManager(self.workspace_frame,
                                     width = PNLab.WORKSPACE_WIDTH,
                                     height = PNLab.WORKSPACE_HEIGHT)
        self.tab_manager.grid(row = 0, column = 0, sticky = tk.NSEW)
        
        
        self.popped_up_menu = None
        self.petri_nets = {}
        
        self.folder_menu = tk.Menu(self.root, tearoff = 0)
        self.folder_menu.add_command(label = 'Add Task', command = self.create_task)
        self.folder_menu.add_command(label = 'Add Folder', command = self.create_folder)
        self.folder_menu.add_command(label = 'Import from PNML', command = self.import_from_PNML)
        self.folder_menu.add_command(label = 'Rename', command = self.rename_folder)
        self.folder_menu.add_command(label = 'Move', command = self.move_folder)
        self.folder_menu.add_command(label = 'Delete', command = self.delete_folder)
        
        self.task_menu = tk.Menu(self.root, tearoff = 0)
        self.task_menu.add_command(label = 'Open', command = self.open_petri_net)
        self.task_menu.add_command(label = 'Rename', command = self.rename_task)
        self.task_menu.add_command(label = 'Move', command = self.move_task)
        self.task_menu.add_command(label = 'Delete', command = self.delete_task)
        self.task_menu.add_command(label = 'Export to PNML', command = self.export_to_PNML)
        
        #MAC OS:
        if (self.root.tk.call('tk', 'windowingsystem')=='aqua'):
            self.project_tree.tag_bind('folder', '<2>', self.popup_folder_menu)
            self.project_tree.tag_bind('folder', '<Control-1>', self.popup_folder_menu)
        #Windows / UNIX / Linux:
        else:
            self.project_tree.tag_bind('folder', '<3>', self.popup_folder_menu)
            
        #MAC OS:
        if (self.root.tk.call('tk', 'windowingsystem')=='aqua'):
            self.project_tree.tag_bind('task', '<2>', self.popup_task_menu)
            self.project_tree.tag_bind('task', '<Control-1>', self.popup_task_menu)
        #Windows / UNIX / Linux:
        else:
            self.project_tree.tag_bind('task', '<3>', self.popup_task_menu)
        
        
        self.project_tree.tag_bind('task', '<Double-1>', self.open_callback)
        self.root.bind('<Button-1>', self._hide_menu)
    
    def popup_folder_menu(self, event):
        self.clicked_element = self.project_tree.identify('item', event.x, event.y)
        if self.clicked_element == 'Tasks/':
            self.folder_menu.entryconfigure(3, state = 'disabled')
            self.folder_menu.entryconfigure(4, state = 'disabled')
            self.folder_menu.entryconfigure(5, state = 'disabled')
        else:
            self.folder_menu.entryconfigure(3, state = 'normal')
            self.folder_menu.entryconfigure(4, state = 'normal')
            self.folder_menu.entryconfigure(5, state = 'normal')
        
        self.popped_up_menu = self.folder_menu
        self.folder_menu.post(event.x_root, event.y_root)
    
    def popup_task_menu(self, event):
        self.clicked_element = self.project_tree.identify('item', event.x, event.y)
        self.popped_up_menu = self.task_menu
        self.task_menu.post(event.x_root, event.y_root)
    
    def _hide_menu(self, event):
        """Hides a popped-up menu."""
        if self.popped_up_menu:
            self.popped_up_menu.unpost()
            self.popped_up_menu = None
            return True
        return False
    
    def _adjust_width(self, text, item_id):
        
        font = tkFont.Font()
        measure = font.measure(text) + self._find_depth(item_id)*20
        current_width = self.project_tree.column('#0', 'minwidth')
        if measure > current_width:
            self.project_tree.column('#0', minwidth = measure, stretch = True)
            
    def _find_depth(self, item):
        
        count = 1
        while item != 'Tasks/':
            item = self.project_tree.parent(item)
            count += 1
        return count
    
    def create_folder(self):
        dialog = InputDialog(
                             'Folder name',
                             'Please input a folder name, preferably composed only of alphabetic characters.',
                             'Name',
                             entry_length = 25)
        dialog.window.transient(self.root)
        self.root.wait_window(dialog.window)
        if not dialog.value_set:
            return
        name = dialog.input_var.get()
        item_id = self.clicked_element + name.replace(' ', '_') + '/'
        self.project_tree.insert(self.clicked_element, 'end', item_id, text = name + '/', tags = ['folder'], open = True)
        self._adjust_width(name + '/', item_id)
    
    def create_task(self):
        dialog = InputDialog('Task name',
                             'Please input a task name, preferably composed only of alphabetic characters.',
                             'Name',
                             entry_length = 25)
        dialog.window.transient(self.root)
        self.root.wait_window(dialog.window)
        if not dialog.value_set:
            return
        name = dialog.input_var.get()
        item_id = self.clicked_element + name.replace(' ', '_')
        
        try:
            self.project_tree.insert(self.clicked_element, 'end', item_id, text = name, tags = ['task'])
            self._adjust_width(name, item_id)
        except Exception as e:
            tkMessageBox.showerror('ERROR', 'Task could not be inserted in the selected node, possible duplicate name.\n\n' + str(e))
            return
        
        pne = PNEditor(self.tab_manager, name = name)
        self.petri_nets[item_id] = pne
        self.tab_manager.add(pne, text = pne.name)
        self.tab_manager.select(pne)
    
    def open_callback(self, event):
        self.clicked_element = self.project_tree.identify('item', event.x, event.y)
        self.open_petri_net()
    
    def open_petri_net(self):
        pne = self.petri_nets[self.clicked_element]
        try:
            self.tab_manager.add(pne, text = pne.name)
        except:
            pass
        
        self.tab_manager.select(pne)
    
    def import_from_PNML(self):
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
            print 'warning: More than 1 petri net read, only 1 loaded.'
        
        try:
            pn = petri_nets[0]
        except Exception as e:
            tkMessageBox.showerror('Error loading PetriNet.', 'An error occurred while loading the PetriNet object.\n\n' + str(e))
        
        name = pn.name
        item_id = self.clicked_element + name.replace(' ', '_')
        
        try:
            self.project_tree.insert(self.clicked_element, 'end', item_id, text = name, tags = ['task'])
            self._adjust_width(name, item_id)
        except Exception as e:
            tkMessageBox.showerror('ERROR', 'Task could not be inserted in the selected node, possible duplicate name.\n\n' + str(e))
            return
        pne = PNEditor(self.tab_manager, PetriNet = pn)
        self.petri_nets[item_id] = pne
        self.tab_manager.add(pne, text = pne.name)
        self.tab_manager.select(pne)
    
    def rename_folder(self):
        old_name = self.project_tree.item(self.clicked_element, 'text')
        dialog = InputDialog('Folder name',
                             'Please input a folder name, preferably composed only of alphabetic characters.',
                             'Name',
                             value = old_name,
                             entry_length = 25)
        dialog.window.transient(self.root)
        self.root.wait_window(dialog.window)
        if not dialog.value_set:
            return
        name = dialog.input_var.get()
        parent = self.project_tree.parent(self.clicked_element)
        
        self._move_folder(self.clicked_element, parent, parent, old_name, name)
    
    def move_folder(self):
        
        destination = self._get_destination(self.clicked_element)
        name = self.project_tree.item(self.clicked_element, 'text')
        old_parent = self.project_tree.parent(self.clicked_element)
        if destination:
            self._move_folder(self.clicked_element, old_parent, destination, name, name)
    
    def rename_task(self):
        old_name = self.project_tree.item(self.clicked_element, 'text')
        dialog = InputDialog('Task name',
                             'Please input a task name, preferably composed only of alphabetic characters.',
                             'Name',
                             value = old_name,
                             entry_length = 25)
        dialog.window.transient(self.root)
        self.root.wait_window(dialog.window)
        if not dialog.value_set:
            return
        name = dialog.input_var.get()
        parent = self.project_tree.parent(self.clicked_element)
        
        self._move_task(self.clicked_element, parent, parent, old_name, name)
    
    def move_task(self):
        
        destination = self._get_destination(self.clicked_element)
        name = self.project_tree.item(self.clicked_element, 'text')
        old_parent = self.project_tree.parent(self.clicked_element)
        if destination:
            self._move_task(self.clicked_element, old_parent, destination, name, name)
    
    def _get_destination(self, item):
        
        dialog = MoveDialog(self.project_tree, item, 'Tasks/')
        
        dialog.window.transient(self.root)
        self.root.wait_window(dialog.window)
        
        return dialog.destination
    
    def _move_folder(self, old_id, old_parent, parent, old_name, name):
        item_id = parent + name.replace(' ', '_')
        if item_id == old_id:
            return
        try:
            self.project_tree.insert(parent, 'end', item_id, text = name, tags = ['folder'], open = True)
            self._adjust_width(name, item_id)
        except Exception as e:
            tkMessageBox.showerror('ERROR', 'Item could not be inserted in the selected node, possible duplicate name.\n\nERROR: ' + str(e))
            return
        
        children_queue = list(self.project_tree.get_children(old_id))
        while children_queue:
            current = children_queue.pop(0)
            item_tags = self.project_tree.item(current, 'tags')
            current_name = self.project_tree.item(current, 'text')
            if 'folder' in item_tags:
                self._move_folder(current, old_id, item_id, current_name, current_name)
            else:
                self._move_task(current, old_id, item_id, current_name, current_name)
        
        self.project_tree.delete(old_id)
    
    def _move_task(self, old_id, old_parent, parent, old_name, name):
        item_id = parent + name.replace(' ', '_')
        pne = self.petri_nets.pop(old_id)
        try:
            self.project_tree.insert(parent, 'end', item_id, text = name, tags = ['task'])
            self.project_tree.delete(old_id)
            self._adjust_width(name, item_id)
            pne.name = name
            self.petri_nets[item_id] = pne
        except Exception as e:
            tkMessageBox.showerror('ERROR', 'Item could not be inserted in the selected node, possible duplicate name.\n\nERROR: ' + str(e))
            try:
                self.project_tree.insert(old_parent, 'end', old_id, text = old_name, tags = ['task'])
            except:
                pass
            self.petri_nets[old_id] = pne
            return
        
        try:
            self.tab_manager.tab(pne, text = pne.name)
        except:
            pass
    
    def delete_task(self, item = None):
        if not item:
            item = self.clicked_element
        pne = self.petri_nets.pop(item, None)
        try:
            self.tab_manager.forget(pne)
        except:
            pass
        self.project_tree.delete(item)
    
    def delete_folder(self, item = None):
        
        if not item:
            item = self.clicked_element
        
        if item == 'Tasks/':
            return
            
        children_queue = list(self.project_tree.get_children(item))
        
        while children_queue:
            current = children_queue.pop(0)
            item_tags = self.project_tree.item(current, 'tags')
            if 'folder' in item_tags:
                self.delete_folder(current)
            else:
                self.delete_task(current)
        
        self.project_tree.delete(item)
    
    def export_to_PNML(self):
        filename = tkFileDialog.asksaveasfilename(
                                                  defaultextension = '.pnml',
                                                  filetypes=[('PNML file', '*.pnml'), ('PNML file', '*.pnml.xml')],
                                                  title = 'Save as PNML file...',
                                                  initialdir = '~/Desktop'
                                                  )
        if not filename:
            return
        
        try:
            self.petri_nets[self.clicked_element].petri_net.to_pnml_file(filename)
        except Exception as e:
            tkMessageBox.showerror('Error saving PNML file.', 'An error occurred while saving the PNML file.\n\n' + str(e))

if __name__ == '__main__':
    w = PNLab()
    
    tk.mainloop()