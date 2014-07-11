# -*- coding: utf-8 -*-
"""
@author: Adrián Revuelta Cuauhtli
"""

import abc
import copy
import io
#import xml.etree.ElementTree as ET
import lxml.etree as ET

from utils.Vector import Vec2
import os

VERSION = '0.8'

def _get_treeElement(parent, tag = 'text', attr = None):
    """Aux function to search or create a certain ElementTree element."""
    
    el = parent.find(tag)
    if el is None:
        if attr is None:
            el = ET.SubElement(parent, tag)
        else:
            el = ET.SubElement(parent, tag, attr)
    return el
 
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
    """PetriNets Node class, which is extended by Place and Transition Classes.
        NOTICE: Arc does not extend from this class.
    """
    
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, name, nodeType, position):
        """Node constructor
        
            Sets the name and position of a node.
            
            Positional Arguments:
            name -- Any string (preferably only alphanumeric characters, daches and underscores).
            position -- An instance of the Vec2 utility class.
            """
        
        if not name:
            raise Exception('A Node name must be a non-empty string.')
        
        self._name = name
        self._type = nodeType
        self.petri_net = None
        self.position = Vec2(position)
        self._incoming_arcs = {}
        self._outgoing_arcs = {}
        self.hasTreeElement = False
        self._references = set()
        self._id = self._get_id()
    
    @property
    def name(self):
        """Read-only property. Name of the node, not including the type prefix."""
        return self._name
    
    def _set_name(self, value):
        
        if not value:
            raise Exception('A Node name must be a non-empty string.')
        
        self._name = value
        self._update_id()
    
    def _get_id(self):
        return self._full_name.replace(' ', '_').replace('(', '__').replace(')', '__').replace(',', '_')
    
    @property
    def _full_name(self):
        """Read-only property. Name of the node, INCLUDING the type prefix."""
        return self._type[0] + '.' + self._name
    
    @property
    def type(self):
        """Read-only property. Node type. The actual value is one of the strings from the constants in PlaceTypes and TransitionTypes classes."""
        
        return self._type
    
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
    
    def _update_id(self):
        
        old_id = self.__repr__()
        self._id = self._get_id()
        
        if not self.hasTreeElement or not self.petri_net:
            return
        
        el = self.petri_net._tree.find('//*[@id="' + old_id + '"]')
        el.set('id', self.__repr__())
        
        for ref in self.petri_net._tree.findall('//*[@ref="' + old_id + '"]'): 
            ref.set('ref', self.__repr__())
        for arc in self.petri_net._tree.findall('//*[@target="' + old_id + '"]'):
            arc.set('target', self.__repr__())
        for arc in self.petri_net._tree.findall('//*[@source="' + old_id + '"]'):
            arc.set('source', self.__repr__())
    
    def _merge_treeElement(self):
        """Merges the current ElementTree element information with the previously loaded info."""
        self._update_id()
    
    @abc.abstractmethod
    def _build_treeElement(self):
        """Builds the ElementTree element from the node's information."""
        return

    def __repr__(self):
        """ String representation of a Node object. It is the id of the node.
        
        If the id is created by PNLab tool, then it is formed with 
        the first letter of the node type, a dot and the node name with spaces replaced by an underscore.
        """
        return self._id
    
    def __str__(self):
        """ Printable name of a Node object. It is the id of the node.
        
        If the id is created by PNLab tool, then it is formed with 
        the first letter of the node type, a dot and the node name.
        """
        return self._full_name

