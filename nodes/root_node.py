from bpy.types import Node
import random
from bpy.props import IntProperty, FloatProperty, EnumProperty, BoolProperty, StringProperty
from .base_node import BaseNode
from ..tree import MTree

class MtreeRoots(Node, BaseNode):
    """
    This is the Roots Node in the UI to control how the roots are generated.
    """
    # Label of the node in blender. Use this to access this node in a python script.
    bl_label = "Roots Node"
    # Seed for random number generation
    seed = IntProperty(default=9, update = BaseNode.property_changed, description="Seed for random number generation")
    # Length of the roots in metres
    length = FloatProperty(min=0, default=14, update = BaseNode.property_changed,
                           description="Length of the roots in metres. min=0, max=inf, default=14")
    # Number of elements (loops or cylinders) the root has along its axis
    resolution = FloatProperty(min=.002, default=2, update = BaseNode.property_changed,
                               description="Number of elements along the root's axis. min=0.002, max=inf, default=2")
    # How likely it is for a root to fork
    split_proba = FloatProperty(min=0, max=1, default=.2, update = BaseNode.property_changed,
                                description="How likely it is for a root to fork. min=0, max=1, default=0.2")
    # Parameter to tune how irregular the branch looks
    randomness = FloatProperty(min=0, max=0.5, default=.2, update = BaseNode.property_changed,
                               description="Tune how irregular the root looks. min=0, max=0.5, default=0.2")

    properties = ["seed", "length", "resolution", "split_proba", "randomness"]
    
    def init(self, context):
        """
        Initialization
        """
        self.inputs.new('TreeSocketType', "0")
        self.name = MtreeRoots.bl_label

    def draw_buttons(self, context, layout):
        """
        Draw buttons in the UI
        """
        col = layout.column()
        for i in self.properties:
            col.prop(self, i)
    
    def execute(self, tree, input_node):
        """
        The function that is called when the root has to be generated.

        This is the function that passes the parameters from the UI to the underlying tree generation functions.
        """
        random.seed(self.seed)
        # get index of node in node tree and use it as tree function identifier
        creator = self.id_data.nodes.find(self.name)
        # Generate the roots using the parameters set in the UI
        tree.roots(self.length, self.resolution, self.split_proba, self.randomness, creator)            