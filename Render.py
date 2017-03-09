# coding: iso-8859-15

# 2016-09-03
# Axel Engström, Sci14

# This module was first built for the BMP format, but still images are also
# compatible with the GIF format.

from math import sqrt

def int_round(x):
    return int(round(x))

class _DrawingObject:
    '''
    Baseclass for all graphics objects.
    Methods include: move,copy,rotate
    '''
    def __init__(self, _pixels=None):
        if _pixels is None:
            _pixels = {}
        self.pixels = _pixels
        
    def __add__(self, drawing_object):
        '''
        Adding is not commutative, the rightmost operand's pixels are layered above the 
        leftmost operand's. Using sum(list_of_objects) will make the image layebored in
        the order such that the latter items are in the foreground.
        
        
        Currently does not preserve attributes from combined objects.
        This is to be resolved in future versions by accessing an attribute containing
        a list of the combined objects.
        '''
        if drawing_object == 0:
            return self
        elif isinstance(drawing_object, _DrawingObject):
            merged_dict = self.pixels.copy()
            merged_dict.update(drawing_object.pixels)
            return _DrawingObject(merged_dict)
        else:
            raise TypeError('Can only add _DrawingObject to 0 or another _DrawingObject')
    
    __radd__ = __add__
    
    def _set_pixel(self,x,y,color):
        '''Set a given pixel with coordinates x,y to string color.'''
        self.pixels[x,y] = color
    
    def move(self,dx,dy):
        '''Shifts the object a specified dx and dy.'''
        self.pixels = {(coord[0]+dx, coord[1]+dy):color for coord,color in self.pixels.items()}
    
    def copy(self):
        return _DrawingObject(self.pixels)
    
    def rotate(self,x,y,angle,radians=True):
        '''
        Rotate the object around a given point for an angle specified in either
        radians or degrees.
        Parameters: rotate(self,x,y,angle,radians=True)
        '''
        pass

class Line(_DrawingObject):
    def __init__(self,x1,y1,x2,y2,color='black'):
        '''My own line drawing algorithm'''
        _DrawingObject.__init__(self)
        self.x1, self.y1 = x1,y1
        self.x2, self.y2 = x2,y2
        self.color=color
        
        ### Line initialising
        vertical = x2-x1 == 0
        
        k = float((y2-y1))/(x2-x1) if not vertical else 0
        
        # Truth values for ŽsteepŽ plotted for each quadrant.
        # \ 1/
        # 0\/0
        #  /\ 
        # / 1\
        steep = k<-1 or k>1 or vertical
        
        # Booleans act as 1 or 0, representing the index.
        # This is to limit the case to only incrementing,
        # reducing the amount of special cases needed.
        minloc = min([(x1,y1),(x2,y2)], key=lambda loc: loc[steep])
        
        # This is to avoid gaps in the line, we now get a unique corresponding
        # value for each step.
        if steep:
            # Iterate over y
            k **= -1 if not vertical else 1  # 0 can not be raised to negative power.
            for ystep in range(int_round(abs(y1-y2))):
                x,y= minloc[0] + ystep*k, ystep + minloc[1]
                self._set_pixel(x,y,color)
        else:
            # Iterate over x
            for xstep in range(int_round(abs(x1-x2))):
                x,y= minloc[0] + xstep, xstep*k + minloc[1]
                self._set_pixel(x,y,color)
    
class Circle(_DrawingObject):
    def __init__(self,xmid,ymid,r,color='black'):
        _DrawingObject.__init__(self)
        self.xmid = xmid
        self.ymid = ymid
        self.r = r
        self.color = color
        
        ### Circle initialising
        xn,yn = round(r), 0
        octant = [(xn,yn)]
        
        while xn >= yn:                # floating point error leads to sqrt(-|a|)
            xn = sqrt(xn*xn - 2*yn - 1) if xn != sqrt(3) and xn != 0 else 0
            yn += 1
            octant.append((xn,yn))
            
        quarter = octant + [(loc[1], loc[0]) for loc in octant]
        semi = quarter + [(-loc[0], loc[1]) for loc in quarter]
        circle = semi + [(loc[0], -loc[1]) for loc in semi]
        
        for x,y in circle:
            self._set_pixel(x+xmid, y+ymid, color)
        
