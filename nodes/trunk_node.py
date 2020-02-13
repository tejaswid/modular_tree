from bpy.types import Node, Operator
import bpy
import random
from bpy.props import IntProperty, FloatProperty, EnumProperty, BoolProperty, StringProperty
from .base_node import BaseNode
from ..tree import MTree

class MtreeTrunk(Node, BaseNode):
    """
    This is the Trunk Node in the UI to control how the trunk is generated.
    """
    # \todo Write a better description of shape. Check units for the terms and enter them into the description

    # Label of the node in blender. Use this to access this node in a python script.
    bl_label = "Trunk Node"
    # Seed value for randomization
    seed = IntProperty(default=1, update=BaseNode.property_changed, description="Seed for randomization. default=1")
    # Length of the trunk
    length = FloatProperty(min=0, default=25, update=BaseNode.property_changed,
                           description="Length of the trunk along its skeleton curve. units=m, min=0, max=inf, default=25")
    # Radius of the trunk at the base
    radius = FloatProperty(min=.0005, default=.5, update=BaseNode.property_changed,
                           description="Radius of the trunk at the base. units=m, min=0.005, max=inf, default=0.5")
    # radius of the trunk at the end of the trunk
    end_radius = FloatProperty(min=0, max=1, default=0, update=BaseNode.property_changed,
                               description="Radius at the top of the trunk. units=m, min=0, max=1, default=0")
    # Number of elements (loops or cylinders) the trunk has along its axis
    resolution = FloatProperty(min=.002, default=1, update=BaseNode.property_changed,
                               description="Number of segments per metre along the trunk's curve."
                                           " min=0.002, max=inf, default=1")
    # Parameter to tune the change in radius of the trunk as a function of the length
    shape = FloatProperty(min=0.01, default=1, update=BaseNode.property_changed,
                          description="Degree of the polynomial that determines how the radius changes with length."
                                      " min=0.01, max=inf, default=1")
    # Parameter to tune how irregular the trunk looks
    randomness = FloatProperty(min=0, max=0.5, default=.1, update=BaseNode.property_changed,
                               description="Tune how irregular the trunk looks. min=0, max=0.5, default=0.1")
    # Parameter to tune how close to the axis the trunk is
    axis_attraction = FloatProperty(min=0, max=1, default=.25, update=BaseNode.property_changed,
                                    description="Amount by which the trunk is attracted to the vertical axis, min=0,"
                                                "max=1, default=0.25")
    # Boolean to use grease pencil
    use_grease_pencil = BoolProperty(default=False, update=BaseNode.property_changed,
                                     description="Boolean if grease pencil has to be used. default=False")

    properties = ["seed", "length", "radius", "end_radius", "resolution", "shape",
                  "randomness", "axis_attraction", "use_grease_pencil"]
    
    def init(self, context):
        """
        Initializer
        """
        self.outputs.new('TreeSocketType', "0")
        # Name of the node in blender
        self.name = MtreeTrunk.bl_label

    def draw_buttons(self, context, layout):
        """
        Draws buttons in the UI
        """
        col = layout.column()
        col.prop(self, "use_grease_pencil")
        if self.use_grease_pencil:
            # only radius and resolution are available in the grease pencil mode
            col.prop(self, "radius")
            col.prop(self, "resolution")
            op = layout.operator("mtree.update_gp_strokes", text="update strokes")  # calls ExecuteMtreeNodeTreeOperator.execute
            op.node_group_name = self.id_data.name  # set name of node group to operator
        else:
            for i in self.properties[:-1]:
                col.prop(self, i)
        
    def execute(self, tree):
        """
        The function that is called when the trunk has to be generated.

        This is the function that passes the parameters from the UI to the underlying tree generation functions.
        """
        # get index of node in node tree and use it as tree function identifier
        creator = self.id_data.nodes.find(self.name)
        if self.use_grease_pencil:
            # Generate the trunk from the grease pencil using the parameters set in the UI
            tree.build_tree_from_grease_pencil(.4/self.resolution, self.radius, creator)
        else:
            random.seed(self.seed)
            # Generate the trunk using the parameters set in the UI
            tree.add_trunk(self.length, self.radius, self.end_radius, self.shape,
                           self.resolution, self.randomness, self.axis_attraction, creator)

        for output in self.outputs:
            # here the execute function is called recursively on first output of all nodes,
            # the second output of all nodes, etc
            links = output.links
            if len(links) > 0:
                links[0].to_node.execute(tree, self)


class UpdateGreasePencil(Operator):
    """Update grease pencil strokes"""
    bl_idname = "mtree.update_gp_strokes"
    bl_label = "Reset Active Tree Object"
    
    node_group_name = StringProperty()

    def execute(self, context):
        parameters_node = [i for i in bpy.data.node_groups[self.node_group_name].nodes if i.bl_idname == "MtreeParameters"][0]
        parameters_node.has_changed = True
        parameters_node.execute()
        return {'FINISHED'}
