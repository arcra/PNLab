# -*- coding: utf-8 -*-
"""
@author: Adrián Revuelta Cuauhtli
"""

import copy
import xml.etree.ElementTree as ET

from utils.Vector import Vec2

VERSION = '0.8'
 
class PlaceTypes(object):
    """'Enum' class for Place types"""
    
    ACTION = 'action'
    PREDICATE = 'predicate'
    TASK = 'task'

class TransitionTypes(object):
    """'Enum' class for Transition types"""
    IMMEDIATE = 'immediate'
    TIMED_STOCHASTIC = 'stochastic'

class Node(object):
    """PetriNets Node class, which is extended by Place and Transition Classes."""
    
    def __init__(self, name, position):
        """Node constructor
        
            Sets the name and position of a node.
            
            Positional Arguments:
            name -- Any string (preferably only alphanumeric characters, daches and underscores).
            position -- An instance of the Vec2 utility class.
            """
        
        self._name = name
        self.position = Vec2(position)
        self._incoming_arcs = {}
        self._outgoing_arcs = {}
        self.petri_net = None
        self._treeElement = None
    
    @property
    def name(self):
        """Read-only property. Name of the node, not including the type prefix."""
        return self._name
    
    @property
    def incoming_arcs(self):
        """Read-only property. Deepcopy of the incoming arcs as a dictionaty with source
            transition/place string representations as keys and weights as values. 
        """
        return copy.deepcopy(self._incoming_arcs)
    
    @property
    def outgoing_arcs(self):
        """Read-only property. Deepcopy of the outgoing arcs as a dictionaty with target
            transition/place string representations as keys and weights as values. 
        """
        return copy.deepcopy(self._outgoing_arcs)
    
    @property
    def treeElement(self):
        
        if self._treeElement:
            return self._merge_treeElement()
        
        return self._build_treeElement()
    
    def _get_treeElement(self, parent, tag = 'text', attr = None):
        el = parent.find(tag)
        if el is None:
            el = ET.SubElement(parent, tag, attr)
        return el

    def __str__(self):
        """ String representation of a Node object.
        
        It is formed with the first letter of the node type, a dot and the node name.
        """
        return self.type[0] + '.' + self.name

