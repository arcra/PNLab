# -*- coding: utf-8 -*-
"""
@author: Adrián Revuelta Cuauhtli
"""

import copy
import re

from utils.Vector import Vec2
 
class PlaceTypes(object):
    """'Enum' class for Place types"""
    
    ACTION = 'action'
    PREDICATE = 'predicate'
    TASK = 'task'
    GENERIC = 'generic'

class TransitionTypes(object):
    """'Enum' class for Transition types"""
    IMMEDIATE = 'immediate'
    TIMED_STOCHASTIC = 'stochastic'

class Place(object):
    
    """Petri Net Place Class."""
    
    PLACE_REGEX = re.compile('^[A-Za-z][A-Za-z0-9_-]*$')
    
    def __init__(self, name, placeType = PlaceTypes.GENERIC, position = Vec2(), init_marking = 0):
        """Place Class' constructor
        
            Sets the name, type, position and initial marking of a place.
            
            Positional Arguments:
            name -- An alphabetic character, followed by any number of 
                    alphanumeric characters, dashes or underscores.
                    
            Keyword Arguments:
            placeType -- Should be set from one of the PlaceTypes Class' class members.
            position -- An instance of the Vec2 utility class.
            initial_marking -- An integer specifying the initial marking for this place.
        """
        
        if not Place.PLACE_REGEX.match(name):
            raise Exception('A place name should start with an alphabetic character, followed by any number of alphanumeric characters, dashes or underscores.')
        
        super(Place, self).__init__()
        
        self._name = name
        self._type = placeType
        self.init_marking = 0
        self.current_marking = self.init_marking
        self.position = Vec2(position)
        self._incoming_arcs = {}
        self._outgoing_arcs = {}
    
    @property
    def name(self):
        return self._name
    
    @property
    def type(self):
        return self._type
    
    @property
    def incoming_arcs(self):
        return copy.deepcopy(self._incoming_arcs)
    
    @property
    def outgoing_arcs(self):
        return copy.deepcopy(self._outgoing_arcs)
    
    def __str__(self):
        """ String representation of a Place object.
        
        It is formed with the first letter of the place type, a dot and the place name.
        """
        return self.type[0] + '.' + self.name

class Transition(object):
    
    """Petri Net Transition Class."""
    
    TRANSITION_REGEX = re.compile('^[A-Za-z][A-Za-z0-9_-]*$')
    
    def __init__(self, name, transitionType = TransitionTypes.IMMEDIATE, position = Vec2(), isHorizontal = True, rate = 1.0):
        
        """Transition Class' constructor
        
            Sets the name, type, position, orientation and rate of a transition.
            
            Positional Arguments:
            name -- An alphabetic character, followed by any number of 
                    alphanumeric characters, dashes or underscores.
                    
            Keyword Arguments:
            transitionType -- Should be set from one of the TransitionTypes Class' class members.
            position -- An instance of the Vec2 utility class.
            isHorizontal -- A boolean specifying whether the transition
                            should be drawn as a vertical bar or as a horizontal bar.
            rate -- For timed_stochastic transitions, the rate used to determine
                    the firing of a transition.
        """
        
        if not Transition.TRANSITION_REGEX.match(name):
            raise Exception('A transition name should start with an alphabetic character, followed by any number of alphanumeric characters, dashes or underscores.')
        
        super(Transition, self).__init__()
        
        self._name = name
        self.type = transitionType
        self.rate = 0
        self.isHorizontal = isHorizontal
        self.position = Vec2(position)
        self._incoming_arcs = {}
        self._outgoing_arcs = {}
    
    @property
    def name(self):
        return self._name
    
    @property
    def incoming_arcs(self):
        return copy.deepcopy(self._incoming_arcs)
    
    @property
    def outgoing_arcs(self):
        return copy.deepcopy(self._outgoing_arcs)
    
    def __str__(self):
        """ String representation of a Transition object.
        
        It is formed with the first letter of the
        transition type(i for IMMEDIATE and s for TIMED_STOCHASTIC),
        followed by a dot and the transition name.
        """
        
        return self.type[0] + '.' + self.name

class PetriNet(object):
    
    '''
    #TODO (Possibly):
    Add a 'saved' attribute, to know when some attribute has changed and
    saving is necessary before the object is destroyed.
    '''
    
    def __init__(self, name):
        """Petri Net Class' constuctor."""
        
        super(PetriNet, self).__init__()
        
        self.name = name
        self.places = {}
        self.transitions = {}
        self.scale = 1.0
    
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
        return True
    
    def remove_place(self, place):
        """Removes a place from the Petri Net.
        
        Argument 'place' should be either a Place object,
        or a string representation of a Place object [i. e. str(place_obj)]. 
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
        return True
    
    def remove_transition(self, transition):
        """Removes a transition from the Petri Net.
        
        Argument 'transition' should be either a Transition object,
        or a string representation of a Transition object [i. e. str(transition_obj)]. 
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
    