class Point(_DrawingObject):
    '''3*3 Pixels.'''
    def __init__(self,x,y,color='black',r=1):
        _DrawingObject.__init__(self)
        self.x = x
        self.y = y
        self.color = color
        x,y = int_round(x), int_round(y) #range takes int params.
        for dx in range(x-r,x+r):
            for dy in range(y-r,y+r):
                self._set_pixel(dx, dy, color)
            
class ConnectPoints(_DrawingObject):
    '''
    Connect given points with lines.
    Attributes include: self.joints, self.pixels
    '''
    def __init__(self,locs,color='black',close=False):
        _DrawingObject.__init__(self)
        self.joints = locs
        self.color=color
        
        ### ConnectPoints initialising
        lines=0
        previous = locs[0]
        for x2,y2 in locs[1:]:
            x1,y1 = previous
            lines += Line(x1,y1,x2,y2, color)
            previous = x2,y2
        if close:
            (x1,y1),(x2,y2) = previous, locs[0]
            lines += Line(x1,y1,x2,y2, color)
        self.pixels=lines.pixels

class Function(_DrawingObject):
    def __init__(self, function, xmin,xmax, color='black',resolution=1): ### BUG NOTE xmin may be negative
        '''Argument function is a standard python function which returns an integer given one as input.'''
        self.func = function
        _DrawingObject.__init__(self)
        locs=[]
        for x in range(0,xmax-xmin+1,resolution):
            y = function(x)
            locs.append((x+xmin, y))
            except (SyntaxError,ZeroDivisionError) as err:
                if err is ZeroDivisionError:
                    # avoid the vertical asymptote line being drawn
                    self.pixels.update(ConnectPoints(locs,color=color).pixels)
                else:
                    raise err
        self.pixels.update(ConnectPoints(locs,color=color,close=True).pixels)
        
class Canvas: ### NOTE should make Graphics class that (perhaps inherits from dict) has attribute dictionary and method _set_pixel().
    '''
    Class that renders any _DrawingObject.
    Can transform the indexed color map to the index stream used in GIF.
    '''
    def __init__(self,Width,Height):
        self.Width = Width
        self.Height = Height
        
        ###ALERT Change this structure to a set with constant bgcolor
        #self.BG_COLOR='white'
        self.chunks = {(x,y):'white' for x in range(Width) for y in range(Height)}

        self.CENTER = Width/2.0, Height/2.0
        self.origin = (0,0)
    
    
    def set_pixel(self, x,y, color='black'):
        '''
        A set_pixel method is introduced to class Canvas for optimisation and display purposes.
        
        _DrawingObject's ._set_pixel method aims to keep the data intact, as opposed to this one.
        This is because different transformations such as scaling and rotating wouldn't want the
        error prone data loss, whilst simply displaying pixels inherently removes information.
        '''
        x0,y0 = self.origin
        roundx,roundy = int_round(x+x0), int_round(y+y0)
        if roundx in range(self.Width+1) and roundy in range(self.Height+1):
            self.chunks[roundx+x0,roundy+y0] = color
    
        
    def add_graphics(self, *drawings):
        for drawing in drawings:
            if isinstance(drawing, _DrawingObject):
                for (x,y), color in drawing.pixels.items():
                    self.set_pixel(x,y,color)
            else:
                raise TypeError('Only instances of baseclass _DrawingObject are compatible.')
            
    def set_origin(self,x,y):
        '''
        Relative to the current origin, identical to 'translate' in postscript.
        '''
        x0,y0 = self.origin
        self.origin = (x+x0,y+y0)

    def save_state(self):
        self.saved_origin = self.origin

    def restore_state(self):
        self.origin = self.saved_origin

    def scaleX(self):pass
    def scaleY(self):pass

    def get_index_stream(self):
        '''
        Translate self.chunks to a 1 dimensional stream
        of color-indices specified in GIF color tables.
        '''
        color_index = {'white':0,'black':1,'red':2,'green':3,'blue':4,'yellow':5,'magenta':6,'cyan':7}
        # Flattening self.chunks
        stream = [color_index[self.chunks[x,self.Height-y-1]] for y in range(self.Height) for x in range(self.Width)]
        return stream

