'''
Created on Apr 23, 2013

@author: Patrick
'''

####class definitions####

import bpy
import math
from mathutils import Vector
from mathutils.geometry import intersect_point_line
import contour_utilities
from bpy_extras.view3d_utils import location_3d_to_region_2d
from bpy_extras.view3d_utils import region_2d_to_vector_3d
from bpy_extras.view3d_utils import region_2d_to_location_3d
#from development.contour_tools import contour_utilities

class ContourControlPoint(object):
    
    def __init__(self, x, y, color = (1,0,0,1), size = 2, mouse_radius=10):
        self.x = x
        self.y = y
        self.world_position = Vector((0,0,0)) #to be updated later
        self.color = color
        self.size = size
        self.mouse_rad = mouse_radius
        
    def mouse_over(self,x,y):
        dist = (self.x -x)**2 + (self.y - y)**2
        #print(dist < 100)
        if dist < 100:
            return True
        else:
            return False

    
class ContourCutLine(object): 
    
    def __init__(self, x, y, view_dir):
        self.head = ContourControlPoint(x,y, color = (1,0,0,1))
        self.tail = ContourControlPoint(x,y, color = (0,1,0,1))
        self.view_dir = view_dir  #this is imporatnt...no reason contours cant bend
        self.target = None
        self.depth = None #perhaps we need a depth value? 
        self.updated = False
        self.plane_pt = None
        self.plane_no = None
        self.seed_face_index = None
        self.verts = []
        self.verts_simple = []
        self.eds_simple = []
        self.edges = []
        
    def draw(self,context):
        
        #draw connecting line
        points = [(self.head.x,self.head.y),(self.tail.x,self.tail.y)]
        contour_utilities.draw_polyline_from_points(context, points, (0,.5,1,1), 1, "GL_LINE_STIPPLE")
        #draw head #draw tail
        contour_utilities.draw_points(context, points, (1,0,.2,1), 5)
        
        if self.plane_pt:
            point = location_3d_to_region_2d(context.region, context.space_data.region_3d,self.plane_pt)
            contour_utilities.draw_points(context, [point], (1,0,.2,1), 5)
        
        if self.verts:
            contour_utilities.draw_3d_points(context, self.verts, (0,1,.2,1), 1)
            
        if self.verts_simple:
            contour_utilities.draw_3d_points(context, self.verts_simple, (0,.2,1,1), 3)
            
        #draw contour points? later
    
    def hit_object(self,context):
        ob = context.object
        region = context.region  
        rv3d = context.space_data.region_3d
        
        pers_mx = rv3d.perspective_matrix  #we need the perspective matrix
        inv_persx_mx = pers_mx.inverted() #and we need to invert it...for some reason    
        pos = rv3d.view_location
        
        #midpoint of the  cutline and world direction of cutline
        screen_coord = (self.head.x + self.tail.x)/2, (self.head.y + self.tail.y)/2
        
        view_x = rv3d.view_rotation * Vector((1,0,0))
        view_y = rv3d.view_rotation * Vector((0,1,0))
        view_z = rv3d.view_rotation * Vector((0,0,1))
        cut_vec = (self.tail.x - self.head.x)*view_x + (self.tail.y - self.head.y)*view_y
        cut_vec.normalize()
        
        self.plane_no = cut_vec.cross(view_z).normalized()
        
        
        vec = region_2d_to_vector_3d(region, rv3d, screen_coord)
        loc = region_2d_to_location_3d(region, rv3d, screen_coord, vec)
        
        #raycast what I think is the ray onto the object
        #raycast needs to be in ob coordinates.
        a = loc + 3000*vec
        b = loc - 3000*vec
    
        mx = ob.matrix_world
        imx = mx.inverted()
        hit = ob.ray_cast(imx*a, imx*b)    
        
        if hit[2] != -1:
            self.plane_pt = mx * hit[0]
            self.seed_face_index = hit[2] 
        
    def cut_object(self,context, bme):
        
        mx = context.object.matrix_world
        pt = self.plane_pt
        pno = self.plane_no
        if pt and pno:
            cross = contour_utilities.cross_section_seed(bme, mx, pt, pno, self.seed_face_index, debug = True)   
            if cross:
                self.verts = [mx*v for v in cross[0]]
                self.eds = cross[1]
        else:
            print('no hit! aim better')
        
    def simplify_cross(self,segments):
        [self.verts_simple, self.eds_simple] = contour_utilities.space_evenly_on_path(self.verts, self.eds, segments)
        
          
    def active_element(self,context,x,y):
        active_head = self.head.mouse_over(x, y)
        active_tail = self.tail.mouse_over(x, y)
        
        mouse_loc = Vector((x,y,0))
        head_loc = Vector((self.head.x, self.head.y, 0))
        tail_loc = Vector((self.tail.x, self.tail.y, 0))
        intersect = intersect_point_line(mouse_loc, head_loc, tail_loc)
        
        dist = (intersect[0] - mouse_loc).length_squared
        bound = intersect[1]
        active_self = (dist < 100) and (bound < 1) and (bound > 0) #TODO:  make this a sensitivity setting
        
        if active_head and active_tail and active_self: #they are all clustered together
            #print('returning head but tail too')
            return self.head
        
        elif active_tail:
            #print('returning tail')
            return self.tail
        
        elif active_head:
            #print('returning head')
            return self.head
        
        elif active_self:
            #print('returning line')
            return self
        
        else:
            #print('returning None')
            return None
#cut line, a user interactive 2d line which represents a plane in 3d splace
    #head (type conrol point)
    #tail (type control points)
    #target mesh
    #view_direction (crossed with line to make plane normal for slicing)
    
    #draw method
    
    #new control point project method
    
    #mouse hover line calc
    
    
#retopo object, surface
    #colelction of cut lines
    #collection of countours to loft
    
    #n rings (crosses borrowed from looptools)
    #n follows (borrowed from looptools and or bsurfaces)
    
    #method contours from cutlines
    
    #method bridge contours