class Place(Node):
    """Petri Net Place Class."""
    
    def __init__(self, name, place_type = PlaceTypes.PREDICATE, position = Vec2(), init_marking = 0, capacity = None):
        """Place constructor
        
            Sets the name, type, position and initial marking of a place.
            
            Positional Arguments:
            name -- Any string (preferably only alphanumeric characters, daches and underscores).
                    
            Keyword Arguments:
            placeType -- Should be set from one of the PlaceTypes Class' class members.
            position -- An instance of the Vec2 utility class.
            initial_marking -- An integer specifying the initial marking for this place.
        """
        
        super(Place, self).__init__(name, position)
        
        self._type = place_type
        
        self.init_marking = init_marking
        self.capacity = capacity
        self.current_marking = self.init_marking
    
    @classmethod
    def fromETreeElement(cls, element):
        if element.tag != 'place':
            raise Exception('Wrong eTree seed element for place.')
        
        name = element.get('id')
        place_name = element.find('name')
        if place_name is not None:
            try:
                name = place_name.findtext('text')
            except:
                tmp = place_name.find('value')
                name = tmp.text
                if PetriNet.FIX_MALFORMED_PNML:
                    place_name.remove(tmp)
                    ET.SubElement(place_name, 'text', text = name)
        if name[1] == '.':
            name = name[2:] 
        if not name:
            raise Exception('Place name cannot be an empty string.')
        
        
        try:
            position_el = element.find('graphics').find('position')
            position = Vec2(float(position_el.get('x')), float(position_el.get('y')))
        except:
            position = Vec2()
        
        initMarking = 0
        place_initMarking = element.find('initialMarking')
        if place_initMarking is not None:
            try:
                initMarking = int(place_initMarking.findtext('text'))
            except:
                tmp = place_initMarking.find('value')
                initMarking = tmp.text
                if PetriNet.FIX_MALFORMED_PNML:
                    place_initMarking.remove(tmp)
                    ET.SubElement(place_initMarking, 'text', text = initMarking)
                initMarking = int(initMarking)
        
        toolspecific_el = element.find("toolspecific[@name='PNLab']")
        try:
            place_type = toolspecific_el.find('type').findtext('text')
            if place_type not in [PlaceTypes.ACTION, PlaceTypes.PREDICATE, PlaceTypes.TASK]:
                raise Exception('Warning: Wrong type while reading place object.')
        except:
            place_type = PlaceTypes.PREDICATE
        
        try:
            if toolspecific_el is not None:
                capacity = int(toolspecific_el.find('capacity').findtext('text'))
            else:
                place_capacity = element.find('capacity')
                capacity = int(place_capacity.findtext('value'))
                if PetriNet.FIX_MALFORMED_PNML:
                    element.remove(place_capacity)
        except:
            capacity = 0
        
        p = Place(name, type, position, initMarking, capacity)
        
        p._treeElement = element
        return p
    
    @property
    def type(self):
        """Read-only property. Type of place."""
        return self._type
    
    def _build_treeElement(self):
        
        name = self.__str__()
        place = ET.Element('place', {'id': name})
        
        place_name = ET.SubElement(place, 'name')
        ET.SubElement(place_name, 'text', text = name)
        tmp = ET.SubElement(place_name, 'graphics')
        ET.SubElement(tmp, 'offset', {'x': 0.0, 'y': PetriNet.PLACE_LABEL_PADDING})
        
        tmp = ET.SubElement(place, 'initialMarking')
        ET.SubElement(tmp, 'text', text = str(self.init_marking))
        
        place_toolspecific = ET.SubElement(place, 'toolspecific', {'tool': 'PNLab', 'version': VERSION})
        
        tmp = ET.SubElement(place_toolspecific, 'type')
        ET.SubElement(tmp, 'text', text = self._type)
        
        tmp = ET.SubElement(place_toolspecific, 'capacity')
        ET.SubElement(tmp, 'text', text = int(self.capacity))
        
        tmp = ET.SubElement(place, 'graphics')
        ET.SubElement(tmp, 'position', {'x': self.position.x, 'y': self.position.y})
        scale = 1.0
        if self.petri_net:
            scale = self.petri_net.scale
        ET.SubElement(tmp, 'dimension', {'x': PetriNet.PLACE_RADIUS*scale, 'y': PetriNet.PLACE_RADIUS*scale})
        ET.SubElement(tmp, 'fill', {'color': PetriNet.PLACE_CONFIG[self._type]['fill']})
        ET.SubElement(tmp, 'line', {
                                    'color': PetriNet.PLACE_CONFIG[self._type]['outline'],
                                    'width': PetriNet.LINE_WIDTH,
                                    'style': 'solid'})
        
        return place
    
    def _merge_treeElement(self):
        
        name = self.__str__()
        place = self._treeElement
        
        place_name = self._get_treeElement(place, 'name')
        tmp = self._get_treeElement(place_name)
        tmp.text = name
        
        if PetriNet.UPDATE_ELEMENT_ID:
            place.set('id', name)
        
        if PetriNet.UPDATE_LABEL_OFFSET:
            place_name_graphics = self._get_treeElement(place_name, 'graphics') 
            tmp = self._get_treeElement(place_name_graphics, 'offset')
            tmp.set('x', 0.0)
            tmp.set('y', PetriNet.PLACE_LABEL_PADDING)
        
        place_initMarking = self._get_treeElement(place, 'initMarking')
        tmp = self._get_treeElement(place_initMarking)
        tmp.text = str(self.init_marking)
        
        
        place_toolspecific = self._get_treeElement(place, "toolspecific[@tool='PNLab']", {'tool': 'PNLab', 'version': VERSION})
        place_type = self._get_treeElement(place_toolspecific, 'type')
        tmp = self._get_treeElement(place_type)
        tmp.text = self._type
        
        place_capacity = self._get_treeElement(place_toolspecific, 'capacity')
        tmp = self._get_treeElement(place_capacity)
        tmp.text = str(self.capacity)
        
        place_graphics = self._get_treeElement(place, 'graphics')
        tmp = self._get_treeElement(place_graphics, 'position')
        tmp.set('x', self.position.x)
        tmp.set('y', self.position.y)
        
        scale = 1.0
        if self.petri_net:
            scale = self.petri_net.scale
        
        tmp = self._get_treeElement(place_graphics, 'dimension')
        tmp.set('x', PetriNet.PLACE_RADIUS*scale)
        tmp.set('y', PetriNet.PLACE_RADIUS*scale)
        
        tmp = place_graphics.find('fill')
        if tmp is None:
            tmp = ET.SubElement(place_graphics, 'fill', {'color': PetriNet.PLACE_CONFIG[self._type]['fill']})
        
        tmp = place_graphics.find('line')
        if tmp is None:
            tmp = ET.SubElement(place_graphics, 'line', {
                                                         'color': PetriNet.PLACE_CONFIG[self._type]['outline'],
                                                         'width': PetriNet.LINE_WIDTH
                                                         }
                                )
        
        return self._treeElement

