from bpy.types import Node
from bpy.props import IntProperty, FloatProperty, EnumProperty, BoolProperty, StringProperty
from .base_node import BaseNode
from ..tree import MTree
import random


class MtreeSplit(Node, BaseNode):
    """
    This is the Split Node in the UI to control how a tree element has to split.
    This node should be followed by a Grow Node.
    """
    # Label of the node in blender. Use this to access this node in a python script.
    bl_label = "Split Node"
    # Seed for random number generation
    seed = IntProperty(default=0, update=BaseNode.property_changed, description="Seed for random number generation")
    # Number of locations at which a split can take place
    amount = IntProperty(min=0, default=20, update=BaseNode.property_changed,
                         description="Number of locations at which the element splits. min=0, max=inf, default=20")
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
    # Minimum height at which a split occurs
    start = FloatProperty(min=0, max=.999, default=0.3, name="start", update=BaseNode.property_changed,
                          description="Minimum height at which the split occurs. min=0, max=0.999, default=0.1")     # min height at which a split occurs

    # \todo Check what this is
    end = FloatProperty(min=0, max=1, default=1, update=BaseNode.property_changed)

    properties = ["seed", "amount", "split_angle", "max_split_number", "radius", "start", "end"]

    def init(self, context):
        """
        Initialization
        """
        self.outputs.new('TreeSocketType', "0")
        self.inputs.new('TreeSocketType', "Tree")
        self.name = MtreeSplit.bl_label

    def draw_buttons(self, context, layout):        
        """
        Draws buttons in the UI
        """
        col = layout.column()
        for i in self.properties:
            col.prop(self, i)
    
    def execute(self, tree, input_node):
        """
        The function that performs the split node operation.

        This is the function that passes the parameters from the UI to the underlying tree generation functions.
        """
        random.seed(self.seed)
        # get index of node in node tree and use it as tree function identifier
        creator = self.id_data.nodes.find(self.name)
        selection = 0 if input_node == None else input_node.id_data.nodes.find(input_node.name)

        tree.split(self.amount, self.split_angle, self.max_split_number, self.radius, self.start, self.end, 0, creator, selection)
        for output in self.outputs:
            # here the execute function is called recursively on first output of all nodes,
            # the second output of all nodes, etc
            links = output.links
            if len(links) > 0:
                links[0].to_node.execute(tree, self)