class Place(Node):
    """Petri Net Place Class."""
    
    def __init__(self, name, place_type = PlaceTypes.PREDICATE, position = Vec2(), init_marking = 0, capacity = 1):
        """Place constructor
        
            Sets the name, type, position and initial marking of a place.
            
            Positional Arguments:
            name -- Any string (preferably only alphanumeric characters, daches and underscores).
                    
            Keyword Arguments:
            placeType -- Should be set from one of the PlaceTypes Class' class members.
            position -- An instance of the Vec2 utility class.
            initial_marking -- An integer specifying the initial marking for this place.
        """
        
        super(Place, self).__init__(name, place_type, position)
        
        self.init_marking = init_marking
        self.capacity = capacity
        self.current_marking = self.init_marking
    
    @classmethod
    def fromETreeElement(cls, element):
        """Method for parsing xml nodes as an ElementTree object."""
        if element.tag != 'place':
            raise Exception('Wrong eTree seed element for place.')
        
        place_id = element.get('id')
        place_name = element.find('name')
        if place_name is not None:
            name = place_name.findtext('text')
        else:
            name = place_id
        
        place_type = PlaceTypes.PREDICATE
        if name[:2] == 'a.':
            name = name[2:]
            place_type = PlaceTypes.ACTION
        elif name[:2] == 't.':
            name = name[2:]
            place_type = PlaceTypes.TASK
        elif name[:2] == 'p.':
            name = name[2:]
        
        if not name:
            raise Exception('Place name cannot be an empty string.')
        
        try:
            position_el = element.find('graphics/position')
            position = Vec2(float(position_el.get('x')), float(position_el.get('y')))
        except:
            position = Vec2()
        
        initMarking = 0
        place_initMarking = element.find('initialMarking')
        if place_initMarking is not None:
            initMarking = int(place_initMarking.findtext('text'))
        
        toolspecific_el = element.find('toolspecific[@tool="PNLab"]')
        try:
            p_type = toolspecific_el.find('type').findtext('text')
            if p_type in [PlaceTypes.ACTION, PlaceTypes.PREDICATE, PlaceTypes.TASK]:
                place_type = p_type
        except:
            pass
        
        try:
            capacity = int(toolspecific_el.find('capacity/text').text)
        except:
            capacity = 0
        
        p = Place(name, place_type, position, initMarking, capacity)
        p.hasTreeElement = True
        return p
    
    def _build_treeElement(self):
        
        place = ET.Element('place', {'id': self.__repr__()})
        
        place_name = ET.SubElement(place, 'name')
        tmp = ET.SubElement(place_name, 'text')
        tmp.text = self.__str__()
        tmp = ET.SubElement(place_name, 'graphics')
        ET.SubElement(tmp, 'offset', {'x': str(0.0), 'y': str(PetriNet.PLACE_LABEL_PADDING)})
            
        tmp = ET.SubElement(place, 'initialMarking')
        tmp = ET.SubElement(tmp, 'text')
        tmp.text = str(self.init_marking)
        
        place_toolspecific = ET.SubElement(place, 'toolspecific', {'tool': 'PNLab', 'version': VERSION})
    
        tmp = ET.SubElement(place_toolspecific, 'type')
        tmp = ET.SubElement(tmp, 'text')
        tmp.text = self._type
        
        tmp = ET.SubElement(place_toolspecific, 'capacity')
        tmp = ET.SubElement(tmp, 'text')
        tmp.text = str(int(self.capacity))
        
        tmp = ET.SubElement(place, 'graphics')
        ET.SubElement(tmp, 'position', {'x': str(self.position.x), 'y': str(self.position.y)})
        scale = 1.0
        if self.petri_net:
            scale = self.petri_net.scale
        ET.SubElement(tmp, 'dimension', {'x': str(PetriNet.PLACE_RADIUS*scale), 'y': str(PetriNet.PLACE_RADIUS*scale)})
        ET.SubElement(tmp, 'fill', {'color': PetriNet.PLACE_CONFIG[self._type]['fill']})
        ET.SubElement(tmp, 'line', {
                                    'color': PetriNet.PLACE_CONFIG[self._type]['outline'],
                                    'width': str(PetriNet.LINE_WIDTH),
                                    'style': 'solid'})
        
        self.hasTreeElement = True
        return place
    
    def _merge_treeElement(self):
        
        super(Place, self)._merge_treeElement()
        
        place = self.petri_net._tree.find('//*[@id="' + self.__repr__() + '"]')
        
        place_name = _get_treeElement(place, 'name')
        tmp = _get_treeElement(place_name)
        tmp.text = self.__str__()
        
        place.set('id', self.__repr__())
        
        if PetriNet.UPDATE_LABEL_OFFSET:
            place_name_graphics = _get_treeElement(place_name, 'graphics') 
            tmp = _get_treeElement(place_name_graphics, 'offset')
            tmp.set('x', str(0.0))
            tmp.set('y', str(PetriNet.PLACE_LABEL_PADDING))
        
        place_initMarking = _get_treeElement(place, 'initialMarking')
        tmp = _get_treeElement(place_initMarking)
        tmp.text = str(self.init_marking)
        
        
        place_toolspecific = _get_treeElement(place, 'toolspecific[@tool="PNLab"]', {'tool': 'PNLab', 'version': VERSION})
        place_type = _get_treeElement(place_toolspecific, 'type')
        tmp = _get_treeElement(place_type)
        tmp.text = self._type
        
        place_capacity = _get_treeElement(place_toolspecific, 'capacity')
        tmp = _get_treeElement(place_capacity)
        tmp.text = str(self.capacity)
        
        place_graphics = _get_treeElement(place, 'graphics')
        tmp = _get_treeElement(place_graphics, 'position')
        tmp.set('x', str(self.position.x))
        tmp.set('y', str(self.position.y))
        
        scale = 1.0
        if self.petri_net:
            scale = self.petri_net.scale
        
        tmp = _get_treeElement(place_graphics, 'dimension')
        tmp.set('x', str(PetriNet.PLACE_RADIUS*scale))
        tmp.set('y', str(PetriNet.PLACE_RADIUS*scale))
        
        tmp = place_graphics.find('fill')
        if tmp is None:
            tmp = ET.SubElement(place_graphics, 'fill', {'color': PetriNet.PLACE_CONFIG[self._type]['fill']})
        
        tmp = place_graphics.find('line')
        if tmp is None:
            tmp = ET.SubElement(place_graphics, 'line', {
                                                         'color': PetriNet.PLACE_CONFIG[self._type]['outline'],
                                                         'width': str(PetriNet.LINE_WIDTH)
                                                         }
                                )

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
        
        super(Transition, self).__init__(name, transition_type, position)
        
        self.isHorizontal = isHorizontal
        
        #For stochastic_timed transitions:
        self.rate = rate
        self.priority = priority
    
    @property
    def type(self):
        """Returns the type of the transition. Should be a value from one of the constants in TransitionTypes class."""
        return self._type
    
    @type.setter
    def type(self, value):
        """Sets the type of the transition. Should be a value from one of the constants in TransitionTypes class."""
        self._type = value
    
    @classmethod
    def fromETreeElement(cls, element):
        """Method for parsing xml nodes as an ElementTree object."""
        if element.tag != 'transition':
            raise Exception('Wrong eTree seed element for transition.')
        
        transition_id = element.get('id')
        transition_name = element.find('name')
        if transition_name is not None:
            name = transition_name.findtext('text')
        else:
            name = transition_id
        
        transition_type = TransitionTypes.IMMEDIATE
        if name[:2] == 'i.':
            name = name[2:]
        elif name[:2] == 's.':
            name = name[2:]
            transition_type = TransitionTypes.TIMED_STOCHASTIC
             
        if not name:
            raise Exception('Transition name cannot be an empty string.')
        
        
        try:
            position_el = element.find('graphics/position')
            position = Vec2(float(position_el.get('x')), float(position_el.get('y')))
        except:
            position = Vec2()
        
        toolspecific_el = element.find('toolspecific[@tool="PNLab"]')
        try:
            t_type = toolspecific_el.find('type/text').text
            if t_type in [TransitionTypes.IMMEDIATE, TransitionTypes.TIMED_STOCHASTIC]:
                transition_type = t_type
        except:
            pass
        
        try:
            isHorizontal = bool(int(toolspecific_el.find('isHorizontal/text').text))
        except:
            isHorizontal = False
        
        try:
            rate = float(toolspecific_el.find('rate/text').text)
        except:
            rate = 1.0
        
        try:
            priority = int(toolspecific_el.find('priority/text').text)
        except:
            priority = 1
        
        t = Transition(name, transition_type, position, isHorizontal, rate, priority)
        t.hasTreeElement = True
        return t
    
    def _build_treeElement(self):
        
        transition = ET.Element('transition', {'id': self.__repr__()})
        
        transition_name = ET.SubElement(transition, 'name')
        tmp = ET.SubElement(transition_name, 'text')
        tmp.text = self.__str__()
        tmp = ET.SubElement(transition_name, 'graphics')
        if self.isHorizontal:
            ET.SubElement(tmp, 'offset', {'x': str(0.0), 'y': str(PetriNet.TRANSITION_HORIZONTAL_LABEL_PADDING)})
        else:
            ET.SubElement(tmp, 'offset', {'x': str(0.0), 'y': str(PetriNet.TRANSITION_VERTICAL_LABEL_PADDING)})
        
        transition_toolspecific = ET.SubElement(transition, 'toolspecific', {'tool': 'PNLab', 'version': VERSION})
        
        tmp = ET.SubElement(transition_toolspecific, 'type')
        tmp = ET.SubElement(tmp, 'text')
        tmp.text = self.type
        
        tmp = ET.SubElement(transition_toolspecific, 'isHorizontal')
        tmp = ET.SubElement(tmp, 'text')
        tmp.text = str(int(self.isHorizontal))
        
        tmp = ET.SubElement(transition_toolspecific, 'rate')
        tmp = ET.SubElement(tmp, 'text')
        tmp.text = str(self.rate)
        
        tmp = ET.SubElement(transition_toolspecific, 'priority')
        tmp = ET.SubElement(tmp, 'text')
        tmp.text = str(self.priority)
        
        tmp = ET.SubElement(transition, 'graphics')
        ET.SubElement(tmp, 'position', {'x': str(self.position.x), 'y': str(self.position.y)})
        scale = 1.0
        if self.petri_net:
            scale = self.petri_net.scale
        if self.isHorizontal:
            width = PetriNet.TRANSITION_HALF_LARGE
            height = PetriNet.TRANSITION_HALF_SMALL
        else:
            width = PetriNet.TRANSITION_HALF_SMALL
            height = PetriNet.TRANSITION_HALF_LARGE
        ET.SubElement(tmp, 'dimension', {'x': str(width*scale), 'y': str(height*scale)})
        ET.SubElement(tmp, 'fill', {'color': PetriNet.TRANSITION_CONFIG[self.type]['fill']})
        ET.SubElement(tmp, 'line', {
                                    'color': PetriNet.TRANSITION_CONFIG[self.type]['outline'],
                                    'width': str(PetriNet.LINE_WIDTH),
                                    'style': 'solid'})
        
        self.hasTreeElement = True
        return transition
    
    def _merge_treeElement(self):
        
        super(Transition, self)._merge_treeElement()
        
        transition = self.petri_net._tree.find('//*[@id="' + self.__repr__() + '"]')
        
        transition_name = _get_treeElement(transition, 'name')
        tmp = _get_treeElement(transition_name)
        tmp.text = self.__str__()
        
        transition.set('id', self.__repr__())
        
        if PetriNet.UPDATE_LABEL_OFFSET:
            transition_name_graphics = _get_treeElement(transition_name, 'graphics') 
            tmp = _get_treeElement(transition_name_graphics, 'offset')
            tmp.set('x', str(0.0))
            if self.isHorizontal:
                tmp.set('y', str(PetriNet.TRANSITION_HORIZONTAL_LABEL_PADDING))
            else:
                tmp.set('y', str(PetriNet.TRANSITION_VERTICAL_LABEL_PADDING))
        
        transition_toolspecific = _get_treeElement(transition, 'toolspecific[@tool="PNLab"]', {'tool': 'PNLab', 'version': VERSION})
        transition_type = _get_treeElement(transition_toolspecific, 'type')
        tmp = _get_treeElement(transition_type)
        tmp.text = self.type
        
        transition_isHorizontal = _get_treeElement(transition_toolspecific, 'isHorizontal')
        tmp = _get_treeElement(transition_isHorizontal)
        tmp.text = str(int(self.isHorizontal))
        
        transition_rate = _get_treeElement(transition_toolspecific, 'rate')
        tmp = _get_treeElement(transition_rate)
        tmp.text = str(self.rate)
        
        transition_priority = _get_treeElement(transition_toolspecific, 'priority')
        tmp = _get_treeElement(transition_priority)
        tmp.text = str(self.priority)
        
        transition_graphics = _get_treeElement(transition, 'graphics')
        tmp = _get_treeElement(transition_graphics, 'position')
        tmp.set('x', str(self.position.x))
        tmp.set('y', str(self.position.y))
        
        scale = 1.0
        if self.petri_net:
            scale = self.petri_net.scale
        
        tmp = _get_treeElement(transition_graphics, 'dimension')
        if self.isHorizontal:
            width = PetriNet.TRANSITION_HALF_LARGE
            height = PetriNet.TRANSITION_HALF_SMALL
        else:
            width = PetriNet.TRANSITION_HALF_SMALL
            height = PetriNet.TRANSITION_HALF_LARGE
        tmp.set('x', str(width*scale))
        tmp.set('y', str(height*scale))
        
        tmp = transition_graphics.find('fill')
        if tmp is None:
            tmp = ET.SubElement(transition_graphics, 'fill', {'color': PetriNet.TRANSITION_CONFIG[self.type]['fill']})
        
        tmp = transition_graphics.find('line')
        if tmp is None:
            tmp = ET.SubElement(transition_graphics, 'line', {
                                                         'color': PetriNet.TRANSITION_CONFIG[self.type]['outline'],
                                                         'width': str(PetriNet.LINE_WIDTH)
                                                         }
                                )