class Transition(Node):
    
    """Petri Net Transition Class."""
    
    def __init__(self, name, transition_type = TransitionTypes.IMMEDIATE, position = Vec2(), isHorizontal = False, rate = 1.0, priority = 1):
        
        """Transition constructor
        
            Sets the name, type, position, orientation and rate of a transition.
            
            Positional Arguments:
            name -- name -- Any string (preferably only alphanumeric characters, daches and underscores).
                    
            Keyword Arguments:
            transitionType -- Should be set from one of the TransitionTypes Class' class members.
            position -- An instance of the Vec2 utility class.
            isHorizontal -- A boolean specifying whether the transition
                            should be drawn as a vertical bar or as a horizontal bar.
            rate -- For timed_stochastic transitions, the rate used to determine
                    the firing of a transition.
        """
        
        super(Transition, self).__init__(name, position)
        
        self.type = transition_type
        self.isHorizontal = isHorizontal
        
        #For stochastic_timed transitions:
        self.rate = rate
        self.priority = priority
    
    @classmethod
    def fromETreeElement(cls, element):
        if element.tag != 'transition':
            raise Exception('Wrong eTree seed element for transition.')
        
        name = element.get('id')
        transition_name = element.find('name')
        if transition_name is not None:
            try:
                name = transition_name.findtext('text')
            except:
                tmp = transition_name.find('value')
                name = tmp.text
                if PetriNet.FIX_MALFORMED_PNML:
                    transition_name.remove(tmp)
                    ET.SubElement(transition_name, 'text', text = name)
        if name[1] == '.':
            name = name[2:] 
        if not name:
            raise Exception('Transition name cannot be an empty string.')
        
        
        try:
            position_el = element.find('graphics').find('position')
            position = Vec2(float(position_el.get('x')), float(position_el.get('y')))
        except:
            position = Vec2()
        
        toolspecific_el = element.find("toolspecific[@name='PNLab']")
        try:
            transition_type = toolspecific_el.find('type').findtext('text')
            if transition_type not in [TransitionTypes.IMMEDIATE, TransitionTypes.TIMED_STOCHASTIC]:
                raise Exception('Warning: Wrong type while reading transition object.')
        except:
            transition_type = TransitionTypes.IMMEDIATE
        
        try:
            if toolspecific_el is not None:
                isHorizontal = bool(int(toolspecific_el.find('isHorizontal').findtext('text')))
            else:
                transition_isHorizontal = element.find('orientation')
                isHorizontal = transition_isHorizontal.findtext('value') == '1'
                if PetriNet.FIX_MALFORMED_PNML:
                    element.remove(transition_isHorizontal)
        except:
            isHorizontal = False
        
        try:
            if toolspecific_el is not None:
                rate = float(toolspecific_el.find('rate').findtext('text'))
            else:
                transition_rate = element.find('rate')
                rate = float(transition_rate.findtext('value'))
                if PetriNet.FIX_MALFORMED_PNML:
                    element.remove(transition_rate)
        except:
            rate = 1.0
        
        try:
            if toolspecific_el is not None:
                priority = int(toolspecific_el.find('priority').findtext('text'))
            else:
                transition_priority = element.find('priority')
                priority = int(transition_priority.findtext('value'))
                if PetriNet.FIX_MALFORMED_PNML:
                    element.remove(transition_priority)
        except:
            priority = 1
        
        t = Transition(name, type, position, isHorizontal, rate, priority)
        
        t._treeElement = element
        return t
    
    def _build_treeElement(self):
        
        name = self.__str__()
        transition = ET.Element('transition', {'id': name})
        
        transition_name = ET.SubElement(transition, 'name')
        ET.SubElement(transition_name, 'text', text = name)
        tmp = ET.SubElement(transition_name, 'graphics')
        if self.isHorizontal:
            ET.SubElement(tmp, 'offset', {'x': 0.0, 'y': PetriNet.TRANSITION_HORIZONTAL_LABEL_PADDING})
        else:
            ET.SubElement(tmp, 'offset', {'x': 0.0, 'y': PetriNet.TRANSITION_VERTICAL_LABEL_PADDING})
        
        transition_toolspecific = ET.SubElement(transition, 'toolspecific', {'tool': 'PNLab', 'version': VERSION})
        
        tmp = ET.SubElement(transition_toolspecific, 'type')
        ET.SubElement(tmp, 'text', text = self.type)
        
        tmp = ET.SubElement(transition_toolspecific, 'isHorizontal')
        ET.SubElement(tmp, 'text', text = str(int(self.isHorizontal)))
        
        tmp = ET.SubElement(transition_toolspecific, 'rate')
        ET.SubElement(tmp, 'text', text = str(self.rate))
        
        tmp = ET.SubElement(transition_toolspecific, 'priority')
        ET.SubElement(tmp, 'text', text = str(self.priority))
        
        tmp = ET.SubElement(transition, 'graphics')
        ET.SubElement(tmp, 'position', {'x': self.position.x, 'y': self.position.y})
        scale = 1.0
        if self.petri_net:
            scale = self.petri_net.scale
        if self.isHorizontal:
            width = PetriNet.TRANSITION_HALF_LARGE
            height = PetriNet.TRANSITION_HALF_SMALL
        else:
            width = PetriNet.TRANSITION_HALF_SMALL
            height = PetriNet.TRANSITION_HALF_LARGE
        ET.SubElement(tmp, 'dimension', {'x': width*scale, 'y': height*scale})
        ET.SubElement(tmp, 'fill', {'color': PetriNet.TRANSITION_CONFIG[self.type]['fill']})
        ET.SubElement(tmp, 'line', {
                                    'color': PetriNet.TRANSITION_CONFIG[self.type]['outline'],
                                    'width': PetriNet.LINE_WIDTH,
                                    'style': 'solid'})
        
        return transition
    
    def _merge_treeElement(self):
        
        name = self.__str__()
        transition = self._treeElement
        
        transition_name = self._get_treeElement(transition, 'name')
        tmp = self._get_treeElement(transition_name)
        tmp.text = name
        
        if PetriNet.UPDATE_ELEMENT_ID:
            transition.set('id', name)
        
        if PetriNet.UPDATE_LABEL_OFFSET:
            transition_name_graphics = self._get_treeElement(transition_name, 'graphics') 
            tmp = self._get_treeElement(transition_name_graphics, 'offset')
            tmp.set('x', 0.0)
            if self.isHorizontal:
                tmp.set('y', PetriNet.TRANSITION_HORIZONTAL_LABEL_PADDING)
            else:
                tmp.set('y', PetriNet.TRANSITION_VERTICAL_LABEL_PADDING)
        
        transition_toolspecific = self._get_treeElement(transition, "toolspecific[@tool='PNLab']", {'tool': 'PNLab', 'version': VERSION})
        transition_type = self._get_treeElement(transition_toolspecific, 'type')
        tmp = self._get_treeElement(transition_type)
        tmp.text = self.type
        
        transition_isHorizontal = self._get_treeElement(transition_toolspecific, 'isHorizontal')
        tmp = self._get_treeElement(transition_isHorizontal)
        tmp.text = str(int(self.isHorizontal))
        
        transition_rate = self._get_treeElement(transition_toolspecific, 'rate')
        tmp = self._get_treeElement(transition_rate)
        tmp.text = str(self.rate)
        
        transition_priority = self._get_treeElement(transition_toolspecific, 'priority')
        tmp = self._get_treeElement(transition_priority)
        tmp.text = str(self.priority)
        
        transition_graphics = self._get_treeElement(transition, 'graphics')
        tmp = self._get_treeElement(transition_graphics, 'position')
        tmp.set('x', self.position.x)
        tmp.set('y', self.position.y)
        
        scale = 1.0
        if self.petri_net:
            scale = self.petri_net.scale
        
        tmp = self._get_treeElement(transition_graphics, 'dimension')
        if self.isHorizontal:
            width = PetriNet.TRANSITION_HALF_LARGE
            height = PetriNet.TRANSITION_HALF_SMALL
        else:
            width = PetriNet.TRANSITION_HALF_SMALL
            height = PetriNet.TRANSITION_HALF_LARGE
        tmp.set('x', width*scale)
        tmp.set('y', height*scale)
        
        tmp = transition_graphics.find('fill')
        if tmp is None:
            tmp = ET.SubElement(transition_graphics, 'fill', {'color': PetriNet.TRANSITION_CONFIG[self.type]['fill']})
        
        tmp = transition_graphics.find('line')
        if tmp is None:
            tmp = ET.SubElement(transition_graphics, 'line', {
                                                         'color': PetriNet.TRANSITION_CONFIG[self.type]['outline'],
                                                         'width': PetriNet.LINE_WIDTH
                                                         }
                                )
        
        return self._treeElement

