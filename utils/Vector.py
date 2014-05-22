# -*- coding: utf-8 -*-
'''
@author: Adrián Revuelta Cuauhtli
'''
import math

class Vec2(object):
    def __init__(self, x = 0, y = 0):
        super(Vec2, self).__init__()
        
        if isinstance(x, Vec2):
            self.x = round(x.x, 8)
            self.y = round(x.y, 8)
        else:
            self.x = round(x, 8)
            self.y = round(y, 8)
    
    def __add__(self, other):
        return Vec2(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other):
        return Vec2(self.x - other.x, self.y - other.y)
    
    def __mul__(self, k):
        return Vec2(self.x*k, self.y*k)
    
    def __rmul__(self, k):
        return self.__mul__(k)
    
    def __div__(self, k):
        return Vec2(self.x/k, self.y/k)
    
    def __truediv__(self, k):
        return Vec2(self.x/k, self.y/k)
    
    def __iadd__(self, other):
        self.x += other.x
        self.y += other.y
        return self
    
    def __isub__(self, other):
        self.x -= other.x
        self.y -= other.y
        return self
    
    def __imul__(self, k):
        self.x *= k
        self.y *= k
        return self 
    
    def __idiv__(self, k):
        self.x /= k
        self.y /= k
        return self
    
    def __itruediv__(self, k):
        self.x /= k
        self.y /= k
        return self
        
    def __neg__(self):
        return Vec2(-self.x, -self.y)
    
    def __str__(self):
        return '(' + str(self.x) + ', ' + str(self.y) + ')'
    
    @property
    def magnitude(self):
        return math.sqrt(self.x*self.x + self.y*self.y)
    
    @property
    def unit(self):
        m = self.magnitude
        if m == 0:
            raise Exception("Null Vectors don't have unit vector.")
        return self/self.magnitude
    
    @property
    def int(self):
        return Vec2(int(self.x), int(self.y))