class _Arc(object):
    
    def __init__(self, source, target, weight = 1, treeElement = None):
        
        self.source = source
        self.target = target
        self.weight = weight
        self._treeElement = treeElement
        self.petri_net = source.petri_net
    
    def __str__(self):
        return repr(self.source) + '_' + repr(self.target)
    
    def __repr__(self):
        return self.__str__()
    
    @property
    def hasTreeElement(self):
        return self._treeElement is not None
    
    def _build_treeElement(self):
        
        arc = ET.Element('arc', {'id': self.__repr__(),
                                 'source': repr(self.source),
                                 'target': repr(self.target),
                                 })
        tmp = ET.SubElement(arc, 'inscription')
        tmp = ET.SubElement(tmp, 'text')
        tmp.text = str(self.weight)
        
        return arc
    
    def _merge_treeElement(self):
        
        el = self.petri_net._tree.find('//*[@id="' + self._treeElement + '"]')
        el.set('id', self.__repr__())
        weight = _get_treeElement(el, 'inscription')
        _get_treeElement(weight).text = str(self.weight)

class PetriNet(object):
    
    '''
    #TODO (Possibly):
    Add a 'saved' attribute, to know when some attribute has changed and
    saving is necessary before the object is destroyed.
    '''
    
    LINE_WIDTH = 2.0
    PLACE_RADIUS = 25
    PLACE_LABEL_PADDING = PLACE_RADIUS + 15
    
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
    TRANSITION_HORIZONTAL_LABEL_PADDING = TRANSITION_HALF_SMALL + 15
    TRANSITION_VERTICAL_LABEL_PADDING = TRANSITION_HALF_LARGE + 15
    
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
    
    UPDATE_LABEL_OFFSET = True
    
    def __init__(self, name, _net = None):
        """Petri Net Class' constuctor."""
        
        super(PetriNet, self).__init__()
        
        if not name:
            raise Exception("PetriNet 'name' must be a non-empty string.")
        
        self.name = name
        self.places = {}
        self.transitions = {}
        self.scale = 1.0
        
        root_el = ET.Element('pnml', {'xmlns': 'http://www.pnml.org/version-2009/grammar/pnml'})
        self._tree = ET.ElementTree(root_el)
        page = None
        if _net is not None:
            root_el.append(_net)
            try:
                self.scale = float(_net.find('toolspecific[@tool="PNLab"]/scale/text').text)
            except:
                pass
            page = _net.find('page')
        else:
            _net = ET.SubElement(root_el, 'net', {'id': name,
                                           'type': 'http://www.pnml.org/version-2009/grammar/ptnet'
                                           })
        
        tmp = _get_treeElement(_net, 'name')
        tmp = _get_treeElement(tmp)
        tmp.text = name
        if page is None:
            ET.SubElement(_net, 'page', {'id': 'PNLab_top_lvl'})
        
    
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
        key = repr(p)
        if key in self.places:
            if not overwrite:
                return False
            else:
                self.places.pop(key)
        p._incoming_arcs = {}
        p._outgoing_arcs = {}
        self.places[key] = p
        
        p.petri_net = self
        
        return True
    
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
        key = repr(t)
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
    
    def remove_place(self, place):
        """Removes a place from the Petri Net.
        
        Argument 'place' should be either a Place object,
        or a string representation of a Place object [i. e. str(place_obj)].
        
        Returns the removed object. 
        """
        
        if isinstance(place, Place): 
            key = repr(place)
        else:
            key = place
        if key not in self.places:
            return None
        p = self.places[key]
        
        for t in p._incoming_arcs.keys() :
            self.remove_arc(self.transitions[t], p)
        
        for t in p._outgoing_arcs.keys():
            self.remove_arc(p, self.transitions[t])
        
        for ref in p._references:
            el = self._tree.find('//*[@id="' + ref + '"]')
            el.getparent().remove(el)
        
        p._references.clear()
        
        p = self.places.pop(key)
        p.petri_net = None
        return p
    
    def _pop_place(self, place):
        
        if isinstance(place, Place): 
            key = repr(place)
        else:
            key = place
        
        return self.places.pop(key, None)
    
    def remove_transition(self, transition):
        """Removes a transition from the Petri Net.
        
        Argument 'transition' should be either a Transition object,
        or a string representation of a Transition object [i. e. str(transition_obj)].
        
        Returns the removed object. 
        """
        if isinstance(transition, Transition): 
            key = repr(transition)
        else:
            key = transition
        if key not in self.transitions:
            return
        t = self.transitions[key]
        
        for p in t._incoming_arcs.keys():
            self.remove_arc(self.places[p], t)
        
        for p in t._outgoing_arcs.keys():
            self.remove_arc(t, self.places[p])
        
        for ref in t._references:
            el = self._tree.find('//*[@id="' + ref + '"]')
            el.getparent().remove(el)
        
        t._references.clear()
        
        t = self.transitions.pop(key)
        t.petri_net = None
        return t
    
    def _pop_transition(self, transition):
        
        if isinstance(transition, Transition): 
            key = repr(transition)
        else:
            key = transition
        
        return self.transitions.pop(key, None)
    
    def rename_place(self, place, value):
        """Renames a place from the Petri Net.
        
        Arguments:
        place -- A Place object or Place string representation to rename.
        value -- The new name of the place WIHTOUT type prefix.
                Preferably this field should be composed of only alphanumeric characters, 
                and possibly underscores or dashes.        
        
        Returns true if successful, false otherwise.
        Raises an exception if name is not a non-empty string.
        """
        
        p = self._pop_place(place)
        if not p:
            raise Exception('Place object to rename not found in PetriNet.')
        
        p._set_name(value)
        
        incoming_arcs = p.incoming_arcs
        outgoing_arcs = p.outgoing_arcs
        
        if not self.add_place(p):
            return False
        
        for key, val in incoming_arcs.items():
            self.add_arc(self.transitions[key], p, val.weight, val._treeElement)
        for key, val in outgoing_arcs.items():
            self.add_arc(p, self.transitions[key], val.weight, val._treeElement)
        
        return True
    
    def rename_transition(self, transition, value):
        """Renames a transition from the Petri Net.
        
        Arguments:
        place -- A Transition object or Transition string representation to rename.
        value -- The new name of the transition WIHTOUT type prefix.
                Preferably this field should be composed of only alphanumeric characters, 
                and possibly underscores or dashes.        
        
        Returns true if successful, false otherwise.
        Raises an exception if name is not a non-empty string.
        """
        
        t = self._pop_transition(transition)
        if not t:
            raise Exception('Transition object to rename not found in PetriNet.') 
        
        t._set_name(value)
        
        incoming_arcs = t.incoming_arcs
        outgoing_arcs = t.outgoing_arcs
        
        if not self.add_transition(t):
            return False
        
        for key, val in incoming_arcs.items():
            self.add_arc(self.places[key], t, val.weight, val._treeElement)
        for key, val in outgoing_arcs.items():
            self.add_arc(t, self.places[key], val.weight, val._treeElement)
        
        return True
        
    
    def _can_connect(self, source, target):
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
            
        if repr(place) not in self.places:
            return False
        if repr(transition) not in self.transitions:
            return False
        
        return True
    
    def add_arc(self, source, target, weight = 1, _treeElement = None):
        """
        Adds an arc from 'source' to 'target' with weight 'weight'.
        
        source and target should  be instances of the Place and Transition classes,
        one of each.
        
        _treeElement is an internal field for maintaining a reference to the tree element when read from a pnml file.
        """
        
        if not self._can_connect(source, target):
            raise Exception('Arcs should go either from a place to a transition or vice versa and they should exist in the PN.')
        
        if repr(target) in source._outgoing_arcs:
            return
        
        arc = _Arc(source, target, weight, _treeElement)
        
        src = repr(source)
        trgt = repr(target)
        
        if isinstance(source, Place):
            self.places[src]._outgoing_arcs[trgt] = arc
            self.transitions[trgt]._incoming_arcs[src] = arc
        else:
            self.transitions[src]._outgoing_arcs[trgt] = arc
            self.places[trgt]._incoming_arcs[src] = arc
        
        return arc
    
    def remove_arc(self, source, target):
        """
        Removes an arc from 'source' to 'target'.
        
        source and target should  be instances of the Place and Transition classes,
        one of each.
        """
        if not self._can_connect(source, target):
            raise Exception('Arcs should go either from a place to a transition or vice versa.')
        
        
        src = repr(source)
        trgt = repr(target)
        if isinstance(source, Place):
            arc = self.places[src]._outgoing_arcs.pop(trgt, None)
            self.transitions[trgt]._incoming_arcs.pop(src, None)
        else:
            arc = self.transitions[src]._outgoing_arcs.pop(trgt, None)
            self.places[trgt]._incoming_arcs.pop(src, None)
        
        if arc and arc.hasTreeElement:
            arc_el = arc.petri_net._tree.find('//*[@id="' + arc._treeElement + '"]')
            arc_el.getparent().remove(arc_el)

    @classmethod
    def from_ElementTree(cls, et, name = None):
        
        pnets = []
        root = et.getroot()
        for net in root.findall('net'):
            if name is None:
                try:
                    name = net.find('name').findtext('text')
                except:
                    name = net.get('id')
            
            pn = PetriNet(name, net)
            
            try:
                scale = float(net.find('toolspecific[@tool="PNLab"]/scale/text').text)
                pn.scale = scale
            except:
                pass
            
            first_queue = [net]
            second_queue = []
            
            while first_queue:
                current = first_queue.pop()
                second_queue.append(current)
                
                for p_el in current.findall('place'):
                    p = Place.fromETreeElement(p_el)
                    pn.add_place(p)
                    place_id = p_el.get('id')
                    for e in net.findall('.//referencePlace[@ref="' + place_id + '"]'):
                        e.set('ref', repr(p))
                    for e in net.findall('.//arc[@source="' + place_id + '"]'):
                        e.set('source', repr(p))
                    for e in net.findall('.//arc[@target="' + place_id + '"]'):
                        e.set('target', repr(p))
                    p_el.set('id', repr(p))
                for t_el in current.findall('transition'):
                    t = Transition.fromETreeElement(t_el)
                    pn.add_transition(t)
                    transition_id = t_el.get('id')
                    for e in net.findall('.//referenceTransition[@ref="' + transition_id + '"]'):
                        e.set('ref', repr(t))
                    for e in net.findall('.//arc[@source="' + transition_id + '"]'):
                        e.set('source', repr(t))
                    for e in net.findall('.//arc[@target="' + transition_id + '"]'):
                        e.set('target', repr(t))
                    t_el.set('id', repr(t))
                
                pages = current.findall('page')
                if pages:
                    first_queue += pages
            
            while second_queue:
                current = second_queue.pop()
                
                for ref in net.findall('.//referencePlace'):
                    reference = ref
                    try:
                        while reference.tag[:9] == 'reference':
                            reference = net.find('.//*[@id="' + reference.get('ref') + '"]')
                    except:
                        raise Exception("Referenced node '" + ref.get('ref') + "' was not found.")
                    
                    pn.places[reference.get('id')]._references.add(ref.get('id'))
                
                for ref in net.findall('.//referenceTransition'):
                    reference = ref
                    try:
                        while reference.tag[:9] == 'reference':
                            reference = net.find('.//*[@id="' + reference.get('ref') + '"]')
                    except:
                        raise Exception("Referenced node '" + ref.get('ref') + "' was not found.")
                    
                    pn.transitions[reference.get('id')]._references.add(ref.get('id'))
                
                for arc in current.findall('arc'):
                    source = net.find('.//*[@id="' + arc.get('source') + '"]')
                    try:
                        while source.tag[:9] == 'reference':
                            source = net.find('.//*[@id="' + source.get('ref') + '"]')
                    except:
                        raise Exception("Referenced node '" + arc.get('source') + "' was not found.")
                    
                    target = net.find('.//*[@id="' + arc.get('target') + '"]')
                    try:
                        while target.tag[:9] == 'reference':
                            target = net.find('.//*[@id="' + target.get('ref') + '"]')
                    except:
                        raise Exception("Referenced node '" + arc.get('target') + "' was not found.")
                    
                    if source.tag == 'place':
                        source = pn.places[source.get('id')]
                        target = pn.transitions[target.get('id')]
                    else:
                        source = pn.transitions[source.get('id')]
                        target = pn.places[target.get('id')]
                        
                    try:
                        weight = int(arc.find('inscription/text').text)
                    except:
                        weight = 1
                    pn.add_arc(source, target, weight, arc.get('id'))
                
            pnets.append(pn)
        
        return pnets
        
    
    def to_ElementTree(self):
        
        net = self._tree.find('net')
        page = net.find('page')
        toolspecific = net.find('toolspecific[@tool="PNLab"]')
        if toolspecific is not None:
            tmp = _get_treeElement(toolspecific, 'scale')
            tmp = _get_treeElement(tmp, 'scale')
            tmp = _get_treeElement(tmp, 'text')
            tmp.text = str(self.scale)
        
        for p in self.places.itervalues():
            if p.hasTreeElement:
                p._merge_treeElement()
            else:
                page.append(p._build_treeElement())
        
        for t in self.transitions.itervalues():
            if t.hasTreeElement:
                t._merge_treeElement()
            else:
                page.append(t._build_treeElement())
        
        for p in self.places.itervalues():
            for arc in p._incoming_arcs.itervalues():
                if arc.hasTreeElement:
                    arc._merge_treeElement()
                else:
                    page.append(arc._build_treeElement())
            
            for arc in p._outgoing_arcs.itervalues():
                if arc.hasTreeElement:
                    arc._merge_treeElement()
                else:
                    page.append(arc._build_treeElement())
        
        
        return copy.deepcopy(self._tree)
    
    @classmethod
    def from_pnml_file(cls, filename):
        et = ET.parse(filename)
        # http://wiki.tei-c.org/index.php/Remove-Namespaces.xsl
        xslt='''<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
        <xsl:output method="xml" indent="no"/>
        
        <xsl:template match="/|comment()|processing-instruction()">
            <xsl:copy>
              <xsl:apply-templates/>
            </xsl:copy>
        </xsl:template>
        
        <xsl:template match="*">
            <xsl:element name="{local-name()}">
              <xsl:apply-templates select="@*|node()"/>
            </xsl:element>
        </xsl:template>
        
        <xsl:template match="@*">
            <xsl:attribute name="{local-name()}">
              <xsl:value-of select="."/>
            </xsl:attribute>
        </xsl:template>
        </xsl:stylesheet>
        '''
        xslt_doc=ET.parse(io.BytesIO(xslt))
        transform=ET.XSLT(xslt_doc)
        et=transform(et)
        filename = os.path.basename(filename)
        if '.pnml.xml' in filename:
            filename = filename[:filename.rfind('.pnml.xml')]
        elif '.pnml' in filename: 
            filename = filename[:filename.rfind('.pnml')]
        elif '.' in filename:
            filename = filename[:filename.rfind('.')]
            
        return PetriNet.from_ElementTree(et, name = filename)
    
    def to_pnml_file(self, file_name):
        et = self.to_ElementTree()
        et.write(file_name, encoding = 'utf-8', xml_declaration = True, pretty_print = True)