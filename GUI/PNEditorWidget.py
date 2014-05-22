# -*- coding: utf-8 -*-
"""
@author: Adrián Revuelta Cuauhtli
"""

import re
import Tkinter
import tkMessageBox

from PetriNets import Place, PlaceTypes, Vec2, Transition, TransitionTypes, PetriNet

class PNEditor(Tkinter.Canvas):
    
    """
    Tk widget for editing Petri Net diagrams.
    
    Subclass of the Tkinter.Canvas Widget class. Handles several GUI interactions
    and provides some basic API methods to edit the Petri Net without the GUI events.
    """
    
    GRID_SIZE = 100
    GRID_SIZE_FACTOR = 3
    LINE_WIDTH = 2.0
    ARROW_SIZE = 13
    ARROW_ANGLE = 40
    
    GENERIC_COLOR = '#777777'
    
    PLACE_RADIUS = 25
    PLACE_LABEL_PADDING = PLACE_RADIUS + 10
    
    ACTION_PLACE_FILL = '#00CC00'
    ACTION_PLACE_OUTLINE = '#008800'
    ACTION_PLACE_REGEX = re.compile('^a\.[A-Za-z][A-Za-z0-9_-]*$')
    
    PREDICATE_PLACE_FILL = '#0000CC'
    PREDICATE_PLACE_OUTLINE = '#000088'
    PREDICATE_PLACE_REGEX = re.compile('^p\.[A-Za-z][A-Za-z0-9_-]*$')
    
    TASK_PLACE_FILL = '#CCCC00'
    TASK_PLACE_OUTLINE = '#888800'
    TASK_PLACE_REGEX = re.compile('^t\.[A-Za-z][A-Za-z0-9_-]*$')
    
    TRANSITION_HALF_LARGE = 40
    TRANSITION_HALF_SMALL = 7.5
    TRANSITION_HORIZONTAL_LABEL_PADDING = TRANSITION_HALF_SMALL + 10
    TRANSITION_VERTICAL_LABEL_PADDING = TRANSITION_HALF_LARGE + 10
    
    IMMEDIATE_TRANSITION_FILL = '#888888'
    IMMEDIATE_TRANSITION_OUTLINE = '#888888'
    IMMEDIATE_TRANSITION_REGEX = re.compile('^i\.[A-Za-z][A-Za-z0-9_-]*$')
    
    STOCHASTIC_TRANSITION_FILL = '#FFFFFF'
    STOCHASTIC_TRANSITION_OUTLINE = '#888888'
    STOCHASTIC_TRANSITION_REGEX = re.compile('^s\.[A-Za-z][A-Za-z0-9_-]*$')
    
    def __init__(self, parent, *args, **kwargs):
        """
        PNEditor Class' constructor.
        
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
        self._petri_net = kwargs.pop('PetriNet', None)
        petri_net_name = kwargs.pop('name', None)
        
        if not (petri_net_name or self._petri_net):
            raise Exception('Either a PetriNet object or a name must be passed to the Petri Net Editor.')
        
        if not self._petri_net:
            self._petri_net = PetriNet(petri_net_name)
        
        Tkinter.Canvas.__init__(self, *args, **kwargs)
        
        self._canvas_menu = Tkinter.Menu(self, tearoff = 0)
        self._canvas_menu.add_command(label = 'Add Action Place', command = self._create_action_place)
        self._canvas_menu.add_command(label = 'Add Predicate Place', command = self._create_predicate_place)
        self._canvas_menu.add_command(label = 'Add Task Place', command = self._create_task_place)
        self._canvas_menu.add_separator()
        self._canvas_menu.add_command(label = 'Add Immediate Transition', command = self._create_immediate_transition)
        self._canvas_menu.add_command(label = 'Add Stochastic Transition', command = self._create_stochastic_transition)
        
        self._place_menu = Tkinter.Menu(self, tearoff = 0)
        self._place_menu.add_command(label = 'Remove Place')
        self._place_menu.add_command(label = 'Rename Place')
        self._place_menu.add_command(label = 'Set Initial Marking')
        self._place_menu.add_command(label = 'Connect to...')
        
        self._transition_menu = Tkinter.Menu(self, tearoff = 0)
        self._transition_menu.add_command(label = 'Switch orientation', command = self._switch_orientation)
        self._transition_menu.add_command(label = 'Remove Transition')
        self._transition_menu.add_command(label = 'Rename Transition')
        self._transition_menu.add_command(label = 'Connect to...')
        
        
        self._place_count = 0
        self._transition_count = 0
        
        self._last_point = Vec2()
        
        self._anchor_tag = 'all'
        self._anchor_set = False
        
        self._popped_up_menu = None
        
        self._current_grid_size = PNEditor.GRID_SIZE
        
        self._draw_petri_net()
        
        ################################
        #        EVENT BINDINGs
        ################################
        self.bind('<Button-1>', self._set_anchor)
        self.bind('<B1-Motion>', self._dragCallback)
        self.bind('<ButtonRelease-1>', self._change_cursor_back)
        #Windows and MAC OS:
        self.bind('<MouseWheel>', self._scale_canvas)
        #UNIX/Linux:
        self.bind('<Button-4>', self._scale_up)
        self.bind('<Button-5>', self._scale_down)
        
        self.bind('<KeyPress-c>', self._center_diagram)
        
        #MAC OS:
        if (self.tk.call('tk', 'windowingsystem')=='aqua'):
            self.bind('<2>', self._popup_menu)
            self.bind('<Control-1>', self._popup_menu)
        #Windows / UNIX / Linux:
        else:
            self.bind('<3>', self._popup_menu)
    
    @property
    def petri_net(self):
        return self._petri_net
    
    def set_petri_net(self, newPN):
        """Loads a new Petri Net object to be viewed/edited."""
        
        '''
        #TODO (Possibly):
        Check PetriNet saved attribute, before changing the Petri Net
        or destroying the widget.
        '''
        
        self._petri_net = newPN
        self._draw_petri_net()
    
    def add_place(self, p, overwrite = False):
        """Adds a place to the Petri Net and draws it.
        
        Note that it uses the PetriNet Class' instance method
        for adding the place and so it will remove any arc information
        it contains for the sake of maintaining consistency. 
        """
        
        if self._petri_net.add_place(p, overwrite):
            self._draw_place(p)
    
    def add_transition(self, t, overwrite = False):
        """Adds a transition to the Petri Net and draws it.
        
        Note that it uses the PetriNet Class' instance method
        for adding the transition and so it will remove any arc information
        it contains for the sake of maintaining consistency.
        """
        
        if self._petri_net.add_transition(t, overwrite):
            self._draw_transition(t)
    
    def add_arc(self, source, target, weight = 1):
        self._petri_net.add_arc(source, target, weight)
        self._draw_arc(source, target, weight)
    
    def _draw_petri_net(self):
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
        minx = 100000
        maxx = -100000
        miny = 100000
        maxy = -100000
        
        padding = PNEditor.TRANSITION_HALF_LARGE * 2 * self._current_scale
        
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
        offset = -Vec2(minx, miny)
        canvas_width = int(self.config()['width'][4])
        canvas_height = int(self.config()['height'][4])
        
        if w > h:
            scale_factor = canvas_width/w
        else:
            scale_factor = canvas_height/h
        
        for p in self._petri_net.places.itervalues():
            p.position = (p.position + offset)*scale_factor
        
        for t in self._petri_net.transitions.itervalues():
            t.position = (t.position + offset)*scale_factor
        
        self._current_scale *= scale_factor
        self._petri_net.scale = self._current_scale
        
        self._draw_petri_net()
    
    def _draw_grid(self):
        
        self.delete('grid')
        
        if not self._grid:
            return
        
        if self._current_grid_size * self._current_scale <= PNEditor.GRID_SIZE / PNEditor.GRID_SIZE_FACTOR:
            self._current_grid_size = self._current_grid_size * PNEditor.GRID_SIZE_FACTOR
        
        if self._current_grid_size / PNEditor.GRID_SIZE_FACTOR * self._current_scale >= PNEditor.GRID_SIZE:
            self._current_grid_size = int(self._current_grid_size / PNEditor.GRID_SIZE_FACTOR)
        
        conf = self.config()
        width = int(conf['width'][4])
        height = int(conf['height'][4])
        
        startx = int(self._grid_offset.x - self._current_grid_size * self._current_scale)
        step = int(self._current_grid_size * self._current_scale / PNEditor.GRID_SIZE_FACTOR)
        
        for x in xrange(startx, width, step):
            self.create_line(x, 0, x, height, fill = '#BBBBFF', tags='grid')
        
        starty = int(self._grid_offset.y - self._current_grid_size * self._current_scale)
        for y in xrange(starty, height, step):
            self.create_line(0, y, width, y, fill = '#BBBBFF', tags='grid')
        
        step *= PNEditor.GRID_SIZE_FACTOR
        
        for x in xrange(startx, width, step):
            self.create_line(x, 0, x, height, fill = '#7777FF', width = 1.4, tags='grid')
        
        for y in xrange(starty, height, step):
            self.create_line(0, y, width, y, fill = '#7777FF', width = 1.4, tags='grid')
            
        self.tag_lower('grid')
    
    def _adjust_grid_offset(self):
        currentGridSize = int(self._current_grid_size * self._current_scale)
        while self._grid_offset.x < 0:
            self._grid_offset.x += currentGridSize
        while self._grid_offset.x > currentGridSize:
            self._grid_offset.x -= currentGridSize
            
        while self._grid_offset.y < 0:
            self._grid_offset.y += currentGridSize
        while self._grid_offset.y > currentGridSize:
            self._grid_offset.y -= currentGridSize
    
    def _draw_all_arcs(self):
        
        self.delete('arc')
        
        for p in self._petri_net.places.itervalues():
            target = p
            for arc in p.incoming_arcs.iterkeys():
                source = self._petri_net.transitions[arc]
                self._draw_arc(source, target)
            source = p
            for arc in p.outgoing_arcs.iterkeys():
                target = self._petri_net.transitions[arc]
                self._draw_arc(source, target)
    
    def _draw_item_arcs(self, obj):
        
        arc_dict = self._petri_net.transitions
        if isinstance(obj, Transition):
            arc_dict = self._petri_net.places
        
        self.delete('source_' + str(obj))
        self.delete('target_' + str(obj))
        target = obj
        for arc in obj.incoming_arcs.iterkeys():
            source = arc_dict[arc]
            self._draw_arc(source, target)
        source = obj
        for arc in obj.outgoing_arcs.iterkeys():
            target = arc_dict[arc]
            self._draw_arc(source, target)
    
    def _draw_place(self, p):
        place_id = self._draw_generic_place(place = p)
        if p.type == PlaceTypes.ACTION:
            self._config_action_place(place_id)
        elif p.type == PlaceTypes.PREDICATE:
            self._config_predicate_place(place_id)
        elif p.type == PlaceTypes.TASK:
            self._config_task_place(place_id)
        
        self.create_text(p.position.x,
                       p.position.y + PNEditor.PLACE_LABEL_PADDING*self._current_scale,
                       tags = ('label', 'place_' + str(p)) + self.gettags(place_id),
                       text = str(p)
                       )
        
        return place_id
    
    def _create_action_place(self):
        
        item = self._draw_generic_place(self._last_point)
        
        #type_specific code:
        self._config_action_place(item)
        p = Place('p' + '%02d' % self._place_count, PlaceTypes.ACTION, self._last_point)
        regex = PNEditor.ACTION_PLACE_REGEX
        
        self._set_label_entry(item, regex, p)
    
    def _create_predicate_place(self):
        
        item = self._draw_generic_place(self._last_point)
        
        #type_specific code:
        self._config_predicate_place(item)
        p = Place('p' + '%02d' % self._place_count, PlaceTypes.PREDICATE, self._last_point)
        regex = PNEditor.PREDICATE_PLACE_REGEX
        
        self._set_label_entry(item, regex, p)
    
    def _create_task_place(self):
        
        item = self._draw_generic_place(self._last_point)
        
        #type_specific code:
        self._config_task_place(item)
        p = Place('p' + '%02d' % self._place_count, PlaceTypes.TASK, self._last_point)
        regex = PNEditor.TASK_PLACE_REGEX
        
        self._set_label_entry(item, regex, p)
    
    def _draw_generic_place(self, point = Vec2(), place = None):
        self._hide_menu()
        place_tag = ''
        if place:
            point = place.position
            place_tag = 'place_' + str(place)
            
        
        item = self.create_oval(point.x - PNEditor.PLACE_RADIUS,
                         point.y - PNEditor.PLACE_RADIUS,
                         point.x + PNEditor.PLACE_RADIUS,
                         point.y + PNEditor.PLACE_RADIUS,
                         tags = ('place', place_tag),
                         width = PNEditor.LINE_WIDTH,
                         fill = 'white',
                         outline = PNEditor.GENERIC_COLOR)
        self.addtag_withtag('p_' + str(item), item)
        self.scale(item, point.x, point.y, self._current_scale, self._current_scale)
        self._place_count += 1
        return item
    
    def _config_action_place(self, item):
        self.itemconfig(item,
                        fill = PNEditor.ACTION_PLACE_FILL,
                        outline = PNEditor.ACTION_PLACE_OUTLINE)
        self.addtag_withtag('action', item)
    
    def _config_predicate_place(self, item):
        self.itemconfig(item,
                        fill = PNEditor.PREDICATE_PLACE_FILL,
                        outline = PNEditor.PREDICATE_PLACE_OUTLINE)
        self.addtag_withtag('predicate', item)
    
    def _config_task_place(self, item):
        self.itemconfig(item,
                        fill = PNEditor.TASK_PLACE_FILL,
                        outline = PNEditor.TASK_PLACE_OUTLINE)
        self.addtag_withtag('task', item)
    
    def _draw_transition(self, t):
        trans_id = self._draw_generic_transition(transition = t)
        
        if t.type == TransitionTypes.IMMEDIATE:
            self._config_immediate_transition(trans_id)
        else:
            self._config_stochastic_transition(trans_id)
        
        if t.isHorizontal:
            padding = PNEditor.TRANSITION_HORIZONTAL_LABEL_PADDING
        else:
            padding = PNEditor.TRANSITION_VERTICAL_LABEL_PADDING
        
        self.create_text(t.position.x,
                       t.position.y + padding*self._current_scale,
                       tags = ('label', 'transition_' + str(t)) + self.gettags(trans_id),
                       text = str(t)
                       )
        
        return trans_id
    
    def _draw_generic_transition(self, point = Vec2(), transition = None):
        self._hide_menu()
        
        transition_tag = ''
        if transition:
            point = transition.position
            transition_tag = 'transition_' + str(transition)
        
        x0 = point.x - PNEditor.TRANSITION_HALF_SMALL
        y0 = point.y - PNEditor.TRANSITION_HALF_LARGE
        x1 = point.x + PNEditor.TRANSITION_HALF_SMALL
        y1 = point.y + PNEditor.TRANSITION_HALF_LARGE
        
        if transition and transition.isHorizontal:
            x0 = point.x - PNEditor.TRANSITION_HALF_LARGE
            y0 = point.y - PNEditor.TRANSITION_HALF_SMALL
            x1 = point.x + PNEditor.TRANSITION_HALF_LARGE
            y1 = point.y + PNEditor.TRANSITION_HALF_SMALL
        
        item = self.create_rectangle(x0, y0, x1, y1,
                         tags = ('transition', transition_tag),
                         width = PNEditor.LINE_WIDTH,
                         fill = 'white',
                         outline = PNEditor.GENERIC_COLOR)
        
        self.addtag_withtag('t_' + str(item), item)
        self.scale(item, point.x, point.y, self._current_scale, self._current_scale)
        self._transition_count += 1
        return item
    
    def _config_immediate_transition(self, item):
        self.itemconfig(item,
                        fill = PNEditor.IMMEDIATE_TRANSITION_FILL,
                        outline = PNEditor.IMMEDIATE_TRANSITION_OUTLINE)
        self.addtag_withtag('immediate', item)
    
    def _config_stochastic_transition(self, item):
        self.itemconfig(item,
                        fill = PNEditor.STOCHASTIC_TRANSITION_FILL,
                        outline = PNEditor.STOCHASTIC_TRANSITION_OUTLINE)
        self.addtag_withtag('stochastic', item)
    
    def _create_immediate_transition(self):
        
        item = self._draw_generic_transition(self._last_point)
        
        #type_specific code:
        self._config_immediate_transition(item)
        t = Transition('t' + '%02d' % self._transition_count, TransitionTypes.IMMEDIATE, self._last_point)
        regex = PNEditor.IMMEDIATE_TRANSITION_REGEX
        
        self._set_label_entry(item, regex, t)
    
    def _create_stochastic_transition(self):
        
        item = self._draw_generic_transition(self._last_point)
        
        #type_specific code:
        self._config_stochastic_transition(item)
        t = Transition('t' + '%02d' % self._transition_count, TransitionTypes.TIMED_STOCHASTIC, self._last_point)
        regex = PNEditor.STOCHASTIC_TRANSITION_REGEX
        
        self._set_label_entry(item, regex, t)
    
    def _switch_orientation(self):
        
        tags = self.gettags(self._last_clicked)
        
        if 'transition' not in tags:
            return
        
        for t in tags:
            if t[:11] == 'transition_':
                name = t[11:]
                break
        
        t = self._petri_net.transitions[name]
        t.isHorizontal = not t.isHorizontal
        
        self.delete('source_' + name)
        self.delete('target_' + name)
        self.delete('transition_' + name)
        
        self._draw_transition(t)
        self._draw_item_arcs(t)
        
        
        
    
    def _set_label_entry(self, canvas_id, regex, obj):
        
        txtbox = Tkinter.Entry(self)
        txtbox.insert(0, str(obj))
        
        #extra padding because entry position refers to the center, not the corner
        if isinstance(obj, Place):
            label_padding = PNEditor.PLACE_LABEL_PADDING + 10
        else:
            if obj.isHorizontal:
                label_padding = PNEditor.TRANSITION_HORIZONTAL_LABEL_PADDING + 10
            else:
                label_padding = PNEditor.TRANSITION_VERTICAL_LABEL_PADDING + 10
        
        self.create_window(obj.position.x, obj.position.y + label_padding*self._current_scale, height= 20, width = 60, window = txtbox)
        txtbox.grab_set()
        txtbox.focus_set()
        
        callback = self._get_txtbox_callback(txtbox, canvas_id, regex, obj, ('label',) + self.gettags(canvas_id))
        
        txtbox.bind('<KeyPress-Return>', callback)
    
    def _get_txtbox_callback(self, txtbox, canvas_id, regex, obj, tags):
        
        isPlace = isinstance(obj, Place)
        def txtboxCallback(event):
            txt = txtbox.get()
            if not regex.match(txt):
                if isPlace:
                    msg = ('A place name must begin with the first letter of its type and a dot, ' +
                    'followed by an alphabetic character and then any number of ' +
                    'alphanumeric characters, dashes or underscores. \
                     \
                    Examples: a.my_Action, t.task1')
                else:
                    msg = ("A transition name must begin with an 'i' and a dot if it's an immediate transition " +
                           "or an 's' and a dot if it's a timed_stochastic transition, " + 
                           "followed by an alphabetic character and then any number of " +
                           "alphanumeric characters, dashes or underscores. \
                           \
                           Example: i.transition1, s.t-2")
                tkMessageBox.showerror('Invalid Name', msg)
                return
            if isPlace:
                if txt in self._petri_net.places:
                    tkMessageBox.showerror('Duplicate name', 'A place of the same type with that name already exists in the Petri Net.')
                    return
            else:
                if txt in self._petri_net.transitions:
                    tkMessageBox.showerror('Duplicate name', 'A transition with that name already exists in the Petri Net.')
                    return
            newObj = obj.__class__(txt[2:], obj.type, obj.position)
            if isPlace:
                label_padding = PNEditor.PLACE_LABEL_PADDING
                if not self._petri_net.add_place(newObj):
                    tkMessageBox.showerror('Insertion failed', 'Failed to add place to the Petri Net.')
                    return
                self.addtag_withtag('place_' + str(newObj), canvas_id)
            else:
                if obj.isHorizontal:
                    label_padding = PNEditor.TRANSITION_HORIZONTAL_LABEL_PADDING
                else:
                    label_padding = PNEditor.TRANSITION_VERTICAL_LABEL_PADDING
                if not self._petri_net.add_transition(newObj):
                    tkMessageBox.showerror('Insertion failed', 'Failed to add transition to the Petri Net.')
                    return
                self.addtag_withtag('transition_' + str(newObj), canvas_id)
            
            self.create_text(newObj.position.x, newObj.position.y + label_padding*self._current_scale, text = str(newObj), tags=tags)
            txtbox.destroy()
        return txtboxCallback
    
    def _draw_arc(self, source, target, weight = 1):
        
        if isinstance(source, Place):
            p = source
            t = target
        else:
            p = target
            t = source
        
        place_vec = t.position - p.position
        trans_vec = -place_vec
        place_point = p.position + place_vec.unit*PNEditor.PLACE_RADIUS*self._current_scale
        transition_point = self._find_intersection(t, trans_vec)
        
        if isinstance(source, Place):
            src_point = place_point
            trgt_point = transition_point
        else:
            src_point = transition_point
            trgt_point = place_point
        
        tags = ('arc', 'source_' + str(source), 'target_' + str(target))
        
        self.create_line(src_point.x,
                         src_point.y,
                         trgt_point.x,
                         trgt_point.y,
                         tags = tags,
                         width = PNEditor.LINE_WIDTH,
                         arrow= Tkinter.LAST,
                         arrowshape = (10,12,5)
                         )
        
        
    def _find_intersection(self, t, vec):
        #NOTE: vec is a vector from the transition's center
        
        if t.isHorizontal:
            half_width = PNEditor.TRANSITION_HALF_LARGE
            half_height = PNEditor.TRANSITION_HALF_SMALL
        else:
            half_width = PNEditor.TRANSITION_HALF_SMALL
            half_height = PNEditor.TRANSITION_HALF_LARGE
        
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
        
        ids = self.find_withtag('current')
        
        self._last_point = Vec2(event.x, event.y)
        self._popped_up_menu = self._canvas_menu
        if len(ids) > 0:
            tags = self.gettags(ids[0])
            self._last_clicked = ids[0]
            if 'place' in tags:
                self._popped_up_menu = self._place_menu
            elif 'transition' in tags:
                self._popped_up_menu = self._transition_menu
        
        self._popped_up_menu.post(event.x_root, event.y_root)
    
    def _hide_menu(self):
        if self._popped_up_menu:
            self._popped_up_menu.unpost()
            self._popped_up_menu = None
            return True
        return False
    
    def _scale_up(self, event):
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
            self._adjust_grid_offset()
            self._draw_grid()
    
    def _scale_down(self, event):
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
            self._adjust_grid_offset()
            self._draw_grid()
    
    def _scale_canvas(self, event):
        if event.delta > 0:
            self._scale_up(event)
        else:
            self._scale_down(event)
    
    def _set_anchor(self, event):
        
        self.focus_set()
        
        if self._hide_menu():
            return
        
        self._anchor_tag = 'all';
        currentTags = self.gettags('current')
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
        self._last_point = Vec2(event.x, event.y)
        self._anchor_set = True
        self.config(cursor = 'fleur')
    
    def _dragCallback(self, event):
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
                item_dict[name].position += dif #/self._current_scale
                self._draw_item_arcs(item_dict[name])
        
        if self._anchor_tag == 'all':
            self._draw_all_arcs()
            for p in self._petri_net.places.itervalues():
                p.position += dif
            for t in self._petri_net.transitions.itervalues():
                t.position += dif
            if self._grid:
                self._grid_offset = (self._grid_offset + dif).int
                self._adjust_grid_offset()
                self._draw_grid()
                
        self._set_anchor(event)
        
        
    def _change_cursor_back(self, event):
        self.config(cursor = 'arrow')
        self._anchor_set = False