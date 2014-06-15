# -*- coding: utf-8 -*-
"""
@author: Adrián Revuelta Cuauhtli
"""

import re
import Tkinter
import tkMessageBox

from copy import deepcopy
from PetriNets import Place, PlaceTypes, Vec2, Transition, TransitionTypes, PetriNet
from InputDialogs import PositiveIntDialog, NonNegativeFloatDialog

class PNEditor(Tkinter.Canvas):
    
    """
    Tk widget for editing Petri Net diagrams.
    
    Subclass of the Tkinter.Canvas Widget class. Handles several GUI interactions
    and provides some basic API methods to edit the Petri Net without the GUI events.
    """
    
    _GRID_SIZE = 100.0
    _GRID_SIZE_FACTOR = 3
    
    _MARKING_REGEX = re.compile('^[0-9]+$')
    _TOKEN_RADIUS = 3
    
    def __init__(self, parent, *args, **kwargs):
        """
        PNEditor constructor.
        
        Besides the usual Canvas parameters, it should receive at least either
        a Petri Net object or a name for the new Petri Net to be created.
        
        Keyword Arguments:
        PetriNet -- Petri Net object to load for viewing/editing.
        name -- In case no Petri Net object is specified, a name must be
                specified for the new Petri Net to be created.
        grid -- (Default True) Boolean that specifies whether to draw a square grid.
        """
        
        if not 'bg' in kwargs:
            kwargs['bg'] = 'white'
            
        self._grid = kwargs.pop('grid', True)
        self._label_transitions = kwargs.pop('label_transitions', False)
        self._petri_net = kwargs.pop('PetriNet', None)
        petri_net_name = kwargs.pop('name', None)
        
        if not (petri_net_name or self._petri_net):
            raise Exception('Either a PetriNet object or a name must be passed to the Petri Net Editor.')
        
        if not self._petri_net:
            if not petri_net_name:
                raise Exception('The PetriNet name cannot be an empty string.')
            self._petri_net = PetriNet(petri_net_name)
        
        Tkinter.Canvas.__init__(self, parent, *args, **kwargs)
        
        self._canvas_menu = Tkinter.Menu(self, tearoff = 0)
        self._canvas_menu.add_command(label = 'Add Action Place', command = self._create_action_place)
        self._canvas_menu.add_command(label = 'Add Predicate Place', command = self._create_predicate_place)
        self._canvas_menu.add_command(label = 'Add Task Place', command = self._create_task_place)
        self._canvas_menu.add_separator()
        self._canvas_menu.add_command(label = 'Add Immediate Transition', command = self._create_immediate_transition)
        self._canvas_menu.add_command(label = 'Add Stochastic Transition', command = self._create_stochastic_transition)
        
        self._place_menu = Tkinter.Menu(self, tearoff = 0)
        self._place_menu.add_command(label = 'Rename Place', command = self._rename_place)
        self._place_menu.add_command(label = 'Set Initial Marking', command = self._set_initial_marking)
        self._place_menu.add_command(label = 'Set Capacity', command = self._set_capacity)
        self._place_menu.add_separator()
        self._place_menu.add_command(label = 'Remove Place', command = self._remove_place)
        self._place_menu.add_separator()
        self._place_menu.add_command(label = 'Connect to...', command = self._connect_place_to)
        
        self._transition_menu = Tkinter.Menu(self, tearoff = 0)
        self._transition_menu.add_command(label = 'Rename Transition', command = self._rename_transition)
        self._transition_menu.add_command(label = 'Switch orientation', command = self._switch_orientation)
        self._transition_menu.add_command(label = 'Set Rate', command = self._set_rate)
        self._transition_menu.add_command(label = 'Set Priority', command = self._set_priority)
        self._transition_menu.add_separator()
        self._transition_menu.add_command(label = 'Remove Transition', command = self._remove_transition)
        self._transition_menu.add_separator()
        self._transition_menu.add_command(label = 'Connect to...', command = self._connect_transition_to)
        
        self._arc_menu = Tkinter.Menu(self, tearoff = 0)
        self._arc_menu.add_command(label = 'Set weight', command = self._set_weight)
        self._arc_menu.add_separator()
        self._arc_menu.add_command(label = 'Remove arc', command = self._remove_arc)
        
        self._last_point = Vec2()
        
        self._anchor_tag = 'all'
        self._anchor_set = False
        
        self._popped_up_menu = None
        self._state = 'normal'
        
        self._current_grid_size = PNEditor._GRID_SIZE
        
        self.set_petri_net(self._petri_net)
        
        ################################
        #        EVENT BINDINGs
        ################################
        self.bind('<Button-1>', self._left_click)
        self.bind('<B1-Motion>', self._dragCallback)
        self.bind('<ButtonRelease-1>', self._change_cursor_back)
        self.bind('<KeyPress-c>', self._center_diagram)
        
        #Windows and MAC OS:
        self.bind('<MouseWheel>', self._scale_canvas)
        #UNIX/Linux:
        self.bind('<Button-4>', self._scale_up)
        self.bind('<Button-5>', self._scale_down)
        
        self.bind('<Configure>', self._resize)
        
        #MAC OS:
        if (self.tk.call('tk', 'windowingsystem')=='aqua'):
            self.bind('<2>', self._popup_menu)
            self.bind('<Control-1>', self._popup_menu)
        #Windows / UNIX / Linux:
        else:
            self.bind('<3>', self._popup_menu)
    
    @property
    def petri_net(self):
        """Read-only propery. Deepcopy of the petri net object."""
        return deepcopy(self._petri_net)
    
    def disable(self):
        self._state = 'disabled'
    
    def enable(self):
        self._state = 'normal'
    
    def set_petri_net(self, newPN):
        """Loads a new Petri Net object to be viewed/edited."""
        
        '''
        #TODO (Possibly):
        Check PetriNet saved attribute, before changing the Petri Net
        or destroying the widget.
        '''
        self._petri_net = newPN
        
        self._place_count = len(newPN.places)
        self._transition_count = len(newPN.transitions)
        
        self._draw_petri_net()
    
    def add_place(self, p, overwrite = False):
        """Adds a place to the Petri Net and draws it.
        
        Note that it uses the PetriNet Class' instance method
        for adding the place and so it will remove any arc information
        it contains for the sake of maintaining consistency. 
        """
        
        if self._petri_net.add_place(p, overwrite):
            self._draw_place(p)
            self._place_count += 1
    
    def add_transition(self, t, overwrite = False):
        """Adds a transition to the Petri Net and draws it.
        
        Note that it uses the PetriNet Class' instance method
        for adding the transition and so it will remove any arc information
        it contains for the sake of maintaining consistency.
        """
        
        if self._petri_net.add_transition(t, overwrite):
            self._draw_transition(t)
            self._transition_count += 1
    
    def add_arc(self, source, target, weight = 1):
        """Adds an arc to the PetriNet object and draws it."""
        arc = self._petri_net.add_arc(source, target, weight)
        self._draw_arc(arc)
    
    def remove_place(self, p):
        """Removes the place from the Petri Net.
        
        p should be either a Place object, or
        a string representation of a place [i. e. str(place_object)]
        
        Returns the removed object.
        """
        
        p = self._petri_net.remove_place(p)
        
        self.delete('place_' + repr(p))
        self.delete('source_' + repr(p))
        self.delete('target_' + repr(p))
        return p
    
    def remove_transition(self, t):
        """Removes the transition from the Petri Net.
        
        t should be either a Transition object, or
        a string representation of a transition [i. e. str(transition_object)]
        
        Returns the removed object.
        """
        
        t = self._petri_net.remove_transition(t)
        
        self.delete('transition_' + repr(t))
        self.delete('source_' + repr(t))
        self.delete('target_' + repr(t))
        
        return t
    
    def remove_arc(self, source, target):
        """Removes an arc from the PetriNet object and from the canvas widget.""" 
        self._petri_net.remove_arc(source, target)
        self.delete('source_' + repr(source) + '&&' + 'target_' + repr(target))
    
    def _resize(self, event):
        self._draw_grid()
    
    def _draw_petri_net(self):
        """Draws an entire PetriNet.
        
        increase_count should be False when redrawing, to prevent
        the place and transition count to go up.
        """ 
        self._current_scale = self._petri_net.scale
        self._grid_offset = Vec2()
        
        self.delete('all')
        
        self._draw_grid()
        
        for p in self._petri_net.places.itervalues():
            self._draw_place(p)
        
        for t in self._petri_net.transitions.itervalues():
            self._draw_transition(t)
            
        self._draw_all_arcs()
    
    def _center_diagram(self, event):
        """Center all elements in the PetriNet inside the canvas current width and height."""
        
        if len(self._petri_net.places) + len(self._petri_net.transitions) == 0:
            return
        
        minx = 1000000000
        maxx = -1000000000
        miny = 1000000000
        maxy = -1000000000
        
        padding = PetriNet.TRANSITION_HALF_LARGE * 2 * self._current_scale
        
        for p in self._petri_net.places.itervalues():
            if p.position.x - padding < minx:
                minx = p.position.x - padding
            if p.position.x + padding > maxx:
                maxx = p.position.x + padding
            if p.position.y - padding < miny:
                miny = p.position.y - padding
            if p.position.y + padding > maxy:
                maxy = p.position.y + padding
        
        for t in self._petri_net.transitions.itervalues():
            if t.position.x - padding < minx:
                minx = t.position.x - padding
            if t.position.x + padding > maxx:
                maxx = t.position.x + padding
            if t.position.y - padding < miny:
                miny = t.position.y - padding
            if t.position.y + padding > maxy:
                maxy = t.position.y + padding
        
        w = maxx - minx
        h = maxy - miny
        canvas_width = self.winfo_width()
        canvas_height = self.winfo_height()
        
        if canvas_width == 1:
            canvas_width = self.winfo_reqwidth()
            canvas_height = self.winfo_reqheight()
        
        offset = Vec2(-minx, -miny)
        
        #canvas might not be squared:
        w_ratio = canvas_width/w
        h_ratio = canvas_height/h
        if w_ratio < h_ratio:
            #scale horizontally, center vertically
            scale_factor = w_ratio
            center_offset = Vec2(0, (canvas_height - h*scale_factor)/2)
        else:
            #scale vertically, center horizontally
            scale_factor = h_ratio
            center_offset = Vec2((canvas_width - w*scale_factor)/2, 0)
        
        # (new_pos - (0, 0))*scale_factor
        for p in self._petri_net.places.itervalues():
            p.position = (p.position + offset)*scale_factor + center_offset
        
        for t in self._petri_net.transitions.itervalues():
            t.position = (t.position + offset)*scale_factor + center_offset
        
        self._petri_net.scale = self._current_scale*scale_factor
        
        self._draw_petri_net()
    
    def _draw_grid(self):
        """Draws the grid on the background."""
        self.delete('grid')
        
        if not self._grid:
            return
        
        self._adjust_grid_offset()
        
        width = self.winfo_width()
        height = self.winfo_height()
        if width == 1:
            width = self.winfo_reqwidth()
            height = self.winfo_reqheight()
        
        startx = int(self._grid_offset.x - self._current_grid_size * self._current_scale)
        step = int(self._current_grid_size * self._current_scale / PNEditor._GRID_SIZE_FACTOR)
        
        for x in xrange(startx, width, step):
            self.create_line(x, 0, x, height, fill = '#BBBBFF', tags='grid')
        
        starty = int(self._grid_offset.y - self._current_grid_size * self._current_scale)
        for y in xrange(starty, height, step):
            self.create_line(0, y, width, y, fill = '#BBBBFF', tags='grid')
        
        step *= PNEditor._GRID_SIZE_FACTOR
        
        for x in xrange(startx, width, step):
            self.create_line(x, 0, x, height, fill = '#7777FF', width = 1.4, tags='grid')
        
        for y in xrange(starty, height, step):
            self.create_line(0, y, width, y, fill = '#7777FF', width = 1.4, tags='grid')
        
        self.tag_lower('grid')
    
    def _adjust_grid_offset(self):
        """Adjusts the grid offset caused by panning the workspace."""
        
        #current_grid_size is smaller than the small grid
        while self._current_grid_size * self._current_scale < PNEditor._GRID_SIZE / PNEditor._GRID_SIZE_FACTOR + 1:
            self._current_grid_size *= PNEditor._GRID_SIZE_FACTOR
        
        #small grid size is bigger than the current_grid_size
        while self._current_grid_size * self._current_scale >= PNEditor._GRID_SIZE * PNEditor._GRID_SIZE_FACTOR - 1:
            self._current_grid_size /= PNEditor._GRID_SIZE_FACTOR
        
        currentGridSize = int(self._current_grid_size * self._current_scale)
        
        while self._grid_offset.x < 0:
            self._grid_offset.x += currentGridSize
        while self._grid_offset.x >= currentGridSize:
            self._grid_offset.x -= currentGridSize
            
        while self._grid_offset.y < 0:
            self._grid_offset.y += currentGridSize
        while self._grid_offset.y >= currentGridSize:
            self._grid_offset.y -= currentGridSize
    
    def _get_current_item(self, event):
        
        halo = 10
        item = ''
        ids = self.find_closest(event.x, event.y, halo)
        ids = [x for x in ids if 'grid' not in self.gettags(x)]
        if ids:
            item = ids[0]
        ids = self.find_overlapping(event.x - halo, event.y - halo, event.x + halo, event.y + halo)
        ids = [x for x in ids if 'grid' not in self.gettags(x)]
        if ids:
            item = ids[0]
        return item
    
    def _get_place_name(self, item = None):
        """Get place name of the specified canvas item or the last clicked item if None given."""
        if not item:
            item = self._last_clicked_id
        
        tags = self.gettags(item)
        
        if 'place' not in tags:
            return None
        
        for tag in tags:
            if tag[:6] == 'place_':
                return tag[6:]
        
        raise Exception('Place name not found!')
    
    def _get_transition_name(self, item = None):
        """Get transition name of the specified canvas item or the last clicked item if None given."""
        if not item:
            item = self._last_clicked_id
        
        tags = self.gettags(item)
        
        if 'transition' not in tags:
            return None
        
        for tag in tags:
            if tag[:11] == 'transition_':
                return tag[11:]
        
        raise Exception('Transition name not found!')
    
    def _draw_all_arcs(self):
        """(Re-)Draws all arcs in the PetriNet object.""" 
        self.delete('arc')
        
        for p in self._petri_net.places.itervalues():
            for arc in p.incoming_arcs.itervalues():
                self._draw_arc(arc)
            for arc in p.outgoing_arcs.itervalues():
                self._draw_arc(arc)
    
    def _draw_item_arcs(self, obj):
        """Draws the arcs of one node from the PetriNet object."""
        
        self.delete('source_' + repr(obj))
        self.delete('target_' + repr(obj))
        for arc in obj.incoming_arcs.itervalues():
            self._draw_arc(arc)
        for arc in obj.outgoing_arcs.itervalues():
            self._draw_arc(arc)
    
    def _draw_place(self, p):
        """Draws a place object in the canvas widget."""
        place_id = self._draw_place_item(place = p)
        self._draw_marking(place_id, p)
        self.create_text(p.position.x,
                       p.position.y + PetriNet.PLACE_LABEL_PADDING*self._current_scale,
                       tags = ('label', 'place_' + repr(p)) + self.gettags(place_id),
                       text = str(p) )
        
        return place_id
    
    def _draw_transition(self, t):
        """Draws a transition object in the canvas widget."""
        trans_id = self._draw_transition_item(transition = t)
        
        if t.isHorizontal:
            padding = PetriNet.TRANSITION_HORIZONTAL_LABEL_PADDING
        else:
            padding = PetriNet.TRANSITION_VERTICAL_LABEL_PADDING
        
        if self._label_transitions:
            self.create_text(t.position.x,
                           t.position.y + padding*self._current_scale,
                           tags = ('label', 'transition_' + repr(t)) + self.gettags(trans_id),
                           text = str(t) )
        
        return trans_id
    
    def _remove_place(self):
        """Menu callback to remove clicked place."""
        self._hide_menu()
        name = self._get_place_name()
        self.remove_place(name)
    
    def _remove_transition(self):
        """Menu callback to remove clicked transition."""
        self._hide_menu()
        name = self._get_transition_name()
        self.remove_transition(name)
    
    def _remove_arc(self):
        """Menu callback to remove clicked arc."""
        self._hide_menu()
        
        tags = self.gettags(self._last_clicked_id)
        
        if 'arc' not in tags:
            return None
        
        source_name = ''
        target_name = ''
        
        for tag in tags:
            if tag[:7] == 'source_':
                source_name = tag[7:]
            elif tag[:7] == 'target_':
                target_name = tag[7:]
        
        if not source_name or not target_name:
            raise Exception('No source and target specified!')
        
        if source_name in self._petri_net.places:
            source = self._petri_net.places[source_name]
            target = self._petri_net.transitions[target_name]
        else:
            source = self._petri_net.transitions[source_name]
            target = self._petri_net.places[target_name]
        
        self.remove_arc(source, target)
    
    def _rename_place(self):
        """Menu callback to rename clicked place.
            
            Removes the clicked place and creates a new one with the same properties,
            then sets the entry widget for entering the new name.  
        """
        self._hide_menu()
        name = self._get_place_name()
        
        #Adjust height when label is occluded
        #h = int(self.config()['height'][4])
        h = self.winfo_height()
        if h == 1:
            h = self.winfo_reqheight()
        entry_y = self._last_point.y + (PetriNet.PLACE_LABEL_PADDING + 10)*self._current_scale + 10
        if entry_y > h:
            dif = Vec2(0.0, h - entry_y)
            self.move('all', dif.x, dif.y)
            for p in self._petri_net.places.itervalues():
                p.position += dif
            for t in self._petri_net.transitions.itervalues():
                t.position += dif
            self._draw_all_arcs()
            if self._grid:
                self._grid_offset = (self._grid_offset + dif).int
                self._draw_grid()
        
        p = self._petri_net.places[name]
        canvas_id = self._last_clicked_id
        
        self.delete('label&&place_' + repr(p))
        
        self.dtag('p_' + str(canvas_id), 'place_' + repr(p))
        self._set_rename_place_entry(canvas_id, p)
        
    def _rename_transition(self):
        """Menu callback to rename clicked transition.
            
            Removes the clicked transition and creates a new one with the same properties,
            then sets the entry widget for entering the new name.  
        """
        self._hide_menu()
        name = self._get_transition_name()
        
        #Adjust height when label is occluded
        #h = int(self.config()['height'][4])
        h = self.winfo_height()
        if h == 1:
            h = self.winfo_reqheight()
        entry_y = self._last_point.y + (PetriNet.TRANSITION_HORIZONTAL_LABEL_PADDING + 10)*self._current_scale + 10
        if entry_y > h:
            #old_t.position.y -= entry_y - h
            dif = Vec2(0.0, h - entry_y)
            self.move('all', dif.x, dif.y)
            for p in self._petri_net.places.itervalues():
                p.position += dif
            for t in self._petri_net.transitions.itervalues():
                t.position += dif
            self._draw_all_arcs()
            if self._grid:
                self._grid_offset = (self._grid_offset + dif).int
                self._draw_grid()
        
        t = self._petri_net.transitions[name]
        canvas_id = self._last_clicked_id
        
        self.delete('label&&transition_' + repr(t))
        
        self.dtag('t_' + str(canvas_id), 'transition_' + repr(t))
        self._set_rename_transition_entry(canvas_id, t)
    
    def _connect_place_to(self):
        """Menu callback to connect clicked place to a transition."""
        self._hide_menu()
        self._state = 'connecting_place'
        self.itemconfig('place', state = Tkinter.DISABLED)
        self.itemconfig('transition&&!label', outline = '#FFFF00', width = 5)
        self._connecting_place_fn_id = self.bind('<Motion>', self._connecting_place, '+')
        name = self._get_place_name()
        self._source = self._petri_net.places[name]
        
    def _connecting_place(self, event):
        """Event callback to draw an arc when connecting a place."""
        
        item = self._get_current_item(event)
        self.delete('connecting')
        
        if item and 'transition' in self.gettags(item):
            name = self._get_transition_name(item)
            target = self._petri_net.transitions[name]
            place_vec = target.position - self._source.position
            trans_vec = -place_vec
            place_point = self._source.position + place_vec.unit*PetriNet.PLACE_RADIUS*self._current_scale
            transition_point = self._find_intersection(target, trans_vec)
            self.create_line(place_point.x,
                         place_point.y,
                         transition_point.x,
                         transition_point.y,
                         tags = ('connecting',),
                         width = PetriNet.LINE_WIDTH,
                         arrow= Tkinter.LAST,
                         arrowshape = (10,12,5) )
        else:
            target_pos = Vec2(event.x, event.y)
            place_vec = target_pos - self._source.position
            place_point = self._source.position + place_vec.unit*PetriNet.PLACE_RADIUS*self._current_scale
            self.create_line(place_point.x,
                         place_point.y,
                         target_pos.x,
                         target_pos.y,
                         tags = ('connecting',),
                         width = PetriNet.LINE_WIDTH,
                         arrow= Tkinter.LAST,
                         arrowshape = (10,12,5) )
    
    def _connect_transition_to(self):
        """Menu callback to connect clicked transition to a place."""
        self._hide_menu()
        self._state = 'connecting_transition'
        self.itemconfig('transition', state = Tkinter.DISABLED)
        self.itemconfig('place&&!label&&!token', outline = '#FFFF00', width = 5)
        self._connecting_transition_fn_id = self.bind('<Motion>', self._connecting_transition, '+')
        name = self._get_transition_name()
        self._source = self._petri_net.transitions[name]
        
    def _connecting_transition(self, event):
        """Event callback to draw an arc when connecting a transition."""
        
        item = self._get_current_item(event)
            
        self.delete('connecting')
        
        if item and 'place' in self.gettags(item):
            name = self._get_place_name(item)
            target = self._petri_net.places[name]
            place_vec = self._source.position - target.position
            trans_vec = -place_vec
            target_point = target.position + place_vec.unit*PetriNet.PLACE_RADIUS*self._current_scale
        else:
            target_point = Vec2(event.x, event.y)
            trans_vec = target_point - self._source.position
        
        transition_point = self._find_intersection(self._source, trans_vec)
        self.create_line(transition_point.x,
                     transition_point.y,
                     target_point.x,
                     target_point.y,
                     tags = ('connecting',),
                     width = PetriNet.LINE_WIDTH,
                     arrow= Tkinter.LAST,
                     arrowshape = (10,12,5) )
    
    def _switch_orientation(self):
        """Menu callback to switch clicked transition's orientation."""
        self._hide_menu()
        name = self._get_transition_name()
        
        t = self._petri_net.transitions[name]
        t.isHorizontal = not t.isHorizontal
        
        self.delete('source_' + name)
        self.delete('target_' + name)
        self.delete('transition_' + name)
        
        self._draw_transition(t)
        self._draw_item_arcs(t)
        
    def _set_initial_marking(self):
        """Menu callback to set the initial marking of a Place."""
        self._hide_menu()
        name = self._get_place_name()
        p = self._petri_net.places[name]
        self._set_marking_entry(self._last_clicked_id, p)
        
        txtbox = Tkinter.Entry(self)
        txtbox.insert(0, str(p.init_marking))
        txtbox.selection_range(0, Tkinter.END)
        txtbox_id = self.create_window(p.position.x, p.position.y, height= 20, width = 20, window = txtbox)
        txtbox.grab_set()
        txtbox.focus_set()
        
        callback = self._get_marking_callback(txtbox, txtbox_id, self._last_clicked_id, p)
        
        txtbox.bind('<KeyPress-Return>', callback)
    
    def _set_capacity(self):
        """Menu callback to set the capacity of a Place."""
        self._hide_menu()
        name = self._get_place_name()
        p = self._petri_net.places[name]
        
        dialog = PositiveIntDialog('Set place capacity', 'Write a positive number for \nthe capacity of place: ' + str(p), 'Capacity', init_value = p.capacity)
        dialog.window.transient(self)
        self.wait_window(dialog.window)
        if dialog.value_set:
            p.capacity = int(dialog.input_var.get())
    
    def _set_rate(self):
        """Menu callback to set the rate of a Transition."""
        self._hide_menu()
        name = self._get_transition_name()
        t = self._petri_net.transitions[name]
        
        dialog = NonNegativeFloatDialog("Set transition's rate", 'Write a positive decimal number for \nthe rate of transition: ' + str(t), 'Rate', init_value = t.rate)
        dialog.window.transient(self)
        self.wait_window(dialog.window)
        if dialog.value_set:
            t.rate = float(dialog.input_var.get())
    
    def _set_priority(self):
        """Menu callback to set the priority of a Transition."""
        self._hide_menu()
        name = self._get_transition_name()
        t = self._petri_net.transitions[name]
        
        dialog = PositiveIntDialog("Set transition's priority", 'Write a positive integer for \nthe priority of transition: ' + str(t), 'Priority', init_value = t.priority)
        dialog.window.transient(self)
        self.wait_window(dialog.window)
        if dialog.value_set:
            t.priority = int(dialog.input_var.get())
    
    def _set_weight(self):
        """Menu callback to set the weight of an arc."""
        self._hide_menu()
        
        tags = self.gettags(self._last_clicked_id)
        
        if 'arc' not in tags:
            return None
        
        source_name = ''
        target_name = ''
        
        for tag in tags:
            if tag[:7] == 'source_':
                source_name = tag[7:]
            elif tag[:7] == 'target_':
                target_name = tag[7:]
        
        if not source_name or not target_name:
            raise Exception('No source and target specified!')
        
        if source_name in self._petri_net.places:
            arc = self._petri_net.places[source_name]._outgoing_arcs[target_name] 
        else:
            arc = self._petri_net.places[target_name]._incoming_arcs[source_name]
            
        dialog = PositiveIntDialog("Set arc's weight", 'Write a positive integer for \nthe weight of arc: ' + str(arc), 'Weight', init_value = arc.weight)
        dialog.window.transient(self)
        self.wait_window(dialog.window)
        if dialog.value_set:
            arc.weight = int(dialog.input_var.get())
            self._draw_arc(arc)
    
    def _get_marking_callback(self, txtbox, txtbox_id, canvas_id, p):
        """Callback factory function for the marking entry widget."""
        def txtboxCallback(event):
            txt = txtbox.get()
            if not PNEditor._MARKING_REGEX.match(txt):
                msg = ('Please input a positive integer number for the marking.')
                tkMessageBox.showerror('Invalid Marking', msg)
                return
            p.init_marking = int(txt)
            self._draw_marking(canvas_id, p)
            txtbox.grab_release()
            txtbox.destroy()
            self.delete(txtbox_id)
            
        return txtboxCallback
    
    def _draw_marking(self, canvas_id, p):
        """Draws the marking of the given place."""
        tag = 'token_' + repr(p)
        
        self.delete(tag)
        
        if p.init_marking == 0:
            return
        tags = ('token', tag) + self.gettags(canvas_id)
        if p.init_marking == 1:
            self.create_oval(p.position.x - PNEditor._TOKEN_RADIUS,
                             p.position.y - PNEditor._TOKEN_RADIUS,
                             p.position.x + PNEditor._TOKEN_RADIUS,
                             p.position.y + PNEditor._TOKEN_RADIUS,
                             tags = tags,
                             fill = 'black' )
            self.scale(tag, p.position.x, p.position.y, self._current_scale, self._current_scale)
            return
        if p.init_marking == 2:
            self.create_oval(p.position.x - 3*PNEditor._TOKEN_RADIUS,
                             p.position.y - PNEditor._TOKEN_RADIUS,
                             p.position.x - PNEditor._TOKEN_RADIUS,
                             p.position.y + PNEditor._TOKEN_RADIUS,
                             tags = tags,
                             fill = 'black' )
            self.create_oval(p.position.x + PNEditor._TOKEN_RADIUS,
                             p.position.y - PNEditor._TOKEN_RADIUS,
                             p.position.x + 3*PNEditor._TOKEN_RADIUS,
                             p.position.y + PNEditor._TOKEN_RADIUS,
                             tags = tags,
                             fill = 'black' )
            self.scale(tag, p.position.x, p.position.y, self._current_scale, self._current_scale)
            return
        if p.init_marking == 3:
            self.create_oval(p.position.x + PNEditor._TOKEN_RADIUS,
                             p.position.y + PNEditor._TOKEN_RADIUS,
                             p.position.x + 3*PNEditor._TOKEN_RADIUS,
                             p.position.y + 3*PNEditor._TOKEN_RADIUS,
                             tags = tags,
                             fill = 'black' )
            self.create_oval(p.position.x - 3*PNEditor._TOKEN_RADIUS,
                             p.position.y + PNEditor._TOKEN_RADIUS,
                             p.position.x - PNEditor._TOKEN_RADIUS,
                             p.position.y + 3*PNEditor._TOKEN_RADIUS,
                             tags = tags,
                             fill = 'black' )
            self.create_oval(p.position.x - PNEditor._TOKEN_RADIUS,
                             p.position.y - 3*PNEditor._TOKEN_RADIUS,
                             p.position.x + PNEditor._TOKEN_RADIUS,
                             p.position.y - PNEditor._TOKEN_RADIUS,
                             tags = tags,
                             fill = 'black' )
            self.scale(tag, p.position.x, p.position.y, self._current_scale, self._current_scale)
            return
        
        fill = 'black'
        if p.type == PlaceTypes.PREDICATE:
            fill = 'white'
        
        self.create_text(p.position.x,
                         p.position.y,
                         text = str(p.init_marking),
                         tags=tags,
                         fill = fill )
    
    def _create_action_place(self):
        """Menu callback to create an ACTION place."""
        self._hide_menu()
        placeType = PlaceTypes.ACTION
        self._create_place(placeType)
    
    def _create_predicate_place(self):
        """Menu callback to create an PREDICATE place."""
        self._hide_menu()
        placeType = PlaceTypes.PREDICATE
        self._create_place(placeType)
    
    def _create_task_place(self):
        """Menu callback to create an TASK place."""
        self._hide_menu()
        placeType = PlaceTypes.TASK
        self._create_place(placeType)
        
    def _create_place(self, placeType):
        """Creates a Place object, draws it and sets the label entry for entering the name."""
        
        #Adjust height when label is occluded
        #h = int(self.config()['height'][4])
        h = self.winfo_height()
        if h == 1:
            h = self.winfo_reqheight()
        entry_y = self._last_point.y + (PetriNet.PLACE_LABEL_PADDING + 10)*self._current_scale + 10
        if entry_y > h:
            dif = Vec2(0.0, h - entry_y)
            self.move('all', dif.x, dif.y)
            for p in self._petri_net.places.itervalues():
                p.position += dif
            for t in self._petri_net.transitions.itervalues():
                t.position += dif
            self._draw_all_arcs()
            if self._grid:
                self._grid_offset = (self._grid_offset + dif).int
                self._draw_grid()
            
            self._last_point += dif
        
        item = self._draw_place_item(self._last_point, placeType)
        p = Place('p' + '%02d' % (self._place_count + 1), placeType, self._last_point)
        self._set_create_place_entry(item, p)
    
    def _create_immediate_transition(self):
        """Menu callback to create an IMMEDIATE transition."""
        self._hide_menu()
        transitionType = TransitionTypes.IMMEDIATE
        self._create_transition(transitionType)
    
    def _create_stochastic_transition(self):
        """Menu callback to create a TIMED_STOCHASTIC transition."""
        self._hide_menu()
        transitionType = TransitionTypes.TIMED_STOCHASTIC
        self._create_transition(transitionType)
    
    def _create_transition(self, transitionType):
        """Creates a Transition object, draws it and sets the label entry for entering the name."""
        
        #Adjust height when label is occluded
        #h = int(self.config()['height'][4])
        h = self.winfo_height()
        if h == 1:
            h = self.winfo_reqheight()
        entry_y = self._last_point.y + (PetriNet.TRANSITION_HORIZONTAL_LABEL_PADDING + 10)*self._current_scale + 10
        if entry_y > h:
            dif = Vec2(0.0, h - entry_y)
            self.move('all', dif.x, dif.y)
            for p in self._petri_net.places.itervalues():
                p.position += dif
            for t in self._petri_net.transitions.itervalues():
                t.position += dif
            self._draw_all_arcs()
            if self._grid:
                self._grid_offset = (self._grid_offset + dif).int
                self._draw_grid()
            self._last_point += dif
        
        item = self._draw_transition_item(self._last_point, transitionType)
        t = Transition('t' + '%02d' % (self._transition_count + 1), transitionType, self._last_point)
        self._set_create_transition_entry(item, t)
    
    def _draw_place_item(self, point = None, placeType = PlaceTypes.PREDICATE, place = None):
        """Draws a place item, with the attributes corresponding to the place type.
        
            Returns the id generated by the canvas widget.
        """
        self._hide_menu()
        place_tag = ''
        if place:
            point = place.position
            place_tag = 'place_' + repr(place)
            placeType = place.type
        elif not point:
            point = Vec2()
            
        
        item = self.create_oval(point.x - PetriNet.PLACE_RADIUS,
                         point.y - PetriNet.PLACE_RADIUS,
                         point.x + PetriNet.PLACE_RADIUS,
                         point.y + PetriNet.PLACE_RADIUS,
                         tags = ('place', placeType, place_tag),
                         width = PetriNet.LINE_WIDTH,
                         fill = PetriNet.PLACE_CONFIG[placeType]['fill'],
                         outline = PetriNet.PLACE_CONFIG[placeType]['outline'],
                         disabledfill = '#888888',
                         disabledoutline = '#888888' )
        self.addtag_withtag('p_' + str(item), item)
        self.scale(item, point.x, point.y, self._current_scale, self._current_scale)
        return item
    
    def _draw_transition_item(self, point = None, transitionType = TransitionTypes.IMMEDIATE, transition = None):
        """Draws a transition item, with the attributes corresponding to the transition type.
        
            Returns the id generated by the canvas widget.
        """
        self._hide_menu()
        
        transition_tag = ''
        if transition:
            point = transition.position
            transition_tag = 'transition_' + repr(transition)
            transitionType = transition.type
        elif not point:
            point = Vec2()
        
        x0 = point.x - PetriNet.TRANSITION_HALF_SMALL
        y0 = point.y - PetriNet.TRANSITION_HALF_LARGE
        x1 = point.x + PetriNet.TRANSITION_HALF_SMALL
        y1 = point.y + PetriNet.TRANSITION_HALF_LARGE
        
        if transition and transition.isHorizontal:
            x0 = point.x - PetriNet.TRANSITION_HALF_LARGE
            y0 = point.y - PetriNet.TRANSITION_HALF_SMALL
            x1 = point.x + PetriNet.TRANSITION_HALF_LARGE
            y1 = point.y + PetriNet.TRANSITION_HALF_SMALL
        
        item = self.create_rectangle(x0, y0, x1, y1,
                         tags = ('transition', transitionType, transition_tag),
                         width = PetriNet.LINE_WIDTH,
                         fill = PetriNet.TRANSITION_CONFIG[transitionType]['fill'],
                         outline = PetriNet.TRANSITION_CONFIG[transitionType]['outline'],
                         disabledfill = '#888888',
                         disabledoutline = '#888888' )
        
        self.addtag_withtag('t_' + str(item), item)
        self.scale(item, point.x, point.y, self._current_scale, self._current_scale)
        return item
    
    def _set_create_place_entry(self, canvas_id, p):
        """Sets the Entry Widget used to set the name of a new place.
            
            Calls the label callback factory function to bind the callback 
            to the <KeyPress-Return> event.
        """
        txtbox = Tkinter.Entry(self)
        txtbox.insert(0, str(p))
        txtbox.selection_range(2, Tkinter.END)
        #extra padding because entry position refers to the center, not the corner
        label_padding = PetriNet.PLACE_LABEL_PADDING + 10
        
        txtbox_id = self.create_window(p.position.x, p.position.y + label_padding*self._current_scale, height= 20, width = 85, window = txtbox)
        txtbox.grab_set()
        txtbox.focus_set()
        
        callback = self._get_create_place_callback(txtbox, txtbox_id, canvas_id, p)
        
        escape_callback = self._get_cancel_create_callback(txtbox, txtbox_id, canvas_id, p)
        
        txtbox.bind('<KeyPress-Return>', callback)
        txtbox.bind('<KeyPress-Escape>', escape_callback)
    
    def _set_create_transition_entry(self, canvas_id, t):
        """Sets the Entry Widget used to set the name of a new transition.
            
            Calls the label callback factory function to bind the callback 
            to the <KeyPress-Return> event.
        """
        txtbox = Tkinter.Entry(self)
        txtbox.insert(0, str(t))
        txtbox.selection_range(2, Tkinter.END)
        #extra padding because entry position refers to the center, not the corner
        if t.isHorizontal:
            label_padding = PetriNet.TRANSITION_HORIZONTAL_LABEL_PADDING + 10
        else:
            label_padding = PetriNet.TRANSITION_VERTICAL_LABEL_PADDING + 10
        
        txtbox_id = self.create_window(t.position.x, t.position.y + label_padding*self._current_scale, height= 20, width = 85, window = txtbox)
        txtbox.grab_set()
        txtbox.focus_set()
        
        callback = self._get_create_transition_callback(txtbox, txtbox_id, canvas_id, t)
        
        escape_callback = self._get_cancel_create_callback(txtbox, txtbox_id, canvas_id, t)
        
        txtbox.bind('<KeyPress-Return>', callback)
        txtbox.bind('<KeyPress-Escape>', escape_callback)
    
    def _get_create_place_callback(self, txtbox, txtbox_id, canvas_id, p):
        """Callback factory function for the <KeyPress-Return> event of the 'create place' entry widget."""
        def txtboxCallback(event):
            txt = txtbox.get()
            if not (txt[:2] == p.type[0] + '.' and len(txt) > 2):
                msg = ('A place name must begin with the first letter of its type and a dot, ' +
                    'followed by a non-empty string, preferably composed of only ' +
                    'alphanumeric characters, and possibly dashes or underscores. \
                     \
                    Examples: a.my_Action, t.task1')
                tkMessageBox.showerror('Invalid Name', msg)
                return
            new_p = Place(txt[2:], p.type, p.position, p.init_marking, p.capacity)
            label_padding = PetriNet.PLACE_LABEL_PADDING
            if not self._petri_net.add_place(new_p):
                tkMessageBox.showerror('Insertion failed', 'Failed to add place to the Petri Net. Possible id duplicate.')
                return
            self.addtag_withtag('place_' + repr(new_p), canvas_id)
            tags = ('label',) + self.gettags(canvas_id)
            self.create_text(new_p.position.x,
                             new_p.position.y + label_padding*self._current_scale,
                             text = str(new_p),
                             tags=tags )
            self._place_count += 1
            txtbox.grab_release()
            txtbox.destroy()
            self.delete(txtbox_id)
        return txtboxCallback
    
    def _get_create_transition_callback(self, txtbox, txtbox_id, canvas_id, t):
        """Callback factory function for the <KeyPress-Return> event of the 'create transition' entry widget."""
        def txtboxCallback(event):
            txt = txtbox.get()
            if not (txt[:2] == t.type[0] + '.' and len(txt) > 2):
                msg = ("A transition name must begin with an 'i' and a dot if it's an immediate transition " +
                       "or an 's' and a dot if it's a timed_stochastic transition, " + 
                       "followed by a non-empty string, preferably composed of only " +
                       "alphanumeric characters, and possibly dashes or underscores. \
                       \
                       Example: i.transition1, s.t-2")
                tkMessageBox.showerror('Invalid Name', msg)
                return
            new_t = Transition(txt[2:], t.type, t.position, t.isHorizontal, t.rate, t.priority)
            if new_t.isHorizontal:
                label_padding = PetriNet.TRANSITION_HORIZONTAL_LABEL_PADDING
            else:
                label_padding = PetriNet.TRANSITION_VERTICAL_LABEL_PADDING
            if not self._petri_net.add_transition(new_t):
                tkMessageBox.showerror('Insertion failed', 'Failed to add transition to the Petri Net. Possible duplicate id.')
                return
            self.addtag_withtag('transition_' + repr(new_t), canvas_id)
            tags = ('label',) + self.gettags(canvas_id)
            if self._label_transitions:
                self.create_text(new_t.position.x,
                                 new_t.position.y + label_padding*self._current_scale,
                                 text = str(new_t),
                                 tags=tags )
            self._transition_count += 1
            txtbox.grab_release()
            txtbox.destroy()
            self.delete(txtbox_id)
        return txtboxCallback
    
    def _get_cancel_create_callback(self, txtbox, txtbox_id, canvas_id, obj):
        """Callback factory function for the <KeyPress-Escape> event of the 'create' entry widget."""
        def escape_callback(event):
            txtbox.grab_release()
            txtbox.destroy()
            self.delete(txtbox_id)
            self.delete(canvas_id)
        return escape_callback
    
    def _set_rename_place_entry(self, canvas_id, p):
        """Sets the Entry Widget used to set the new name of a place.
            
            Calls the callback factory functions to bind the callbacks 
            to the <KeyPress-Return> and <KeyPress-Escape> events.
        """
        txtbox = Tkinter.Entry(self)
        txtbox.insert(0, str(p))
        txtbox.selection_range(2, Tkinter.END)
        
        #extra padding because entry position refers to the center, not the corner
        label_padding = PetriNet.PLACE_LABEL_PADDING + 10
        
        txtbox_id = self.create_window(p.position.x, p.position.y + label_padding*self._current_scale, height= 20, width = 85, window = txtbox)
        txtbox.grab_set()
        txtbox.focus_set()
        
        callback = self._get_rename_place_callback(txtbox, txtbox_id, canvas_id, p)
        
        escape_callback = self._get_cancel_rename_place_callback(txtbox, txtbox_id, canvas_id, p)
        
        txtbox.bind('<KeyPress-Return>', callback)
        txtbox.bind('<KeyPress-Escape>', escape_callback)
    
    def _set_rename_transition_entry(self, canvas_id, t):
        """Sets the Entry Widget used to set the new name of a transition.
            
            Calls the callback factory functions to bind the callbacks 
            to the <KeyPress-Return> and <KeyPress-Escape> events.
        """
        txtbox = Tkinter.Entry(self)
        txtbox.insert(0, str(t))
        txtbox.selection_range(2, Tkinter.END)
        
        #extra padding because entry position refers to the center, not the corner
        if t.isHorizontal:
            label_padding = PetriNet.TRANSITION_HORIZONTAL_LABEL_PADDING + 10
        else:
            label_padding = PetriNet.TRANSITION_VERTICAL_LABEL_PADDING + 10
        
        txtbox_id = self.create_window(t.position.x, t.position.y + label_padding*self._current_scale, height= 20, width = 85, window = txtbox)
        txtbox.grab_set()
        txtbox.focus_set()
        
        callback = self._get_rename_transition_callback(txtbox, txtbox_id, canvas_id, t)
        
        escape_callback = self._get_cancel_rename_transition_callback(txtbox, txtbox_id, canvas_id, t)
        
        txtbox.bind('<KeyPress-Return>', callback)
        txtbox.bind('<KeyPress-Escape>', escape_callback)
    
    def _get_rename_place_callback(self, txtbox, txtbox_id, canvas_id, p):
        """Callback factory function for the <KeyPress-Return> event of the 'rename place' entry widget."""
        def txtboxCallback(event):
            txt = txtbox.get()
            if not (txt[:2] == p.type[0] + '.' and len(txt) > 2):
                msg = ('A place name must begin with the first letter of its type and a dot, ' +
                    'followed by a non-empty string, preferably composed of only ' +
                    'alphanumeric characters, and possibly dashes or underscores. \
                     \
                    Examples: a.my_Action, t.task1')
                tkMessageBox.showerror('Invalid Name', msg)
                return
            self.delete('source_' + repr(p))
            self.delete('target_' + repr(p))
            try:
                if not self._petri_net.rename_place(p, txt[2:]):
                    self._draw_item_arcs(p)
                    tkMessageBox.showerror('Duplicate name', 'A place of the same type with that name already exists in the Petri Net.')
                    return
            except Exception as e:
                self._draw_item_arcs(p)
                tkMessageBox.showerror('ERROR', str(e))
                return
            self.addtag_withtag('place_' + repr(p), canvas_id)
            tags = ('label',) + self.gettags(canvas_id)
            self.create_text(p.position.x,
                             p.position.y + PetriNet.PLACE_LABEL_PADDING*self._current_scale,
                             text = str(p),
                             tags=tags )
            self._draw_item_arcs(p)
            
            txtbox.grab_release()
            txtbox.destroy()
            self.delete(txtbox_id)
        return txtboxCallback
    
    def _get_rename_transition_callback(self, txtbox, txtbox_id, canvas_id, t):
        """Callback factory function for the <KeyPress-Return> event of the 'rename transition' entry widget."""
        def txtboxCallback(event):
            txt = txtbox.get()
            if not (txt[:2] == t.type[0] + '.' and len(txt) > 2):
                msg = ("A transition name must begin with an 'i' and a dot if it's an immediate transition " +
                       "or an 's' and a dot if it's a timed_stochastic transition, " + 
                       "followed by a non-empty string, preferably composed of only " +
                       "alphanumeric characters, and possibly dashes or underscores. \
                       \
                       Example: i.transition1, s.t-2")
                tkMessageBox.showerror('Invalid Name', msg)
                return
            self.delete('source_' + repr(t))
            self.delete('target_' + repr(t))
            try:
                if not self._petri_net.rename_transition(t, txt[2:]):
                    self._draw_item_arcs(t)
                    tkMessageBox.showerror('Duplicate name', 'A transition of the same type with that name already exists in the Petri Net.')
                    return
            except Exception as e:
                self._draw_item_arcs(t)
                tkMessageBox.showerror('ERROR', str(e))
                return
            self.addtag_withtag('transition_' + repr(t), canvas_id)
            if t.isHorizontal:
                label_padding = PetriNet.TRANSITION_HORIZONTAL_LABEL_PADDING + 10
            else:
                label_padding = PetriNet.TRANSITION_VERTICAL_LABEL_PADDING + 10
            tags = ('label',) + self.gettags(canvas_id)
            if self._label_transitions:
                self.create_text(t.position.x,
                                 t.position.y + label_padding*self._current_scale,
                                 text = str(t),
                                 tags=tags )
            self._draw_item_arcs(t)
            
            txtbox.grab_release()
            txtbox.destroy()
            self.delete(txtbox_id)
        return txtboxCallback
    
    def _get_cancel_rename_place_callback(self, txtbox, txtbox_id, canvas_id, p):
        """Callback factory function for the <KeyPress-Escape> event of the 'rename place' entry widget."""
        def escape_callback(event):
            label_padding = PetriNet.PLACE_LABEL_PADDING
            self.addtag_withtag('place_' + repr(p), canvas_id)
            tags = ('label',) + self.gettags(canvas_id)
            self.create_text(p.position.x,
                             p.position.y + label_padding*self._current_scale,
                             text = str(p),
                             tags=tags )
            self._draw_item_arcs(p)
            txtbox.grab_release()
            txtbox.destroy()
            self.delete(txtbox_id)
        return escape_callback
    
    def _get_cancel_rename_transition_callback(self, txtbox, txtbox_id, canvas_id, t):
        """Callback factory function for the <KeyPress-Escape> event of the 'rename transition' entry widget."""
        def escape_callback(event):
            if t.isHorizontal:
                label_padding = PetriNet.TRANSITION_HORIZONTAL_LABEL_PADDING
            else:
                label_padding = PetriNet.TRANSITION_VERTICAL_LABEL_PADDING
            self.addtag_withtag('transition_' + repr(t), canvas_id)
            tags = ('label',) + self.gettags(canvas_id)
            if self._label_transitions:
                self.create_text(t.position.x,
                                 t.position.y + label_padding*self._current_scale,
                                 text = str(t),
                                 tags=tags )
            txtbox.grab_release()
            txtbox.destroy()
            self.delete(txtbox_id)
        return escape_callback
    
    def _draw_arc(self, arc):
        """Draws the arc specified by the source and target objects, which must be
            instances of Place and Transition classes, one of each."""
        if isinstance(arc.source, Place):
            p = arc.source
            t = arc.target
        else:
            p = arc.target
            t = arc.source
        
        self.delete('source_' + repr(arc.source) + '&&target_' + repr(arc.target))
        
        place_vec = t.position - p.position
        trans_vec = -place_vec
        place_point = p.position + place_vec.unit*PetriNet.PLACE_RADIUS*self._current_scale
        transition_point = self._find_intersection(t, trans_vec)
        
        if isinstance(arc.source, Place):
            src_point = place_point
            trgt_point = transition_point
        else:
            src_point = transition_point
            trgt_point = place_point
        
        tags = ('arc', 'source_' + repr(arc.source), 'target_' + repr(arc.target))
        
        self.create_line(src_point.x,
                         src_point.y,
                         trgt_point.x,
                         trgt_point.y,
                         tags = tags,
                         width = PetriNet.LINE_WIDTH,
                         arrow= Tkinter.LAST,
                         arrowshape = (10,12,5) )
        
        if arc.weight > 1:
            arc_vec = arc.target.position - arc.source.position
            offset = Vec2(arc_vec.unit.y, -arc_vec.unit.x)*PetriNet.PLACE_RADIUS/2
            text_pos = (src_point + trgt_point)/2 + offset
            self.create_text(text_pos.x,
                             text_pos.y,
                             tags = tags + ('label',),
                             text = str(arc.weight)
                             )
        
        
    def _find_intersection(self, t, vec):
        """This is used to compute the point where an arc hits an edge
            of a transition's graphic representation (rectangle)."""
        #NOTE: vec is a vector from the transition's center
        
        if t.isHorizontal:
            half_width = PetriNet.TRANSITION_HALF_LARGE
            half_height = PetriNet.TRANSITION_HALF_SMALL
        else:
            half_width = PetriNet.TRANSITION_HALF_SMALL
            half_height = PetriNet.TRANSITION_HALF_LARGE
        
        half_width *= self._current_scale
        half_height *= self._current_scale
        
        if vec.x < 0:
            half_width = -half_width
        if vec.y < 0:
            half_height = -half_height
        
        #vector is vertical => m is infinity
        if vec.x == 0:
            return Vec2(t.position.x, t.position.y + half_height)
        
        m = vec.y/vec.x
        if abs(m) <= abs(half_height/half_width):
            #Test vertical side:
            x = half_width
            y = m*x #x0 = y0 = b0 = 0
            return t.position + Vec2(x, y)
        
        #Test horizontal side:
        y = half_height
        x = y/m #x0 = y0 = b0 = 0 
        return t.position + Vec2(x, y)
    
    def _popup_menu(self, event):
        """Determines whether the event ocurred over an existing item and which one to
            pop up the correct menu."""
        if self._state != 'normal':
            return
        
        item = self._get_current_item(event)
        
        self._last_point = Vec2(event.x, event.y)
        self._popped_up_menu = self._canvas_menu
        if item:
            tags = self.gettags(item)
            self._last_clicked_id = item
            if 'place' in tags:
                self._popped_up_menu = self._place_menu
            elif 'transition' in tags:
                self._popped_up_menu = self._transition_menu
            elif 'arc' in tags:
                self._popped_up_menu = self._arc_menu
        
        self._popped_up_menu.post(event.x_root, event.y_root)
    
    def _hide_menu(self):
        """Hides a popped-up menu."""
        if self._popped_up_menu:
            self._popped_up_menu.unpost()
            self._popped_up_menu = None
            return True
        return False
    
    def _scale_up(self, event):
        """Callback for the wheel-scroll to scale the canvas elements to look like a zoom-in."""
        
        if self._state != 'normal':
            return
        
        e = Vec2(event.x, event.y)
        scale_factor = 1.11111111
        self.scale('all', e.x, e.y, scale_factor, scale_factor)
        self._current_scale = round(self._current_scale * scale_factor, 8)
        self._petri_net.scale = self._current_scale
        for p in self._petri_net.places.itervalues():
            p.position = e + (p.position - e)*scale_factor
        for t in self._petri_net.transitions.itervalues():
            t.position = e + (t.position - e)*scale_factor
        self._draw_all_arcs()
        if self._grid:
            self._grid_offset = (e + (self._grid_offset - e)*scale_factor).int
            self._draw_grid()
    
    def _scale_down(self, event):
        """Callback for the wheel-scroll to scale the canvas elements to look like a zoom-out."""
        
        if self._state != 'normal':
            return
        
        e = Vec2(event.x, event.y)
        scale_factor = 0.9
        self.scale('all', e.x, e.y, scale_factor, scale_factor)
        self._current_scale = round(self._current_scale * scale_factor, 8)
        self._petri_net.scale = self._current_scale
        for p in self._petri_net.places.itervalues():
            p.position = e + (p.position - e)*scale_factor
        for t in self._petri_net.transitions.itervalues():
            t.position = e + (t.position - e)*scale_factor
        self._draw_all_arcs()
        if self._grid:
            self._grid_offset = (e + (self._grid_offset - e)*scale_factor).int
            self._draw_grid()
    
    def _scale_canvas(self, event):
        """Callback for handling the wheel-scroll event in different platforms."""
        if event.delta > 0:
            self._scale_up(event)
        else:
            self._scale_down(event)
    
    def _left_click(self, event):
        """Callback for the left-click event.
        
            It determines what to do depending
            on the current state (normal, connecting_place or connecting_transition).
        """
        
        self.focus_set()
        
        if self._hide_menu():
            return
        
        if self._state == 'normal':
            self._set_anchor(event)
            return
        
        if self._state == 'connecting_place':
            self._state = 'normal'
            self.itemconfig('place', state = Tkinter.NORMAL)
            self.itemconfig('transition&&' + TransitionTypes.IMMEDIATE + '&&!label', outline = PetriNet.TRANSITION_CONFIG[TransitionTypes.IMMEDIATE]['outline'], width = PetriNet.LINE_WIDTH)
            self.itemconfig('transition&&' + TransitionTypes.TIMED_STOCHASTIC + '&&!label', outline = PetriNet.TRANSITION_CONFIG[TransitionTypes.TIMED_STOCHASTIC]['outline'], width = PetriNet.LINE_WIDTH)
            self.unbind('<Motion>', self._connecting_place_fn_id)
            self.delete('connecting')
            item = self._get_current_item(event)
        
            if item and 'transition' in self.gettags(item):
                name = self._get_transition_name(item)
                target = self._petri_net.transitions[name]
                self.add_arc(self._source, target)
            return
        
        if self._state == 'connecting_transition':
            self._state = 'normal'
            self.itemconfig('transition', state = Tkinter.NORMAL)
            self.itemconfig('place&&' + PlaceTypes.ACTION + '&&!label&&!token', outline = PetriNet.PLACE_CONFIG[PlaceTypes.ACTION]['outline'], width = PetriNet.LINE_WIDTH)
            self.itemconfig('place&&' + PlaceTypes.PREDICATE + '&&!label&&!token', outline = PetriNet.PLACE_CONFIG[PlaceTypes.PREDICATE]['outline'], width = PetriNet.LINE_WIDTH)
            self.itemconfig('place&&' + PlaceTypes.TASK + '&&!label&&!token', outline = PetriNet.PLACE_CONFIG[PlaceTypes.TASK]['outline'], width = PetriNet.LINE_WIDTH)
            self.unbind('<Motion>', self._connecting_transition_fn_id)
            self.delete('connecting')
            item = self._get_current_item(event)
        
            if item and 'place' in self.gettags(item):
                name = self._get_place_name(item)
                target = self._petri_net.places[name]
                self.add_arc(self._source, target)
            return
        
    
    def _set_anchor(self, event):
        """When in "normal" mode (see _left_click), determines whether a movable element or the
            canvas "background" was clicked, to either move the element or pan
            the work area.
        """
        self._anchor_tag = 'all';
        self._last_point = Vec2(event.x, event.y)
        self._anchor_set = True
        self.config(cursor = 'fleur')
        
        item = self._get_current_item(event)
        
        if not item:
            return
            
        currentTags = self.gettags(item)
        
        if 'place' in currentTags:
            for t in currentTags:
                if t[:2] == 'p_':
                    self._anchor_tag = t
                    break
        elif 'transition' in currentTags:
            for t in currentTags:
                if t[:2] == 't_':
                    self._anchor_tag = t
                    break
        
    
    def _dragCallback(self, event):
        """<B1-Motion> callback for moving an element or panning the work area."""
        if not self._anchor_set:
            return
        
        e = Vec2(event.x, event.y)
        
        dif = e - self._last_point
        self.move(self._anchor_tag, dif.x, dif.y)
        if self._anchor_tag != 'all':
            name = ''
            item_dict = self._petri_net.places
            item = self.find_withtag(self._anchor_tag)[0]
            for t in self.gettags(item):
                if t[:6] == 'place_':
                    name = t[6:]
                    break
                elif t[:11] == 'transition_':
                    name = t[11:]
                    item_dict = self._petri_net.transitions
                    break
            if name != '':
                item_dict[name].position += dif
                self._draw_item_arcs(item_dict[name])
        
        if self._anchor_tag == 'all':
            for p in self._petri_net.places.itervalues():
                p.position += dif
            for t in self._petri_net.transitions.itervalues():
                t.position += dif
            #self._draw_all_arcs()
            if self._grid:
                self._grid_offset = (self._grid_offset + dif).int
                self._draw_grid()
                
        self._last_point = Vec2(event.x, event.y)
        
        
    def _change_cursor_back(self, event):
        """Callback for when the left click is released after panning or moving an item."""
        self.config(cursor = 'arrow')
        self._anchor_set = False