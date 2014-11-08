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
    REGULAR = 'regular'

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
            nodeType -- A class variable from the PlaceTypes or TransitionTypes classes.
            position -- An instance of the Vec2 utility class.
            """
        
        if not name:
            raise Exception('A Node name must be a non-empty string.')
        
        if nodeType == PlaceTypes.PREDICATE and name[:2] == 'r.':
            name = name[2:]
            self._isRunningCondition = True
        else:
            self._isRunningCondition = False
        
        if nodeType == PlaceTypes.PREDICATE and name[:2] == 'e.':
            name = name[2:]
            self._isEffect = True
        else:
            self._isEffect = False
            
        if nodeType in [PlaceTypes.ACTION, PlaceTypes.TASK] and name[:2] == 'o.':
            name = name[2:]
            self._isOutput = True
        else:
            self._isOutput = False
        
        if nodeType == PlaceTypes.PREDICATE and name[:4] == 'NOT_':
            name = name[4:]
            self._isNegated = True
        else:
            self._isNegated = False
        
        self._name = name
        self._type = nodeType
        self.petri_net = None
        self.position = Vec2(position)
        self._incoming_arcs = {}
        self._outgoing_arcs = {}
        self.hasTreeElement = False
        self._references = set()
        self._id = name.replace(' ', '_').replace('(', '__').replace(')', '__').replace(',', '_')
    
    @property
    def name(self):
        """Returns the name of the node."""
        return self._name
    
    @name.setter
    def name(self, value):
        """Sets the name of the node. Throws an exception if name is None or an empty string."""
        
        if not value:
            raise Exception('A Node name must be a non-empty string.')
        
        if self.type == PlaceTypes.PREDICATE and value[:2] == 'r.':
            value = value[2:]
            self._isRunningCondition = True
        else:
            self._isRunningCondition = False
        
        if self.type == PlaceTypes.PREDICATE and value[:2] == 'e.':
            value = value[2:]
            self._isEffect = True
        else:
            self._isEffect = False
            
        if self.type in [PlaceTypes.ACTION, PlaceTypes.TASK] and value[:2] == 'o.':
            value = value[2:]
            self._isOutput = True
        else:
            self._isOutput = False
        
        if self._type == PlaceTypes.PREDICATE and value[:4] == 'NOT_':
            value = value[4:]
            self._isNegated = True
        
        self._name = value
    
    @property
    def _full_name(self):
        """Read-only property. Name of the node, INCLUDING the type prefix."""
        return self._type[0] + '.' + ('e.' if self._isEffect else '') + ('r.' if self._isRunningCondition else '') + ('o.' if self._isOutput else '') + ('NOT_' if self._isNegated else '') + self._name
    
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
    
    @abc.abstractmethod
    def _merge_treeElement(self):
        """Merges the current ElementTree element information with the previously loaded info."""
        return
    
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
        elif name[:7] == 'action.':
            name = name[7:]
            place_type = PlaceTypes.ACTION
        elif name[:2] == 't.':
            name = name[2:]
            place_type = PlaceTypes.TASK
        elif name[:5] == 'task.':
            name = name[5:]
            place_type = PlaceTypes.TASK
        elif name[:2] == 'r.':
            name = name[2:]
            place_type = PlaceTypes.REGULAR
        elif name[:8] == 'regular.':
            name = name[8:]
            place_type = PlaceTypes.REGULAR
        elif name[:2] == 'p.':
            name = name[2:]
        elif name[:10] == 'predicate.':
            name = name[10:]
        
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
            if p_type in [PlaceTypes.ACTION, PlaceTypes.PREDICATE, PlaceTypes.TASK, PlaceTypes.REGULAR]:
                place_type = p_type
        except:
            pass
        
        try:
            capacity = int(toolspecific_el.find('capacity/text').text)
        except:
            capacity = 0
            
        try:
            if name[:2] == 'r.':
                running = True
                name = name[2:]
            else:
                running = int(toolspecific_el.find('isRunningCondition/text').text)
        except:
            running = False
        
        try:
            if name[:2] == 'e.':
                effect = True
                name = name[2:]
            else:
                effect = int(toolspecific_el.find('isEffect/text').text)
        except:
            effect = False
            
        try:
            if name[:2] == 'o.':
                output = True
                name = name[2:]
            else:
                output = int(toolspecific_el.find('isOutput/text').text)
        except:
            output = False
            
        try:
            if name[:4] == 'NOT_':
                negated = True
                name = name[4:]
            else:
                negated = int(toolspecific_el.find('isNegated/text').text)
        except:
            negated = False
        
        #NOTE: PNML renaming is done by the PetriNet procedure where this node is created.
        
        p = Place(name, place_type, position, initMarking, capacity)
        p._isRunningCondition = running
        p._isEffect = effect
        p._isNegated = negated
        p._isOutput = output
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
        
        tmp = ET.SubElement(place_toolspecific, 'isRunningCondition')
        tmp = ET.SubElement(tmp, 'text')
        tmp.text = str(int(self._isRunningCondition))
        
        tmp = ET.SubElement(place_toolspecific, 'isEffect')
        tmp = ET.SubElement(tmp, 'text')
        tmp.text = str(int(self._isEffect))
        
        tmp = ET.SubElement(place_toolspecific, 'isOutput')
        tmp = ET.SubElement(tmp, 'text')
        tmp.text = str(int(self._isOutput))
        
        tmp = ET.SubElement(place_toolspecific, 'isNegated')
        tmp = ET.SubElement(tmp, 'text')
        tmp.text = str(int(self._isNegated))
        
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
        
        place_isRunningCondition = _get_treeElement(place_toolspecific, 'isRunningCondition')
        tmp = _get_treeElement(place_isRunningCondition)
        tmp.text = str(int(self._isRunningCondition))
        
        place_isEffect = _get_treeElement(place_toolspecific, 'isEffect')
        tmp = _get_treeElement(place_isEffect)
        tmp.text = str(int(self._isEffect))
        
        place_isOutput = _get_treeElement(place_toolspecific, 'isOutput')
        tmp = _get_treeElement(place_isOutput)
        tmp.text = str(int(self._isOutput))
        
        place_isNegated = _get_treeElement(place_toolspecific, 'isNegated')
        tmp = _get_treeElement(place_isNegated)
        tmp.text = str(int(self._isNegated))
        
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
        
        #NOTE: PNML renaming is done by the PetriNet procedure where this node is created.
        
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
        
        self._treeElement = self.__repr__()
        
        return arc
    
    def _merge_treeElement(self):
        
        el = self.petri_net._tree.find('//*[@id="' + self._treeElement + '"]')
        if el is None:
            print 'DEBUG - TE: ' + self._treeElement + ' - TreeName: ' + self.petri_net.name
            return
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
    
    '''
    #TODO (Possibly):
    Add prefix field to CONFIG dicts (instead of always taking the first letter of type).
    '''
    
    PLACE_CONFIG = {
                PlaceTypes.ACTION: {
                            'fill' : '#00EE00',
                            'outline' : '#00AA00'
                            },
                PlaceTypes.PREDICATE: {
                            'fill' : '#4444FF',
                            'outline' : '#0000BB'
                            },
                PlaceTypes.TASK: {
                            'fill' : '#EEEE00',
                            'outline' : '#AAAA00'
                            },
                PlaceTypes.REGULAR: {
                            'fill' : '#FFFFFF',
                            'outline' : '#444444'
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
        
        self._place_counter = 0
        self._transition_counter = 0
        
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
        
    
    def add_place(self, p):
        """Adds a place from the Petri Net.
        
        Clears the arcs from the place object and adds it to the Petri Net.
        
        Arguments:
        p -- A Place object to insert
        
        """
        
        self._place_counter += 1
        p._id = "P{:0>3d}".format(self._place_counter)
        
        p._incoming_arcs = {}
        p._outgoing_arcs = {}
        self.places[repr(p)] = p
        
        p.petri_net = self
    
    def add_transition(self, t, overwrite = False):
        """Adds a transition from the Petri Net.
        
        Clears the arcs from the transition object and adds it to the Petri Net.
        
        Arguments:
        t -- A Transition object to insert
        """
        
        self._transition_counter += 1
        t._id = "T{:0>3d}".format(self._transition_counter)
        
        t._incoming_arcs = {}
        t._outgoing_arcs = {}
        self.transitions[repr(t)] = t
        
        t.petri_net = self
    
    def remove_place(self, place):
        """Removes a place from the Petri Net.
        
        Argument 'place' should be either a Place object,
        or a representation of a Place object [i. e. repr(place_obj)].
        
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
        
        p = self.places.pop(key)
        p._references.clear()
        p.petri_net = None
        
        return p
    
    def remove_transition(self, transition):
        """Removes a transition from the Petri Net.
        
        Argument 'transition' should be either a Transition object,
        or a representation of a Transition object [i. e. str(transition_obj)].
        
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
        
        t = self.transitions.pop(key)
        t._references.clear()
        t.petri_net = None
        
        return t
    
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
                    
                    place_id = ref.get('id')
                    pn._place_counter += 1
                    new_id = 'P{:0>3d}'.format(pn._place_counter)
                    for e in net.findall('.//referencePlace[@ref="' + place_id + '"]'):
                        e.set('ref', new_id)
                    for e in net.findall('.//arc[@source="' + place_id + '"]'):
                        e.set('source', new_id)
                    for e in net.findall('.//arc[@target="' + place_id + '"]'):
                        e.set('target', new_id)
                    ref.set('id', new_id)
                    pn.places[reference.get('id')]._references.add(new_id)
                
                for ref in net.findall('.//referenceTransition'):
                    reference = ref
                    try:
                        while reference.tag[:9] == 'reference':
                            reference = net.find('.//*[@id="' + reference.get('ref') + '"]')
                    except:
                        raise Exception("Referenced node '" + ref.get('ref') + "' was not found.")
                    
                    transition_id = ref.get('id')
                    pn._transition_counter += 1
                    new_id = 'P{:0>3d}'.format(pn._transition_counter)
                    for e in net.findall('.//referenceTransition[@ref="' + transition_id + '"]'):
                        e.set('ref', new_id)
                    for e in net.findall('.//arc[@source="' + transition_id + '"]'):
                        e.set('source', new_id)
                    for e in net.findall('.//arc[@target="' + transition_id + '"]'):
                        e.set('target', new_id)
                    ref.set('id', new_id)
                    pn.places[reference.get('id')]._references.add(new_id)
                
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
        if toolspecific is None:
            toolspecific = ET.SubElement(net, 'toolspecific', {'tool' : 'PNLab'})
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