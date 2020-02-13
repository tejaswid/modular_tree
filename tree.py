from .tree_node import MTreeNode
from mathutils import Vector, Quaternion
from .geometry import random_tangent, build_module_rec, to_array
from .grease_pencil import process_gp_layer
# import numpy as np
from collections import deque
from random import random, randint, sample
from math import pi


class MTree:
    """
    This is the main class of this module and defines the entire tree.
    """
    def __init__(self):
        self.stem = None    # MTreeNode - the first node of the tree
        self.verts = []     # list of Vector - the vertices of the tree
        self.faces = []     # list of list of int - the faces of the tree

    def build_mesh_data(self, resolution):
        verts = []
        faces = []
        weights = []
        uvs = []
        bone_weights = dict()
        build_module_rec(self.stem, resolution, verts, faces, uvs, weights, bone_weights)
        return to_array(verts), faces, weights, uvs, bone_weights

    def create_object(self):
        """
        At the moment this class does nothing. Not sure what it does or why it is necessary
        :return:
        """
        pass

    def add_trunk(self, length, radius, end_radius, shape, resolution, randomness, axis_attraction, creator):
        """
        Add a trunk to the tree using input parameters
        :param length: Length of the trunk, in metres, along its skeleton curve
        :param radius: Radius of the trunk, in metres, at the base
        :param end_radius: Radius of the trunk, in metres, at the top
        :param shape: Degree of the polynomial that maps the radius of the trunk as a function of the trunk's length
        :param resolution:  Number of segments per metre along the trunk's curve
        :param randomness: Amount of irregularity, i.e. disturbance tangential to the tree skeleton
        :param axis_attraction: A measure of straightness (how close the trunk is to the vertical axis)
        :param creator: ID of the node that creates the trunk
        :return: Nothing
        """
        # The first node of the tree is at (0,0,0) with its direction vertically upwards.
        self.stem = MTreeNode(Vector((0, 0, 0)), Vector((0, 0, 1)), radius, creator)
        self.stem.is_branch_origin = True   # Set it to be the origin of a tree element

        remaining_length = length
        extremity = self.stem   # extremity is always the current last node of the trunk
        while remaining_length > 0:
            if remaining_length < 1/resolution:
                # last last branch is shorter so that the trunk is exactly of required length
                resolution = 1/remaining_length

            # generate a vector in the plane tangential to the direction of the extremity
            tangent = random_tangent(extremity.direction)

            # direction of new TreeNode
            direction = extremity.direction + tangent * randomness / resolution
            course_correction = Vector((-extremity.position.x, -extremity.position.y, 1/direction.z))
            direction += course_correction * axis_attraction
            direction.normalize()
            # position of new TreeNode
            position = extremity.position + extremity.direction / resolution
            # radius of new TreeNode
            rad = radius * (remaining_length/length)**shape + (1 - remaining_length/length) * end_radius

            new_node = MTreeNode(position, direction, rad, creator)     # new TreeNode
            extremity.children.append(new_node)  # Add new TreeNode to extremity's children
            extremity = new_node    # replace extremity by new TreeNode
            remaining_length -= 1/resolution

    def grow(self, length, shape_start, shape_end, shape_convexity, resolution,
             randomness, split_proba, split_angle, split_radius, split_flatten,
             end_radius, gravity_strength, floor_avoidance, can_spawn_leaf, creator, selection):
        """
        Grows a tree element

        :param length:
        :param shape_start:
        :param shape_end:
        :param shape_convexity:
        :param resolution:
        :param  randomness:
        :param split_proba:
        :param split_angle:
        :param split_radius:
        :param split_flatten:
        :param end_radius:
        :param gravity_strength:
        :param floor_avoidance:
        :param can_spawn_leaf:
        :param creator:
        :param selection:
        """
        grow_candidates = []
        self.stem.get_grow_candidates(grow_candidates, selection)   # get all leafs of valid creator

        print(grow_candidates)

        branch_length = 1/resolution    # branch length is used multiple times so best to calculate it once

        def shape_length(x):
            """
            Returns the shape of the curve, which is parametrized by the position along the curve
            y(x) = shape_start + (shape_end - shape_start)*x  - 4*shape_convexity*x*(x-1)
            y(0) = shape_start, y(1) = shape_end, y(0.5) = 0.5*(shape_start + shape_end) + shape_convexity

            The interpolation is linear if shape_convexity is zero. Else it is quadratic.

            :param x: parameter along the curve, x=0 is the start and x=1 is the end of the curve
            :return: y(x)
            """
            return -4*shape_convexity*x*(x-1) + x*shape_end + (1-x)*shape_start
        
        for node in grow_candidates:
            node.growth = 0
            # add length to node growth goal
            node.growth_goal = max(0.001, length * shape_length(node.position_in_branch))
            node.growth_radius = node.radius

        # convert grow_candidates to deque for performance (lots of adding/removing last element)
        grow_candidates = deque(grow_candidates)

        # grow all candidates until there are none (all have grown to their respective length)
        while len(grow_candidates) > 0:
            node = grow_candidates.popleft()

            # get the type of node
            # (a) children_number = 1 <- normal branch node
            # (b) children_number = 2 <- forking node
            children_number = 1 if random() > split_proba or node.is_branch_origin else 2
            # compute tangent to the node direction
            tangent = random_tangent(node.direction)
            # if the tangent is pointing downwards or if the branch forks at this node
            if tangent.z < 0 or children_number > 1:
                tangent.z *= (1-split_flatten)  # factor in how horizontal the branch should be
                tangent.normalize()             # get the unit tangent

            for i in range(children_number):
                # compute how much the new direction will be changed by tangent
                # -------------------------------------------------------------
                # 1. Amount of deviation
                # (a) the deviation is @randomness
                # (b) the deviation is the @split_angle
                deviation = randomness if children_number == 1 else split_angle
                # 2. Direction of new node
                # (a) linear interpolation of (tangent * deviation) and old direction
                # (b) linear interpolation of (tangent * i * split_angle) and old direction
                direction = node.direction.lerp(tangent * (i - .5) * 2, deviation)  # direction of new node

                direction += Vector((0, 0, -1)) * gravity_strength / 10 / resolution  # apply gravity
                if floor_avoidance != 0:
                    # if -1 then the branches must stay below ground, if 1 they must stay above ground
                    below_ground = -1 if floor_avoidance < 0 else 1
                    distance_from_floor = max(.01, abs(node.position.z))
                    # get how much the branch is going towards the floor
                    direction_toward_ground = max(0, - direction.z * below_ground)
                    floor_avoidance_strength = direction_toward_ground * .3 / distance_from_floor * floor_avoidance

                    # if the branch is too much towards the floor, break it
                    if floor_avoidance_strength > .1 * (1 + floor_avoidance):
                        break
                    direction += Vector((0, 0, 1)) * floor_avoidance_strength
                direction.normalize() 
                if i == 0:
                    position = node.position + direction * branch_length    # position of new node
                else:
                    t = (tangent - tangent.project(node.direction)).normalized()
                    position = (node.position + node.children[0].position)/2 + t*node.radius
                growth = min(node.growth_goal, node.growth + branch_length)     # growth of new node

                # radius of new node
                radius = node.growth_radius * ((1 - node.growth / node.growth_goal)
                                               + end_radius * node.growth / node.growth_goal)
                if i > 0:
                    radius *= split_radius   # forked branches have smaller radii

                if children_number == 1:
                    print("Normal branch: i: ", i, " ", creator, position)
                else:
                    print("Forking branch: i: ", i, " ", creator, position)

                # Create a new child node with the same creator
                child = MTreeNode(position, direction, radius, creator)
                child.growth_goal = node.growth_goal
                child.growth = growth
                child.growth_radius = node.growth_radius if i == 0 else node.growth_radius * split_radius
                child.can_spawn_leaf = can_spawn_leaf
                if i > 0:
                    child.is_branch_origin = True
                node.children.append(child)
                if growth < node.growth_goal:
                    grow_candidates.append(child)   # if child can still grow, add it to the grow candidates

    def split(self, amount, angle, max_split_number, radius, start, end, flatten, creator, selection):
        """
        Creates a split location
        """
        split_candidates = []
        self.stem.set_positions_in_branches()
        self.stem.get_split_candidates(split_candidates, selection, start, end)
        
        amount = min(amount, len(split_candidates))
        split_candidates = sample(split_candidates, amount)
        for node in split_candidates:
            n_children = randint(1, max_split_number)
            tangent = random_tangent(node.direction)
            flatten_tangent = tangent.copy()
            flatten_tangent.z = 0
            tangent = tangent.lerp(flatten_tangent, flatten)
            tangent.normalize()
            rot = Quaternion(node.direction, 2*pi/n_children)
            for i in range(n_children):
                t = node.position_in_branch
                direction = node.direction.lerp(tangent, angle * (1-t/2)).normalized()
                position = (node.position + node.children[0].position)/2
                position += (tangent - tangent.project(node.direction)).normalized() * node.radius
                rad = node.radius * radius
                child = MTreeNode(position, direction, rad, creator)
                child.position_in_branch = node.position_in_branch
                child.is_branch_origin = True
                child.can_spawn_leaf = False
                node.children.append(child)
                tangent = rot @ tangent

    def add_branches(self, amount, angle, max_split_number, radius, end_radius, start, length,
                     shape_start, shape_end, shape_convexity, resolution, randomness,
                     split_proba, split_flatten, gravity_strength, floor_avoidance, can_spawn_leaf, creator, selection):
        split_creator = creator - 0.5
        split_selection = selection
        grow_selection = creator - 0.5
        grow_creator = creator
        self.split(amount, angle, max_split_number, radius, start, 1, split_flatten, split_creator, split_selection)
        self.grow(length, shape_start, shape_end, shape_convexity, resolution,
                  randomness, split_proba, 0.3, 0.9, split_flatten, end_radius,
                  gravity_strength, floor_avoidance, can_spawn_leaf, grow_creator, grow_selection)

    def roots(self, length, resolution, split_proba, randomness, creator):
        if len(self.stem.children) == 0:    # roots can only be added on a trunk on non 0 length
            return
        
        roots_origin = MTreeNode(self.stem.position, -self.stem.direction, self.stem.radius, -1)
        roots_origin.is_branch_origin = True
        # stem is set as branch origin, so it cannot be aplit by split function.
        # second children of stem will then always be root origin
        self.stem.children.append(roots_origin)

        self.grow(length, 1, 1, 0, resolution, randomness, split_proba, .5, .6, 0, 0, -.1, -1, False, creator, -1)

    def get_leaf_emitter_data(self, number, weight, max_radius, spread, flatten, extremity_only):
        leaf_candidates = []
        self.stem.get_leaf_candidates(leaf_candidates, max_radius)
        if not extremity_only:
            if number > len(leaf_candidates):
                # remove extremities from factor because they won't participate in candidate addition
                factor = number // len([i for i in leaf_candidates if not i[-1]])
                add_candidates(leaf_candidates, factor)
            leaf_candidates = sample(leaf_candidates, number)
        else:
            leaf_candidates = [i for i in leaf_candidates if i[-1]]
        verts = []
        faces = []

        for position, direction, length, radius, is_end in leaf_candidates:
            tangent = Vector((0, 0, 1)).cross(direction).normalized()
            if not is_end:  # only change direction when leaf is not at a branch extremity
                tangent = (randint(0, 1) * 2 - 1) * tangent  # randomize sign of tangent
                direction = direction.lerp(tangent, spread)
                direction.z *= (1-flatten)
                direction.z -= weight
                direction.normalize()
            x_axis = direction.orthogonal()
            y_axis = direction.cross(x_axis)
            v1 = position + x_axis * .01
            v3 = position + y_axis * .01
            v2 = position - x_axis * .01
            n_verts = len(verts)
            verts.extend([v3, v2, v1])
            faces.append((n_verts, n_verts+1, n_verts+2))
        
        return verts, faces

    def twig(self, radius, length, branch_number, randomness, resolution, gravity_strength, flatten):
        self.stem = MTreeNode(Vector((0, 0, 0)), Vector((1, 0, 0)), radius*.1, 0)
        self.grow(1, 1, 1, 0, resolution, randomness/2/resolution, 0, .2, 0, 0, 0, .1, 0, True, 1, 0)
        self.add_branches(branch_number, .5, 2, .7, .1, 0, length*.7, .5, .5, 0, resolution,
                          randomness/resolution, .1/resolution, flatten, gravity_strength/resolution, 0, True, 2, 1)

        leaf_candidates = []
        self.stem.get_leaf_candidates(leaf_candidates, radius)
        return [i for i in leaf_candidates if i[-1]]

    def get_armature_data(self, min_radius):
        bone_index = [0]
        armature_data = [[]]
        parent_index = 0
        self.stem.get_armature_data(min_radius, bone_index, armature_data, parent_index)
        return armature_data

    def build_tree_from_grease_pencil(self, point_dist, radius, creator):
        strokes, splits = process_gp_layer(point_dist)
        nodes = []

        for i, s in enumerate(strokes):
            nodes.append([])
            last_node = None
            origin_radius = 1
            n = len(s)
            if n < 2:
                break
            for j, p in enumerate(s):
                radius_multiplier = 1 - j/(n-1)
                if j < n-1:
                    direction = (s[j+1] - p).normalized()
                else:
                    direction = (p - last_node.position).normalized()
                new_node = MTreeNode(p, direction, origin_radius * radius_multiplier, creator)
                if last_node is not None:
                    last_node.children.append(new_node)
                last_node = new_node
                nodes[-1].append(new_node)
        
        for parent_index, node_index, child_index in splits:
            nodes[parent_index][node_index].children.append(nodes[child_index][0].children[0])
            print(len(nodes))
            print(parent_index)
        
        self.stem = nodes[0][0]
        self.stem.recalculate_radius(radius)


def add_candidates(leaf_candidates, dupli_number):
    """
    create new leaf candidates by interpolating existing ones

    :param leaf_candidates:
    :param dupli_number:
    """
    new_candidates = []

    for position, direction, length, radius, is_end in leaf_candidates:
        if is_end:   # no new candidate can be created from end_leaf
            continue
        for i in range(dupli_number):
            pos = position + direction*length * (i+1)/(dupli_number+2)
            new_candidates.append((pos, direction, length, radius, is_end))
    leaf_candidates.extend(new_candidates)
