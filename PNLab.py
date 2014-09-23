# -*- coding: utf-8 -*-
'''
@author: Adrián Revuelta Cuauhtli
'''

import sys
import os
import tkMessageBox
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import Tkinter as tk
import ttk
import tkFileDialog
import tkFont

import zipfile
import tempfile

from lxml import etree as ET
from subprocess import call

from PetriNets import PetriNet, PlaceTypes
from GUI.TabManager import TabManager
from GUI.PNEditor import PNEditor
from GUI.AuxDialogs import InputDialog, MoveDialog, SelectItemDialog
from PNLab2PIPE import pnlab2pipe
from PIPE2PNLab import pipe2pnlab

class PNLab(object):
    
    WORKSPACE_WIDTH = 600
    WORKSPACE_HEIGHT = 600
    
    EXPLORER_WIDTH = 250
    
    def __init__(self):
        super(PNLab, self).__init__()
        
        self.root = tk.Tk()
        self.root.wm_title('PNLab')
        self.root.protocol("WM_DELETE_WINDOW", self.exit)
        #Necessary in order for the children to expand to the real size of the window if resized:
        self.root.rowconfigure(1, weight = 1)
        self.root.columnconfigure(2, weight = 1)
        
        toolbar_frame = tk.Frame(self.root)
        toolbar_frame.grid(row = 0, column = 2, sticky = tk.E)
        
        mode_label = tk.Label(toolbar_frame, text = 'mode: ')
        mode_label.grid(row = 0, column = 0, sticky = tk.E)
        
        self.mode_var = tk.StringVar()
        mode_combo = ttk.Combobox(toolbar_frame,
                                  values = ['Editor', 'Simulation', 'Execution'],
                                  textvariable = self.mode_var,
                                  state = 'readonly')
        self.mode_var.set('Editor')
        mode_combo.grid(row = 0, column = 1, sticky = tk.E)
        
        project_frame = tk.Frame(self.root, width = PNLab.EXPLORER_WIDTH)
        project_frame.grid(row = 1, column = 0, sticky = tk.NSEW)
        project_frame.rowconfigure(0, weight = 1)
        
        sep = ttk.Separator(self.root, orient = tk.VERTICAL)
        sep.grid(row = 1, column = 1, sticky = tk.NS)
        
        workspace_frame = tk.Frame(self.root, width = PNLab.WORKSPACE_WIDTH, height = PNLab.WORKSPACE_HEIGHT)
        workspace_frame.grid(row = 1, column = 2, sticky = tk.NSEW)
        #Necessary in order for the children to expand to the real size of the window if resized:
        workspace_frame.rowconfigure(0, weight = 1)
        workspace_frame.columnconfigure(0, weight = 1)
        
        self.status_bar = tk.Frame(self.root, height = 20)
        self.status_bar.grid(row = 2, columnspan=3, sticky = tk.EW)
        
        self.status_var = tk.StringVar()
        self.status_var.set('Ready.')
        
        self.status_label = tk.Label(self.status_bar, textvariable = self.status_var)
        self.status_label.grid(row = 0, column = 0, sticky = tk.EW)
        
        self.project_tree = ttk.Treeview(project_frame, height = int((PNLab.WORKSPACE_HEIGHT - 20)/20), selectmode = 'browse')
        self.project_tree.heading('#0', text='Project Explorer', anchor=tk.W)
        self.project_tree.grid(row = 0, column = 0, sticky = tk.NSEW)
        
        #ysb = ttk.Scrollbar(project_frame, orient='vertical', command=self.project_tree.yview)
        xsb = ttk.Scrollbar(project_frame, orient='horizontal', command=self.project_tree.xview)
        self.project_tree.configure(xscroll = xsb.set)#, yscroll = ysb.set)
        #ysb.grid(row = 0, column = 1, sticky = tk.NS)
        xsb.grid(row = 1, column = 0, sticky = tk.EW)
        
        self.folder_img = tk.PhotoImage('folder_img', file = os.path.join(os.path.dirname(__file__), 'GUI', 'img', 'TreeView_Folder.gif'))
        self.petri_net_img = tk.PhotoImage('petri_net_img', file = os.path.join(os.path.dirname(__file__), 'GUI', 'img', 'doc.gif'))
        self.project_tree.tag_configure('folder', image = self.folder_img)
        self.project_tree.tag_configure('petri_net', image = self.petri_net_img)
        self.project_tree.insert('', 'end', 'Actions/', text = 'Actions/', tags = ['folder'], open = True)
        self.project_tree.insert('', 'end', 'CommActions/', text = 'CommActions/', tags = ['folder'], open = True)
        self.project_tree.insert('', 'end', 'Tasks/', text = 'Tasks/', tags = ['folder'], open = True)
        self.project_tree.insert('', 'end', 'Environment/', text = 'Environment/', tags = ['folder'], open = True)
        
        self.tab_manager = TabManager(workspace_frame,
                                     width = PNLab.WORKSPACE_WIDTH,
                                     height = PNLab.WORKSPACE_HEIGHT)
        self.tab_manager.grid(row = 0, column = 0, sticky = tk.NSEW)
        
        self.tab_manager.bind('<<NotebookTabChanged>>', self._set_string_var)
        
        menubar = tk.Menu(self.root)
        
        file_menu = tk.Menu(menubar, tearoff = False)
        file_menu.add_command(label = 'Open', command = self.open)
        file_menu.add_command(label="Save", command = self.save, accelerator = 'Ctrl+s')
        file_menu.add_command(label="Save As...", command = self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command = self.exit, accelerator = 'Ctrl+q', foreground = 'red', activeforeground = 'white', activebackground = 'red')
        
        menubar.add_cascade(label = 'File', menu = file_menu)
        
        analysis_menu = tk.Menu(menubar, tearoff = False)
        analysis_menu.add_command(label="Generate FullPetriNet", command = self.get_full_pn)
        analysis_menu.add_command(label = 'ComputeMC', command = self.computeMC)
        
        menubar.add_cascade(label = 'Analysis Tools', menu = analysis_menu)
        
        '''
        mode_menu = tk.Menu(menubar, tearoff = False)
        mode_menu.add_command(label = 'Editing Mode')
        mode_menu.add_command(label = 'Simulation Mode')
        mode_menu.add_command(label = 'Execution Mode')
        menubar.add_cascade(label = 'Set mode...', menu = mode_menu)
        '''
        
        self.root.config(menu = menubar)
        
        self.popped_up_menu = None
        self.petri_nets = {}
        self.file_path = None
        
        self.folder_menu = tk.Menu(self.root, tearoff = 0)
        self.folder_menu.add_command(label = 'Add Petri Net', command = self.create_petri_net)
        self.folder_menu.add_command(label = 'Import from Standard PNML', command = self.import_from_PNML)
        self.folder_menu.add_command(label = 'Import from PIPE PNML', command = self.import_from_PIPE)
        
        self.petri_net_menu = tk.Menu(self.root, tearoff = 0)
        self.petri_net_menu.add_command(label = 'Open', command = self.open_petri_net)
        self.petri_net_menu.add_command(label = 'Rename', command = self.rename_petri_net)
        self.petri_net_menu.add_command(label = 'Move', command = self.move_petri_net)
        self.petri_net_menu.add_command(label = 'Delete', command = self.delete_petri_net)
        self.petri_net_menu.add_command(label = 'Export to Standard PNML', command = self.export_to_PNML)
        self.petri_net_menu.add_command(label = 'Export to PIPE PNML', command = self.export_to_PIPE)
        
        #MAC OS:
        if (self.root.tk.call('tk', 'windowingsystem')=='aqua'):
            self.project_tree.tag_bind('folder', '<2>', self.popup_folder_menu)
            self.project_tree.tag_bind('folder', '<Control-1>', self.popup_folder_menu)
        #Windows / UNIX / Linux:
        else:
            self.project_tree.tag_bind('folder', '<3>', self.popup_folder_menu)
            
        #MAC OS:
        if (self.root.tk.call('tk', 'windowingsystem')=='aqua'):
            self.project_tree.tag_bind('petri_net', '<2>', self.popup_petri_net_menu)
            self.project_tree.tag_bind('petri_net', '<Control-1>', self.popup_petri_net_menu)
        #Windows / UNIX / Linux:
        else:
            self.project_tree.tag_bind('petri_net', '<3>', self.popup_petri_net_menu)
        
        
        self.project_tree.tag_bind('petri_net', '<Double-1>', self.open_callback)
        self.root.bind('<Button-1>', self._hide_menu)
        self.root.bind('<Control-s>', self.save)
        self.root.bind('<Control-q>', self.exit)
    
    
    #######################################################
    #        TREE WIDGET, PNs AND TABS INTERACTIONS
    #######################################################
    def _set_string_var(self, event):
        try:
            tab_id = self.tab_manager.select()
            if not tab_id:
                return
        except:
            return
        
        pne = self.tab_manager.widget_dict[tab_id]
        self.status_label.configure(textvariable = pne.status_var)
        pne.focus_set()
    
    def popup_folder_menu(self, event):
        self.clicked_element = self.project_tree.identify('item', event.x, event.y)
        self.popped_up_menu = self.folder_menu
        self.folder_menu.post(event.x_root, event.y_root)
    
    def popup_petri_net_menu(self, event):
        self.clicked_element = self.project_tree.identify('item', event.x, event.y)
        self.popped_up_menu = self.petri_net_menu
        self.petri_net_menu.post(event.x_root, event.y_root)
    
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
        
        count = 0
        while item != '':
            item = self.project_tree.parent(item)
            count += 1
        return count
    
    def _add_pne(self, pn, item_id, open_tab = True):
        if isinstance(pn, PetriNet):
            pne = PNEditor(self.tab_manager, PetriNet = pn)
        else:
            pne = PNEditor(self.tab_manager, name = pn)
        self.petri_nets[item_id] = pne
        if open_tab:
            self.tab_manager.add(pne, text = pne.name)
            self.tab_manager.select(pne)
        return pne
    
    def create_petri_net(self):
        dialog = InputDialog('Petri Net name',
                             'Please input a Petri Net name, preferably composed only of alphabetic characters.',
                             'Name',
                             entry_length = 25)
        dialog.window.transient(self.root)
        self.root.wait_window(dialog.window)
        if not dialog.value_set:
            return
        name = dialog.input_var.get()
        item_id = self.clicked_element + name
        
        try:
            self.project_tree.insert(self.clicked_element, 'end', item_id, text = name, tags = ['petri_net'])
            self._adjust_width(name, item_id)
        except Exception as e:
            tkMessageBox.showerror('ERROR', 'Petri Net could not be inserted in the selected node, possible duplicate name.\n\n' + str(e))
            return
        
        self._add_pne(name, item_id)
    
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
                                              filetypes=[('Standard PNML file', '*.pnml'), ('Standard PNML file', '*.pnml.xml')],
                                              title = 'Open Standard PNML file...',
                                              initialdir = os.path.expanduser('~/Desktop')
                                              )
        if not filename:
            return
        
        item_id = self._import_from_pnml(filename, self.clicked_element)
        pne = self.petri_nets[item_id]
        self.tab_manager.add(pne, text = pne.name)
        self.tab_manager.select(pne)
        
    def _import_from_pnml(self, filename, parent):
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
        item_id = parent + name
        
        try:
            self.project_tree.insert(parent, 'end', item_id, text = name, tags = ['petri_net'])
            self._adjust_width(name, item_id)
        except Exception as e:
            tkMessageBox.showerror('ERROR', 'Petri Net could not be inserted in the selected node, possible duplicate name.\n\n' + str(e))
            return
        
        pne = self._add_pne(pn, item_id, False)
        pne.edited = False
        return item_id
    
    def import_from_PIPE(self):
        filename = tkFileDialog.askopenfilename(
                                              defaultextension = '.pnml.xml',
                                              filetypes=[('PNML file', '*.pnml.xml'), ('PNML file', '*.pnml')],
                                              title = 'Open PIPE PNML file...',
                                              initialdir = os.path.expanduser('~/Desktop')
                                              )
        if not filename:
            return
        
        pn = None
        try:
            name = os.path.basename(filename)
            if name[-5:] == '.pnml':
                name = name[:-5]
            if name[-9:] == '.pnml.xml':
                name = name[:-9]
            et = pipe2pnlab.convert(filename)
            petri_nets = PetriNet.from_ElementTree(et, name)
        except Exception as e:
            tkMessageBox.showerror('Error reading PNML file.', 'An error occurred while reading the PNML file.\n\n' + str(e))
            return
        
        if len(petri_nets) > 1:
            print 'warning: More than 1 petri net read, only 1 loaded.'
        
        try:
            pn = petri_nets[0]
        except Exception as e:
            tkMessageBox.showerror('Error loading PetriNet.', 'An error occurred while loading the PetriNet object.\n\n' + str(e))
        
        parent = self.clicked_element
        item_id = parent + name
        
        try:
            self.project_tree.insert(parent, 'end', item_id, text = name, tags = ['petri_net'])
            self._adjust_width(name, item_id)
        except Exception as e:
            tkMessageBox.showerror('ERROR', 'Petri Net could not be inserted in the selected node, possible duplicate name.\n\n' + str(e))
            return
        
        pne = self._add_pne(pn, item_id, True)
        pne.edited = False
    
    def rename_petri_net(self):
        old_name = self.project_tree.item(self.clicked_element, 'text')
        dialog = InputDialog('Petri Net name',
                             'Please input a Petri Net name, preferably composed only of alphabetic characters.',
                             'Name',
                             value = old_name,
                             entry_length = 25)
        dialog.window.transient(self.root)
        self.root.wait_window(dialog.window)
        if not dialog.value_set:
            return
        name = dialog.input_var.get()
        parent = self.project_tree.parent(self.clicked_element)
        
        self._move_petri_net(self.clicked_element, parent, parent, old_name, name)
    
    def move_petri_net(self):
        
        destination = self._get_destination(self.clicked_element)
        name = self.project_tree.item(self.clicked_element, 'text')
        old_parent = self.project_tree.parent(self.clicked_element)
        if destination:
            self._move_petri_net(self.clicked_element, old_parent, destination, name, name)
    
    def _get_destination(self, item):
        
        dialog = MoveDialog(self.project_tree, item, '')
        
        dialog.window.transient(self.root)
        self.root.wait_window(dialog.window)
        
        return dialog.selection
    
    def _move_petri_net(self, old_id, old_parent, parent, old_name, name):
        item_id = parent + name
        pne = self.petri_nets.pop(old_id)
        try:
            self.project_tree.insert(parent, 'end', item_id, text = name, tags = ['petri_net'])
            self.project_tree.delete(old_id)
            self._adjust_width(name, item_id)
            pne.name = name
            self.petri_nets[item_id] = pne
        except Exception as e:
            tkMessageBox.showerror('ERROR', 'Item could not be inserted in the selected node, possible duplicate name.\n\nERROR: ' + str(e))
            try:
                self.project_tree.insert(old_parent, 'end', old_id, text = old_name, tags = ['petri_net'])
            except:
                pass
            self.petri_nets[old_id] = pne
            return
        
        try:
            self.tab_manager.tab(pne, text = pne.name)
        except:
            pass
    
    def delete_petri_net(self, item = None):
        if not item:
            item = self.clicked_element
        pne = self.petri_nets.pop(item, None)
        try:
            self.tab_manager.forget(pne)
        except:
            pass
        self.project_tree.delete(item)
    
    def export_to_PNML(self):
        filename = tkFileDialog.asksaveasfilename(
                                                  defaultextension = '.pnml',
                                                  filetypes=[('Standard PNML file', '*.pnml')],
                                                  title = 'Save as Standard PNML file...',
                                                  initialdir = os.path.dirname(self.file_path) if self.file_path is not None else os.path.expanduser('~/Desktop'),
                                                  initialfile = os.path.basename(self.clicked_element) + '.pnml'
                                                  )
        if not filename:
            return
        
        try:
            self.petri_nets[self.clicked_element].petri_net.to_pnml_file(filename)
        except Exception as e:
            tkMessageBox.showerror('Error saving PNML file.', 'An error occurred while saving the PNML file.\n\n' + str(e))
    
    def export_to_PIPE(self):
        filename = tkFileDialog.asksaveasfilename(
                                                  defaultextension = '.pnml.xml',
                                                  filetypes=[('PIPE PNML file', '*.pnml.xml')],
                                                  title = 'Save as PIPE PNML file...',
                                                  initialdir = os.path.dirname(self.file_path) if self.file_path is not None else os.path.expanduser('~/Desktop'),
                                                  initialfile = os.path.basename(self.clicked_element) + '.pnml.xml'
                                                  )
        if not filename:
            return
        
        try:
            et = self.petri_nets[self.clicked_element]._petri_net.to_ElementTree()
            et = pnlab2pipe.convert(et)
            et.write(filename, encoding = 'utf-8', xml_declaration = True, pretty_print = True)
        except Exception as e:
            tkMessageBox.showerror('Error saving PNML file.', 'An error occurred while saving the PNML file.\n\n' + str(e))
    
    
    #######################################################
    #                FILE MENU ACTIONS
    #######################################################
    def open(self):
        zip_filename = tkFileDialog.askopenfilename(
                                                  defaultextension = '.rpnp',
                                                  filetypes=[('Robotic Petri Net Plan file', '*.rpnp')],
                                                  title = 'Open RPNP file...',
                                                  initialdir = os.path.expanduser('~/Desktop')
                                                  )
        if not zip_filename:
            return
        
        items = self.project_tree.get_children('Actions/') \
        + self.project_tree.get_children('CommActions/') \
        + self.project_tree.get_children('Tasks/') \
        + self.project_tree.get_children('Environment/')
        
        for i in items:
            self.delete_petri_net(i)
        
        self.file_path = zip_filename
        
        zip_file = zipfile.ZipFile(self.file_path, 'r')
        tmp_dir = tempfile.mkdtemp()
        
        for x in zip_file.infolist():
            prev_sep = -1
            sep_index = x.filename.find('/', 0)
            while sep_index > -1:
                current_dir = x.filename[:sep_index + 1]
                parent = x.filename[:prev_sep + 1]
                if not self.project_tree.exists(current_dir):
                    name = current_dir[current_dir[:-1].rfind('/') + 1:]
                    self.project_tree.insert(parent, 'end', current_dir, text = name, tags = ['folder'], open = True)
                    self._adjust_width(name, current_dir)
                prev_sep = sep_index
                sep_index = x.filename.find('/', sep_index + 1)
            if x.filename[-5:] == '.pnml':
                last_sep = x.filename.rfind('/') + 1
                filename = x.filename[last_sep:]
                parent = x.filename[:last_sep]
                file_path = os.path.join(tmp_dir, filename)
                f = open(file_path, 'w')
                data = zip_file.read(x)
                f.write(data)
                f.close()
                self._import_from_pnml(file_path, parent)
                os.remove(file_path)
            
        os.rmdir(tmp_dir)
        zip_file.close()
        
        self.status_var.set('Opened: ' + self.file_path)
    
    def save(self, event = None):
        if not self.file_path:
            self.save_as()
            return
        
        try:
            zip_file = zipfile.ZipFile(self.file_path, "w")
        except:
            tkMessageBox.showerror('Error opening file.', 'A problem ocurred while opening a file for writing, make sure the file is not open by other program before saving.')
            return
        tmp_dir = tempfile.mkdtemp()
        
        folders = ('Actions/', 'CommActions/', 'Tasks/', 'Environment/')
        
        for f in folders:
            children = self.project_tree.get_children(f)
            if not children:
                file_path = os.path.join(tmp_dir, f)
                os.mkdir(file_path)
                zip_file.write(file_path, f)
                os.rmdir(file_path)
                continue
            for current in children:
                path = current + '.pnml'
                pne = self.petri_nets[current]
                file_name = os.path.basename(path)
                file_path = os.path.join(tmp_dir, file_name)
                pne._petri_net.to_pnml_file(file_path)
                zip_file.write(file_path, path)
                pne.edited = False
                os.remove(file_path)
        
        os.rmdir(tmp_dir)
        zip_file.close()
        
        try:
            tab_id = self.tab_manager.select()
            if not tab_id:
                raise Exception()
        except:
            self.status_label.configure(textvariable = self.status_var)
            self.status_var.set('File saved: ' + self.file_path)
            return
        
        pne = self.tab_manager.widget_dict[tab_id]
        pne.status_var.set('File saved: ' + self.file_path)
    
    def save_as(self):
        zip_filename = tkFileDialog.asksaveasfilename(
                                                  defaultextension = '.rpnp',
                                                  filetypes=[('Robotic Petri Net Plan file', '*.rpnp')],
                                                  title = 'Save as RPNP file...',
                                                  initialdir = os.path.dirname(self.file_path) if self.file_path is not None else os.path.expanduser('~/Desktop'),
                                                  initialfile = os.path.basename(self.file_path) if self.file_path is not None else ''
                                                  )
        if not zip_filename:
            return
        
        self.file_path = zip_filename
        
        self.save()
        
    
    def exit(self, event = None):
        
        edited = False
        for pne in self.petri_nets.itervalues():
            if pne.edited:
                edited = True
                break
        
        if edited:
            if not tkMessageBox.askokcancel('Exit without saving?', 'Are you sure you want to quit without saving any changes?', default = tkMessageBox.CANCEL):
                return
        
        self.root.destroy()
    
    #######################################################
    #                ANALYSIS MENU ACTIONS
    #######################################################
    def get_full_pn(self):
        
        dialog = SelectItemDialog(self.project_tree, None, 'Tasks/')
        
        dialog.window.transient(self.root)
        self.root.wait_window(dialog.window)
        
        if not dialog.selection:
            return
        
        file_location = tkFileDialog.askdirectory(
                                                  title = 'Save Full Petri Net in...',
                                                  initialdir = os.path.dirname(self.file_path) if self.file_path is not None else os.path.expanduser('~/Desktop'),
                                                  parent = self.root,
                                                  mustexist = True
                                                  )
        
        if not file_location:
            return
        
        tmp_dir = tempfile.mkdtemp()
        #print tmp_dir
        folders = ('Actions/', 'CommActions/', 'Tasks/', 'Environment/')
        
        root_pred = ET.Element('AvailablePredicates')
        predicates_tree = ET.ElementTree(root_pred)
        
        added_predicates = set()
        
        for f in folders:
            dir_path = os.path.join(tmp_dir, f)
            os.mkdir(dir_path)
            
            root_models = ET.Element('AvailablePetriNetModels')
            models_tree = ET.ElementTree(root_models)
            children = self.project_tree.get_children(f)
            
            for current in children:
                path = current + '.pnml'
                pne = self.petri_nets[current]
                
                model = ET.SubElement(root_models, 'PetriNetModel')
                tmp = ET.SubElement(model, 'FilePath')
                tmp.text = os.path.basename(path)
                
                for p in pne._petri_net.places.itervalues():
                    if p.type == PlaceTypes.PREDICATE and p.name not in added_predicates and p.name[:4] != 'NOT_':
                        added_predicates.add(p.name)
                        pred = ET.SubElement(root_pred, 'Predicate')
                        tmp = ET.SubElement(pred, 'Name')
                        tmp.text = p.name
                        tmp = ET.SubElement(pred, 'InitialMarking')
                        tmp.text = str(p.init_marking)
                        tmp = ET.SubElement(pred, 'Comment')
                        tmp.text = '...'
                    
                    if f == 'Actions/':
                        if p._isRunningCondition:
                            tmp = ET.SubElement(model, 'RunningCondition')
                            tmp.text = ('NOT_' if p._isNegated else '') + p.name
                        
                        if p._isEffect:
                            tmp = ET.SubElement(model, 'DesiredEffect')
                            tmp.text = ('NOT_' if p._isNegated else '') + p.name
                
                file_path = os.path.join(tmp_dir, path)
                et = pne._petri_net.to_ElementTree()
                et = pnlab2pipe.convert(et)
                et.write(file_path, encoding = 'utf-8', xml_declaration = True)
                
            models_tree.write(os.path.join(tmp_dir, f, 'AvailableModels.xml'), encoding = 'utf-8', xml_declaration = True, pretty_print=True)
            
        predicates_tree.write(os.path.join(tmp_dir, 'PredicatesList.xml'), encoding = 'utf-8', xml_declaration = True, pretty_print=True)
        
        dir_path = os.path.join(tmp_dir, 'FullPetriNets/')
        os.mkdir(dir_path)
        
        path = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(path, 'Analysis_tools', 'expandNet')
        task = os.path.join(tmp_dir, dialog.selection + '.pnml')
        call([path, task])
        
        try:
            os.remove('PetriNetFramework.log')
        except:
            pass
        
        for f in folders:
            children = self.project_tree.get_children(f)
            
            for current in children:
                path = current + '.pnml'
                file_path = os.path.join(tmp_dir, path)
                os.remove(file_path)
            
            os.remove(os.path.join(tmp_dir, f, 'AvailableModels.xml'))
            
            dir_path = os.path.join(tmp_dir, f)
            os.rmdir(dir_path)
        
        final_filename = os.path.basename(dialog.selection) + '_full.pnml'
        
        call(['mv', os.path.join(tmp_dir, 'FullPetriNets', final_filename), os.path.join(file_location, final_filename + '.xml')])
        
        print 'Moved file to: ' + os.path.join(file_location, final_filename)
        
        os.remove(os.path.join(tmp_dir, 'PredicatesList.xml'))
        
        dir_path = os.path.join(tmp_dir, 'FullPetriNets')
        os.rmdir(dir_path)
        
        os.rmdir(tmp_dir)
    
    def computeMC(self):
        pass

if __name__ == '__main__':
    w = PNLab()
    
    tk.mainloop()
