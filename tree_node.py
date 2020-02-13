from math import inf


class MTreeNode:
    """
    This is the basic unit of the entire tree.
    """
    def __init__(self, position, direction, radius, creator=0):
        """
        Initialization

        :param position: Vector - Position of the node in local space
        :param direction: Vector -  Direction of the node in local space
        :param radius: float - Radius of the node (at the start?)
        :param creator: uint - ID of the node function that created this node
        """
        self.position = position        # Vector - position of node in local space
        self.direction = direction      # Vector - direction of node in local space
        self.radius = radius            # float - radius of node
        self.children = []              # list of MTreeNode - the extremities of the node.
                                        # First child is the continuity of the branch
        self.creator = creator          # int - the id of the NodeFunction that created the node
        self.growth = 0                 # float - when growing nodes it is useful to know how much they should grow.
                                        # this parameter gives the length a node has grown since grow was called.
        self.growth_goal = 0            # float - How much the node should be grown.
        self.growth_radius = 0          # float - The radius of the node when it first started growing
        self.can_be_splitted = True     # bool - if true the node can be split (can have more than 1 children)
        self.position_in_branch = 0     # float - 0 when node is at the beginning of a branch, 1 when it is at the end
        self.is_branch_origin = False   # bool - indicates if this is the origin of a tree element or not.
        self.can_spawn_leaf = True      # bool - if true this branch segment can spawn leaves
        self.bone_name = None           # string - name of bone the branch is bound to, if any.

    def get_grow_candidates(self, candidates, creator):
        """
        Get candidates that can be grown.
        Recursively populates @candidates with nodes starting from the current node until the last child
        that the same @creator created. (leafs of tree if a leaf has the right creator)
        Returns min and max height over all the candidates

        :param candidates: The list of candidates that can be grown. This is the main output.
        :param creator: The ID of the NodeFunction that created this node
        :return: the minimum and maximum height of the node and all its children
        """
        # initializing max and min heights
        max_height = -inf
        min_height = inf

        # only extremities can be grown

        # if the node does not have any children
        if len(self.children) == 0:
            if self.creator == creator:     # only grow the node created by creator
                candidates.append(self)
                max_height = min_height = self.position.z   # get height of node
            
        for child in self.children:
            min_h, max_h = child.get_grow_candidates(candidates, creator)   # recursively call function to children
            min_height = min(min_height, min_h)  # min height is now the min between itself and the min height of child
            max_height = max(max_height, max_h)  # max height is now the max between itself and the max height of child
        
        return min_height, max_height

    def set_positions_in_branches(self, current_distance=0, distance_from_parent=0):
        """
        Set each node position_in_branch property to it's correct value.
        To do so, the function returns the length of current branch.

        :param current_distance:
        :param distance_from_parent:
        :return:
        """
        current_distance += distance_from_parent    # increase current distance by the distance from node parent

        # if node is the end of the branch,
        if len(self.children) == 0:
            self.position_in_branch = 1     # return the length of the branch and set the position_in_branch to 1
            return current_distance
        
        for child in self.children[1:]:     # recursively call the function on all side children
            # the current_distance of a side child is 0 since it is the beginning of a new branch
            child.set_positions_in_branches(0, 0)

        distance_to_child = (self.position - self.children[0].position).length
        branch_length = self.children[0].set_positions_in_branches(current_distance, distance_to_child)

        self.position_in_branch = 0 if branch_length == 0 else current_distance / branch_length
        return branch_length
        
    def get_split_candidates(self, candidates, creator, start, end):
        """
        :param candidates:
        :param creator:
        :param start:
        :param end:
        """
        # if there is only one child and this node is not the origin of a branch
        if len(self.children) == 1 and not self.is_branch_origin \
                and self.creator == creator and end >= self.position_in_branch >= start:
            if end <= start:
                self.position_in_branch = 0
            else:
                # transform the position in branch so that a position at offset is 0
                self.position_in_branch = (self.position_in_branch - start) / (end-start)
            candidates.append(self)
        
        for child in self.children:
            child.get_split_candidates(candidates, creator, start, end)

    def get_leaf_candidates(self, candidates, max_radius):
        """
         recursively populates a list with position, direction radius of all modules susceptible to create a leaf
        """
        if self.radius <= max_radius and self.can_spawn_leaf:
            extremity = len(self.children) == 0
            direction = self.direction if extremity else (self.children[0].position - self.position)
            length = direction.magnitude
            if length != 0:
                direction /= length
            candidates.append((self.position, direction, length, self.radius, extremity))
        
        for child in self.children:
            child.get_leaf_candidates(candidates, max_radius)

    def get_branches(self, positions, radii, first_branch=False, parent_pos=None):
        """
        populate list of list of points of each branch
        """
        
        pos = parent_pos if first_branch else self.position
        positions[-1].extend([pos.x, pos.y, pos.z, 0])  # add position to last branch
        radii[-1].append(self.radius)   # add radius to last branch

        for i, child in enumerate(self.children):
            if i > 0:   # if child is begining of new branch
                positions.append([])    # add empty branch for position
                radii.append([])        # add empty branch for radius
            child.get_branches(positions, radii, i > 0, self.position)

    def get_armature_data(self, min_radius, bone_index, armature_data, parent_index):
        """
        armature data is list of list of (position_head, position_tail, radius_head, radius_tail, parent bone index) of
        each node. bone_index is a list of one int
        """
        # if radius is greater than max radius, add data to armature data
        if self.radius > min_radius and len(self.children) > 0:
            child = self.children[0]
            armature_data[-1].append((self.position, child.position, self.radius, child.radius, parent_index))
            bone_name = "bone_" + str(bone_index[0])
            index = bone_index[0]
            bone_index[0] += 1
        else:
            bone_name = "bone_" + str(parent_index)
            index = parent_index

        self.bone_name = bone_name

        for i, child in enumerate(self.children):
            if i > 0 and child.radius > min_radius:
                armature_data.append([])
            child.get_armature_data(min_radius, bone_index, armature_data, index)
            
    def recalculate_radius(self, base_radius):
        """
        Rescales the radius of each branch according to its parent's radius.
        Used when creating tree from grease pencil.

        :param base_radius: float - base radius
        """
        # Multiply the radius of the node with the base radius
        self.radius *= base_radius
        for i, child in enumerate(self.children):
            if i == 0:
                # scale the radius by the @base_radius
                child.recalculate_radius(base_radius)
            else:
                # scale the radius by 0.9 -\todo this is a hard coded number - may be ideal to make it a parameter
                child.recalculate_radius(self.radius * .9)