class PetriNet(object):
    
    '''
    #TODO (Possibly):
    Add a 'saved' attribute, to know when some attribute has changed and
    saving is necessary before the object is destroyed.
    '''
    
    LINE_WIDTH = 2.0
    PLACE_RADIUS = 25
    PLACE_LABEL_PADDING = PLACE_RADIUS + 10
    
    PLACE_CONFIG = {
                PlaceTypes.ACTION: {
                            'fill' : '#00EE00',
                            'outline' : '#00AA00'
                            },
                PlaceTypes.PREDICATE: {
                            'fill' : '#0000EE',
                            'outline' : '#0000AA'
                            },
                PlaceTypes.TASK: {
                            'fill' : '#EEEE00',
                            'outline' : '#AAAA00'
                            }
                }
    
    TRANSITION_HALF_LARGE = 40
    TRANSITION_HALF_SMALL = 7.5
    TRANSITION_HORIZONTAL_LABEL_PADDING = TRANSITION_HALF_SMALL + 10
    TRANSITION_VERTICAL_LABEL_PADDING = TRANSITION_HALF_LARGE + 10
    
    TRANSITION_CONFIG = {
                 TransitionTypes.IMMEDIATE: {
                                    'fill' : '#444444',
                                    'outline' : '#444444'
                                    },
                 TransitionTypes.TIMED_STOCHASTIC: {
                                    'fill' : '#FFFFFF',
                                    'outline' : '#444444'
                                    }
                }
    
    UPDATE_ELEMENT_ID = True
    UPDATE_LABEL_OFFSET = True
    FIX_MALFORMED_PNML = True
    
    def __init__(self, name):
        """Petri Net Class' constuctor."""
        
        super(PetriNet, self).__init__()
        
        if not name:
            raise Exception("Parameter 'name' must be a non-empty string.")
        
        self.name = name
        self.places = {}
        self.transitions = {}
        self.scale = 1.0
        
        root_el = ET.Element('pnml', {'xmlns': 'http://www.pnml.org/version-2009/grammar/pnml'})
        self._tree = ET.ElementTree(root_el)
        ET.SubElement(root_el, 'page', {'id': 'top_lvl_page'})
    
    @classmethod
    def from_ElementTree(cls, et):
        
        pnets = []
        root = et.getroot()
        for net in root.findall('net'):
            
            try:
                name = net.find('name').findtext('text')
            except:
                name = net.get('id')
            
            pn = PetriNet(name)
            
            try:
                scale = float(net.find("toolspecific[@tool='PNLab']").find('scale').findtext('text'))
                pn.scale = scale
            except:
                pass
            
            nodes_queue = [net]
            
            while nodes_queue:
                current = nodes_queue[-1]
                pages = current.findall('page')
                if pages:
                    nodes_queue += pages
                    continue
                for p in current.findall('place'):
                    pn.add_place(Place.fromETreeElement(p))
                for t in current.findall('transition'):
                    pn.add_transition(Transition.fromETreeElement(t))
                
                for arc in current.findall('arc'):
                    pass
                
                nodes_queue = nodes_queue[:-1]
        
        return pnets
        
    
    def to_ElementTree(self):
        
        root_el = self._tree
        net = ET.SubElement(root_el, 'net', {
                                        'id' : self.name,
                                        'type': 'http://www.pnml.org/version-2009/grammar/ptnet'
                                        })
        
        page = ET.SubElement(net, 'page', {'id': 'page_01'})
        for p in self.places.itervalues():
            place = ET.SubElement(page, 'place', {'id': str(p)})
            place_graphics = ET.SubElement(place, 'graphics')
            ET.SubElement(place_graphics, 'position', {'x': p.position.x*self.scale, 'y': p.position.y*self.scale})
            ET.SubElement(place_graphics, 'dimension', {'x': 2*PetriNet.PLACE_RADIUS*self.scale, 'y': 2*PetriNet.PLACE_RADIUS*self.scale})
            ET.SubElement(place_graphics, 'fill', {'color': PetriNet.PLACE_CONFIG[p.type]['fill']})
            ET.SubElement(place_graphics, 'line', {'color': PetriNet.PLACE_CONFIG[p.type]['outline'], 'width': PetriNet.LINE_WIDTH})
            name = ET.SubElement(place, 'name')
            ET.SubElement(name, 'text', text = str(p))
            name_graphics = ET.SubElement(name, 'graphics')
            ET.SubElement(name_graphics, 'offset', {'x': 0, 'y': PetriNet.PLACE_LABEL_PADDING*self.scale})
            marking = ET.SubElement(place, 'initialMarking')
            ET.SubElement(marking, 'text', text = p.init_marking)
            tool_specific = ET.SubElement(place, 'toolspecific')
            ET.SubElement(tool_specific, 'type', text = p.type)
        
        for t in self.transitions.itervalues():
            transition = ET.SubElement(page, 'transition', {'id': str(t)})
            transition_graphics = ET.SubElement(transition, 'graphics')
            ET.SubElement(transition_graphics, 'position', {'x': t.position.x*self.scale, 'y': t.position.y*self.scale})
            if t.isHorizontal:
                ET.SubElement(transition_graphics, 'dimension', {'x': 2*PetriNet.TRANSITION_HALF_LARGE*self.scale, 'y': 2*PetriNet.TRANSITION_HALF_SMALL*self.scale})
            else:
                ET.SubElement(transition_graphics, 'dimension', {'x': 2*PetriNet.TRANSITION_HALF_SMALL*self.scale, 'y': 2*PetriNet.TRANSITION_HALF_LARGE*self.scale})
            ET.SubElement(transition_graphics, 'fill', {'color': PetriNet.TRANSITION_CONFIG [t.type]['fill']})
            ET.SubElement(transition_graphics, 'line', {'color': PetriNet.TRANSITION_CONFIG[t.type]['outline'], 'width': PetriNet.LINE_WIDTH})
            name = ET.SubElement(transition, 'name')
            ET.SubElement(name, 'text', text = str(t))
            name_graphics = ET.SubElement(name, 'graphics')
            if t.isHorizontal:
                ET.SubElement(name_graphics, 'offset', {'x': 0, 'y': PetriNet.TRANSITION_HORIZONTAL_LABEL_PADDING*self.scale})
            else:
                ET.SubElement(name_graphics, 'offset', {'x': 0, 'y': PetriNet.TRANSITION_VERTICAL_LABEL_PADDING*self.scale})
            orientation = ET.SubElement(transition, 'orientation')
            ET.SubElement(orientation, 'value', text = int(t.isHorizontal))
            tool_specific = ET.SubElement(transition, 'toolspecific')
            ET.SubElement(tool_specific, 'type', text = t.type)
        
        
        return copy.deepcopy(self._tree)
    
    @classmethod
    def from_pnml_file(cls, file_name):
        et = ET.parse(file_name)
        return PetriNet.from_ElementTree(et)
    
    def to_pnml_file(self, file_name):
        et = self.to_ElementTree()
        et.write(file_name, 'utf-8')
    
    def add_place(self, p, overwrite = False):
        """Adds a place from the Petri Net.
        
        Clears the arcs from the place object and adds it to the Petri Net.
        If a place with the same string representation [i. e. str(place_obj)]
        already exists, it can either replace it or do nothing, depending on
        the second argument.  
        
        Arguments:
        p -- A Place object to insert
        overwrite -- Indicates whether to overwrite the place
                    when a place with the same string representation
                    already exists.
                    
        Returns False if a place with the same string representation
        already exists and overwrite is False. Returns True otherwise.
        """
        key = str(p)
        if key in self.places:
            if not overwrite:
                return False
            else:
                self.places.pop(key)
        p._incoming_arcs = {}
        p._outgoing_arcs = {}
        self.places[key] = p
        
        p.petri_net = self
        
        if p._treeElement:
            return True
        
        place_element = p.treeElement 
        page = self._tree.getroot().find('page')
        page.append(place_element)
        
        return True
    
    def remove_place(self, place):
        """Removes a place from the Petri Net.
        
        Argument 'place' should be either a Place object,
        or a string representation of a Place object [i. e. str(place_obj)].
        
        Returns the removed object. 
        """
        if isinstance(place, Place): 
            key = str(place)
        else:
            key = place
        if key not in self.places:
            return
        p = self.places.pop(key)
        for t in p._incoming_arcs.iterkeys():
            self.transitions[t]._incoming_arcs.pop(key, None)
            self.transitions[t]._outgoing_arcs.pop(key, None)
        
        for t in p._outgoing_arcs.iterkeys():
            self.transitions[t]._incoming_arcs.pop(key, None)
            self.transitions[t]._outgoing_arcs.pop(key, None)
        
        p.petri_net = None
        return p
    
    def add_transition(self, t, overwrite = False):
        """Adds a transition from the Petri Net.
        
        Clears the arcs from the transition object and adds it to the Petri Net.
        If a transition with the same string representation [i. e. str(transition_obj)]
        already exists, it can either replace it or do nothing, depending on
        the second argument.  
        
        Arguments:
        t -- A Transition object to insert
        overwrite -- Indicates whether to overwrite the transition
                    when a transition with the same string representation
                    already exists.
        
        Returns False if a transition with the same string representation
        already exists and overwrite is False. Returns True otherwise.
        """
        key = str(t)
        if key in self.transitions:
            if not overwrite:
                return False
            else:
                self.transitions.pop(key)
        t._incoming_arcs = {}
        t._outgoing_arcs = {}
        self.transitions[key] = t
        
        t.petri_net = self
        
        return True
    
    def remove_transition(self, transition):
        """Removes a transition from the Petri Net.
        
        Argument 'transition' should be either a Transition object,
        or a string representation of a Transition object [i. e. str(transition_obj)].
        
        Returns the removed object. 
        """
        if isinstance(transition, Transition): 
            key = str(transition)
        else:
            key = transition
        if key not in self.transitions:
            return
        t = self.transitions.pop(key)
        for p in t._incoming_arcs.iterkeys():
            self.places[p]._incoming_arcs.pop(key, None)
            self.places[p]._outgoing_arcs.pop(key, None)
        
        for p in t._outgoing_arcs.iterkeys():
            self.places[p]._incoming_arcs.pop(key, None)
            self.places[p]._outgoing_arcs.pop(key, None)
        
        t.petri_net = None
        
        return t
    
    def can_connect(self, source, target):
        """
        Checks if an arc can be created between the source and target objects. 
        
        Checks if the source and target are Place and Transition objects (one of each),
        as well as if they both exist in the Petri Net.
        """
        if not ((isinstance(source, Place) and isinstance(target, Transition))
                or (isinstance(source, Transition) and isinstance(target, Place))):
            return False
        
        if isinstance(source, Place):
            place = source
            transition = target
        else:
            place = target
            transition = source
            
        if str(place) not in self.places:
            return False
        if str(transition) not in self.transitions:
            return False
        
        return True
    
    def add_arc(self, source, target, weight = 1):
        """
        Adds an arc from 'source' to 'target' with weight 'weight'.
        
        source and target should  be instances of the Place and Transition classes,
        one of each.
        """
        if not self.can_connect(source, target):
            raise Exception('Arcs should go either from a place to a transition or vice versa and they should exist in the PN.')
        
        src = str(source)
        trgt = str(target)
        if isinstance(source, Place):
            self.places[src]._outgoing_arcs[trgt] = weight
            self.transitions[trgt]._incoming_arcs[src] = weight
        else:
            self.transitions[src]._outgoing_arcs[trgt] = weight
            self.places[trgt]._incoming_arcs[src] = weight
    
    def remove_arc(self, source, target):
        """
        Removes an arc from 'source' to 'target'.
        
        source and target should  be instances of the Place and Transition classes,
        one of each.
        """
        if not self.can_connect(source, target):
            raise Exception('Arcs should go either from a place to a transition or vice versa.')
        
        src = str(source)
        trgt = str(target)
        if isinstance(source, Place):
            self.places[src]._outgoing_arcs.pop(trgt, None)
            self.transitions[trgt]._incoming_arcs.pop(src, None)
        else:
            self.transitions[src]._outgoing_arcs.pop(trgt, None)
            self.places[trgt]._incoming_arcs.pop(src, None)
    