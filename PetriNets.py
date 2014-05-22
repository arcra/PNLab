# -*- coding: utf-8 -*-
'''
@author: Adrián Revuelta Cuauhtli
'''

from utils.Vector import Vec2
 
class PlaceTypes(object):
    ACTION = 'action'
    PREDICATE = 'predicate'
    TASK = 'task'
    GENERIC = 'generic'

class TransitionTypes(object):
    IMMEDIATE = 'immediate'
    TIMED_STOCHASTIC = 'stochastic'

class Place(object):
    
    def __init__(self, name, placeType = PlaceTypes.GENERIC, position = Vec2(), init_marking = 0):
        super(Place, self).__init__()
        
        self._name = name
        self._type = placeType
        self.init_marking = 0
        self.current_marking = self.init_marking
        self.position = Vec2(position)
        self.incoming_arcs = {}
        self.outgoing_arcs = {}
    
    @property
    def name(self):
        return self._name
    
    @property
    def type(self):
        return self._type
    
    def __str__(self):
        return self.type[0] + '.' + self.name

class Transition(object):
    
    def __init__(self, name, transitionType = TransitionTypes.IMMEDIATE, position = Vec2(), isHorizontal = True, rate = 1.0):
        super(Transition, self).__init__()
        
        self._name = name
        self.type = transitionType
        self.rate = 0
        self.isHorizontal = isHorizontal
        self.position = Vec2(position)
        self.incoming_arcs = {}
        self.outgoing_arcs = {}
    
    @property
    def name(self):
        return self._name
    
    def __str__(self):
        return self.type[0] + '.' + self.name

class PetriNet(object):
    
    def __init__(self, name):
        super(PetriNet, self).__init__()
        
        self.name = name
        self.places = {}
        self.transitions = {}
        self.scale = 1.0
    
    def add_place(self, p, overwrite = False):
        key = str(p)
        if key in self.places:
            if not overwrite:
                return False
            else:
                self.places.pop(key)
        p.incoming_arcs = {}
        p.outgoing_arcs = {}
        self.places[key] = p
        return True
    
    def remove_place(self, p):
        key = str(p)
        if key not in self.places:
            return
        p = self.places.pop(key)
        for t in p.incoming_arcs.iterkeys():
            self.transitions[t].incoming_arcs.pop(key, None)
            self.transitions[t].outgoing_arcs.pop(key, None)
        
        for t in p.outgoing_arcs.iterkeys():
            self.transitions[t].incoming_arcs.pop(key, None)
            self.transitions[t].outgoing_arcs.pop(key, None)
    
    def add_transition(self, t, overwrite = False):
        key = str(t)
        if key in self.transitions:
            if not overwrite:
                return False
            else:
                self.transitions.pop(key)
        t.incoming_arcs = {}
        t.outgoing_arcs = {}
        self.transitions[key] = t
        return True
    
    def remove_transition(self, t):
        key = str(t)
        if key not in self.transitions:
            return True
        t = self.transitions.pop(key)
        for p in t.incoming_arcs.iterkeys():
            self.places[p].incoming_arcs.pop(key, None)
            self.places[p].outgoing_arcs.pop(key, None)
        
        for p in t.outgoing_arcs.iterkeys():
            self.places[p].incoming_arcs.pop(key, None)
            self.places[p].outgoing_arcs.pop(key, None)
    
    def is_arc(self, source, target):
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
        if not self.is_arc(source, target):
            raise Exception('Arcs should go either from a place to a transition or vice versa and they should exist in the PN.')
        
        src = str(source)
        trgt = str(target)
        if isinstance(source, Place):
            self.places[src].outgoing_arcs[trgt] = weight
            self.transitions[trgt].incoming_arcs[src] = weight
        else:
            self.transitions[src].outgoing_arcs[trgt] = weight
            self.places[trgt].incoming_arcs[src] = weight
    
    def remove_arc(self, source, target):
        if not self.is_arc(source, target):
            raise Exception('Arcs should go either from a place to a transition or vice versa.')
        
        src = str(source)
        trgt = str(target)
        if isinstance(source, Place):
            self.places[src].outgoing_arcs.pop(trgt, None)
            self.transitions[trgt].incoming_arcs.pop(src, None)
        else:
            self.transitions[src].outgoing_arcs.pop(trgt, None)
            self.places[trgt].incoming_arcs.pop(src, None)
    