from bpy.types import Node
from bpy.props import IntProperty, FloatProperty, EnumProperty, BoolProperty, StringProperty
from .base_node import BaseNode
from ..tree import MTree
import random


class MtreeBranch(Node, BaseNode):
    """
    This is the Branch Node in the UI to control how the branch is generated.
    """
    # Label of the node in blender. Use this to access this node in a python script.
    bl_label = "Branch Node"
    # Seed for random number generation
    seed = IntProperty(update=BaseNode.property_changed, description="Seed for random number generation")
    # Checkbox to enable advanced settings
    advanced_settings = BoolProperty(default=False, update=BaseNode.property_changed,
                                     description="Toggle the display of advanced properties")
    # Number of locations at which the branch can split
    amount = IntProperty(min=0, default=20, update=BaseNode.property_changed,
                         description="Number of locations at which the branch splits. min=0, max=inf, default=20")
    # Angle with which the fork splits from the main branch in radians
    split_angle = FloatProperty(min=0, max=1.5, default=.6, update=BaseNode.property_changed,
                                description="Angle with which the fork splits from the main branch."
                                            " min=0, max=1.5 (90deg), default=0.6")
    # Maximum number of forks per split location
    max_split_number = IntProperty(min=0, default=3, update=BaseNode.property_changed,
                                   description="Maximum number of forks per split location. min=0, max=inf, default=3")
    # Radius of the fork at the base (the split location)
    radius = FloatProperty(min=0, max=1, default=.6, update=BaseNode.property_changed,
                           description="Radius of fork at the base (the split location). min=0, max=1, default=0.6")
    # Radius of the fork at the end
    end_radius = FloatProperty(min=0, max=1, default=0, update=BaseNode.property_changed,
                               description="Radius of the fork at the end. min=0, max=1, default=0")
    # Minimum height at which a split occurs
    min_height = FloatProperty(min=0, max=.999, default=.1, name="start", update=BaseNode.property_changed,
                               description="Minimum height at which the split occurs. min=0, max=0.999, default=0.1")
    # Length of the branch
    length = FloatProperty(min=0, default=7, update=BaseNode.property_changed,
                           description="Length of the branch in metres. min=0, max=inf, default=7")
    # Length of the branches at the base of the tree
    shape_start = FloatProperty(min=0, default=1, update=BaseNode.property_changed,
                                description="Length of the branches at the base of the tree. min=0, default=1")
    # Length of the branches at the top of the tree
    shape_end = FloatProperty(min=0, default=1, update=BaseNode.property_changed,
                              description="Length of the branches at the top of the tree. min=0, default=1")
    # How the length of the branches should change as a function of height - determines the shape of the canopy
    shape_convexity = FloatProperty(default=.3, update=BaseNode.property_changed,
                                    description="Tune the length of the branches as a function of height")
    # Number of elements (loops or cylinders) the branch has along its axis
    resolution = FloatProperty(min=.002, default=1, update=BaseNode.property_changed,
                               description="Number of elements along the branch's axis. min=0.002, max=inf, default=1")
    # Parameter to tune how irregular the branch looks
    randomness = FloatProperty(default=.15, update=BaseNode.property_changed,
                               description="Tune how irregular the branch looks. default=0.15")
    # How likely it is for a branch to fork
    split_proba = FloatProperty(min=0, max=1, default=.1, update=BaseNode.property_changed,
                                description="Tune how likely it is for a branch to fork. min=0, max=1, default=0.1")
    # How constrained on the horizontal axis the forks from the splits are
    split_flatten = FloatProperty(min=0, max=1, default=.5, update=BaseNode.property_changed,
                                  description="How constrained on the horizontal axis the forks are."
                                              " min=0, max=1, default=0.5")
    # Boolean indicating if the branch can spawn leaves
    can_spawn_leafs = BoolProperty(default=True, update=BaseNode.property_changed,
                                   description="Boolean indicating if a branch can spawn leaves")
    # Tune how much the branches go towards the ground/sky
    gravity_strength = FloatProperty(default=.3, update=BaseNode.property_changed,
                                     description="Tune how much the branches go towards the floor or sky. default=0.3")
    # Tune how much the branches avoid the floor
    floor_avoidance = FloatProperty(min=0, default=1, update=BaseNode.property_changed,
                                    description="Tune how much the branches avoid the floor. min=0, default=1")

    properties = ["seed", "amount", "split_angle", "max_split_number", "radius", "end_radius", "min_height",
                  "length", "shape_start", "shape_end", "shape_convexity", "resolution", "randomness",
                  "split_proba", "split_flatten", "gravity_strength", "floor_avoidance", "can_spawn_leafs"]

    def init(self, context):
        """
        Initialization
        """
        self.outputs.new('TreeSocketType', "0")
        self.inputs.new('TreeSocketType', "Tree")
        self.name = MtreeBranch.bl_label

    def draw_buttons(self, context, layout):
        """
        Draws buttons in the UI
        """
        layout.prop(self, "advanced_settings")
        if self.advanced_settings:
            # if advanced settings are enabled then draw all settings
            for i in self.properties:
                layout.prop(self, i)
        else:
            # else draw just a few settings
            props = ["seed", "amount", "split_angle", "radius", "min_height", "length",
                     "shape_convexity", "resolution", "randomness", "split_proba",
                     "gravity_strength", "floor_avoidance", "can_spawn_leafs"]
            for i in props:
                layout.prop(self, i)

    def execute(self, tree, input_node):
        """
        The function that is called when the branch has to be generated.

        This is the function that passes the parameters from the UI to the underlying tree generation functions.
        """
        random.seed(self.seed)
        # get index of node in node tree and use it as tree function identifier
        creator = self.id_data.nodes.find(self.name)
        selection = 0 if input_node is None else input_node.id_data.nodes.find(input_node.name)

        # Generate the branches using the parameters set in the UI
        tree.add_branches(self.amount, self.split_angle, self.max_split_number, self.radius, self.end_radius,
                          self.min_height, self.length, self.shape_start, self.shape_end, self.shape_convexity,
                          self.resolution, self.randomness, self.split_proba, self.split_flatten,
                          self.gravity_strength, self.floor_avoidance, self.can_spawn_leafs, creator, selection )

        for output in self.outputs:
            # here the execute function is called recursively on first output of all nodes,
            # the second output of all nodes, etc.
            links = output.links
            if len(links) > 0:
                links[0].to_node.execute(tree, self)
            