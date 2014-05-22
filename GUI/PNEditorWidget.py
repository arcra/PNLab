# -*- coding: utf-8 -*-
'''
@author: Adrián Revuelta Cuauhtli
'''

import re
import math
import Tkinter
import tkMessageBox

from PetriNets import Place, PlaceTypes, Vec2, Transition, TransitionTypes, PetriNet

class PNEditor(Tkinter.Canvas):
    
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
    
    TRANSITION_HALF_LARGE = 40
    TRANSITION_HALF_SMALL = 7.5
    TRANSITION_HORIZONTAL_LABEL_PADDING = TRANSITION_HALF_SMALL + 10
    TRANSITION_VERTICAL_LABEL_PADDING = TRANSITION_HALF_LARGE + 10 
    
    TASK_PLACE_FILL = '#CCCC00'
    TASK_PLACE_OUTLINE = '#888800'
    TASK_PLACE_REGEX = re.compile('^t\.[A-Za-z][A-Za-z0-9_-]*$')
    
    def __init__(self, parent, *args, **kwargs):
        
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
        
        self._canvas_menu = Tkinter.Menu(self, tearoff=0)
        self._canvas_menu.add_command(label = 'Add Action Place', command = self._create_action_place)
        self._canvas_menu.add_command(label = 'Add Predicate Place', command = self._create_predicate_place)
        self._canvas_menu.add_command(label = 'Add Task Place', command = self._create_task_place)
        self._canvas_menu.add_separator()
        self._canvas_menu.add_command(label = 'Add Immediate Transition')
        self._canvas_menu.add_command(label = 'Add Stochastic Transition')
        
        self._place_count = 0
        self._transition_count = 0
        
        self._last_point = Vec2()
        
        self._anchor_tag = 'all'
        self._anchor_set = False
        
        self._popped_up_menu = None
        
        self._current_grid_size = PNEditor.GRID_SIZE
        
        self._place_menu = Tkinter.Menu(self, tearoff=0)
        self._place_menu.add_command(label = 'Rename')
        self._place_menu.add_separator()
        self._place_menu.add_command(label = 'Set Marking')
        
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
            self.bind('<2>', self._popup_canvas_menu)
            self.bind('<Control-1>', self._popup_canvas_menu)
        #Windows / UNIX / Linux:
        else:
            self.bind('<3>', self._popup_canvas_menu )
    
    @property
    def petri_net(self):
        return self._petri_net
    
    def set_petri_net(self, newPN):
        self._petri_net = newPN
        self._draw_petri_net()
    
    def add_place(self, p, overwrite = False):
        if self._petri_net.add_place(p, overwrite):
            self._draw_place(p)
    
    def add_transition(self, t, overwrite = False):
        if self._petri_net.add_transition(t, overwrite):
            self._draw_transition(transition = t)
    
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
    
    def _create_action_place(self):
        
        item = self._draw_generic_place(self._last_point)
        
        #type_specific code:
        self._config_action_place(item)
        p = Place('P' + '%02d' % self._place_count, PlaceTypes.ACTION, self._last_point)
        self.addtag_withtag('place_' + str(p), item)
        regex = PNEditor.ACTION_PLACE_REGEX
        
        self._set_label_entry(item, regex, p)
    
    def _create_predicate_place(self):
        
        item = self._draw_generic_place(self._last_point)
        
        #type_specific code:
        self._config_predicate_place(item)
        p = Place('P' + '%02d' % self._place_count, PlaceTypes.PREDICATE, self._last_point)
        self.addtag_withtag('place_' + str(p), item)
        regex = PNEditor.PREDICATE_PLACE_REGEX
        
        self._set_label_entry(item, regex, p)
    
    def _create_task_place(self):
        
        item = self._draw_generic_place(self._last_point)
        
        #type_specific code:
        self._config_task_place(item)
        p = Place('P' + '%02d' % self._place_count, PlaceTypes.TASK, self._last_point)
        self.addtag_withtag('place_' + str(p), item)
        regex = PNEditor.TASK_PLACE_REGEX
        
        self._set_label_entry(item, regex, p)
        
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
            else:
                if obj.isHorizontal:
                    label_padding = PNEditor.TRANSITION_HORIZONTAL_LABEL_PADDING
                else:
                    label_padding = PNEditor.TRANSITION_VERTICAL_LABEL_PADDING
                if not self._petri_net.add_transition(newObj):
                    tkMessageBox.showerror('Insertion failed', 'Failed to add transition to the Petri Net.')
                    return
            
            self.create_text(newObj.position.x, newObj.position.y + label_padding*self._current_scale, text = str(newObj), tags=tags)
            txtbox.destroy()
        return txtboxCallback
    
    def _draw_transition(self, t):
        trans_id = self._create_transition(transition = t)
        
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
    
    def _create_transition(self, x = 0, y = 0, transition = None):
        self._hide_menu()
        
        transition_tag = ''
        if transition:
            x = transition.position.x
            y = transition.position.y
            transition_tag = 'transition_' + str(transition)
        
        x0 = x - PNEditor.TRANSITION_HALF_LARGE
        y0 = y - PNEditor.TRANSITION_HALF_SMALL
        x1 = x + PNEditor.TRANSITION_HALF_LARGE
        y1 = y + PNEditor.TRANSITION_HALF_SMALL
        
        if not transition.isHorizontal:
            x0 = x - PNEditor.TRANSITION_HALF_SMALL
            y0 = y - PNEditor.TRANSITION_HALF_LARGE
            x1 = x + PNEditor.TRANSITION_HALF_SMALL
            y1 = y + PNEditor.TRANSITION_HALF_LARGE
        
        fill = 'white' if transition.type == TransitionTypes.TIMED_STOCHASTIC else PNEditor.GENERIC_COLOR
        
        item = self.create_rectangle(x0, y0, x1, y1,
                         tags = ('transition', transition_tag),
                         width = PNEditor.LINE_WIDTH,
                         fill = fill,
                         outline = PNEditor.GENERIC_COLOR)
        
        self.addtag_withtag('t_' + str(item), item)
        self.scale(item, x, y, self._current_scale, self._current_scale)
        self._transition_count += 1
        return item
    
    def _draw_arc(self, source, target, weight = 1):
        if not self._petri_net.is_arc(source, target):
            print 'Arcs should go either from a place to a transition or vice versa and they should exist in the PN.'
        
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
        
        arrow_vec = src_point - trgt_point
        
        p0, p1 = self._get_arrow_points(trgt_point, arrow_vec)
        tags = ('arc', 'source_' + str(source), 'target_' + str(target))
        
        self.create_line(src_point.x,
                         src_point.y,
                         trgt_point.x,
                         trgt_point.y,
                         tags = tags,
                         width = PNEditor.LINE_WIDTH
                         )
        
        self.create_line(trgt_point.x,
                         trgt_point.y,
                         p0.x,
                         p0.y,
                         tags = tags,
                         width = PNEditor.LINE_WIDTH
                         )
        
        self.create_line(trgt_point.x,
                         trgt_point.y,
                         p1.x,
                         p1.y,
                         tags = tags,
                         width = PNEditor.LINE_WIDTH
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
    
    def _get_arrow_points(self, p, vec):
        
        base_vec = vec.unit*PNEditor.ARROW_SIZE #*self._current_scale
        #From the 2D rotation matrix:
        sin_ang = math.sin(PNEditor.ARROW_ANGLE*math.pi/180)
        cos_ang = math.cos(PNEditor.ARROW_ANGLE*math.pi/180)
        rotated_vec = Vec2(base_vec.x*cos_ang - base_vec.y*sin_ang, sin_ang*base_vec.x + cos_ang*base_vec.y)  
        p0 = p + rotated_vec
        rotated_vec = Vec2(base_vec.x*cos_ang + base_vec.y*sin_ang, -sin_ang*base_vec.x + cos_ang*base_vec.y)
        p1 = p + rotated_vec
        
        return (p0, p1)
    
    def _popup_canvas_menu(self, event):
        self._last_point = Vec2(event.x, event.y)
        self._canvas_menu.post(event.x_root, event.y_root)
        self._popped_up_menu = self._canvas_menu
    
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
            arc_dict = self._petri_net.transitions
            item = self.find_withtag(self._anchor_tag)[0]
            for t in self.gettags(item):
                if t[:6] == 'place_':
                    name = t[6:]
                    break
                elif t[:11] == 'transition_':
                    name = t[11:]
                    item_dict = self._petri_net.transitions
                    arc_dict = self._petri_net.places
                    break
            if name != '':
                item_dict[name].position += dif #/self._current_scale
                self.delete('source_' + name)
                self.delete('target_' + name)
                target = item_dict[name]
                for arc in item_dict[name].incoming_arcs.iterkeys():
                    source = arc_dict[arc]
                    self._draw_arc(source, target)
                source = item_dict[name]
                for arc in item_dict[name].outgoing_arcs.iterkeys():
                    target = arc_dict[arc]
                    self._draw_arc(source, target)
        
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

if __name__ == '__main__':
    root = Tkinter.Tk()
    
    PN = PetriNet(name = 'test')
    p1 = Place('myAction', PlaceTypes.ACTION, Vec2(150, 250))
    t = Transition('transition1', TransitionTypes.IMMEDIATE, Vec2(250, 250),False)
    p2 = Place('result', PlaceTypes.PREDICATE, Vec2(500, 250))
    PN.add_place(p1)
    PN.add_place(p2)
    PN.add_transition(t)
    PN.add_arc(p1, t)
    PN.add_arc(t, p2)
    
    pne = PNEditor(root, width=600, height=400, grid = True, PetriNet = PN)
    pne.grid({'row': 0, 'column': 0})
    
    btn = Tkinter.Button(root, )
    
    Tkinter.mainloop()