import bpy
import os
from bpy.types import Node, Operator
import bmesh
from mathutils import Vector, Matrix
from bpy.props import IntProperty, FloatProperty, EnumProperty, BoolProperty, StringProperty, PointerProperty
from .base_node import BaseNode
from .tree_parameters_node import generate_tree_object
from ..tree import MTree
from random import random, seed


class MtreeTwig(Node, BaseNode):
    """
    This is the Twig Node in the UI to control how the twig is generated.
    """
    # Label of the node in blender. Use this to access this node in a python script.
    bl_label = "Twig Node"
    # Seed for random number generation
    seed = IntProperty(default=1, description="Seed for random number generation. default=1")
    # Length of the twig
    length = FloatProperty(min=.01, default=3, description="Length of the twig in metres. min=0.01, default=3")
    # Radius of the twig
    radius = FloatProperty(min=0.001, default=.15,
                           description="Radius of the twig in metres. min=0.001, default=0.15")
    # todo what is this?
    branch_number = IntProperty(min=0, default=6, description="What is this? min=0, default=6")
    # Parameter to tune how irregular the twig looks
    randomness = FloatProperty(default=.7, min=0, description="Tune how irregular the branch looks. min=0, default=0.7")
    # Number of elements (loops or cylinders) the twig has along its axis
    resolution = FloatProperty(min=.1, default=8,
                               description="Number of elements along the twig's axis. min=0.1, max=inf, default=8")
    # Tune how much the twigs go towards the ground/sky
    gravity_strength = FloatProperty(default=4, description="Tune how much the twigs avoid the floor. default=4")
    # Tune How flat the twig is
    flatten = FloatProperty(min=0, max=1, default=.6,
                            description="Tune how flat the twig is. min=0, max=1, default=0.6")
    # The object to use as the leaf
    leaf_object = PointerProperty(type=bpy.types.Object, description="The object to use as the leaf")
    # Type of leaf
    leaf_type = EnumProperty(
        items=[('palmate', 'Palmate', ''), ('serrate', 'Serrate', ''), ('palmatisate', 'Palmatisate', ''), ('custom', 'Custom', '')],
        name="leaf type",
        default="palmate",
        description="The type of leaf to use - palmate, serrate or palmatisate. default=palmate")
    # The size of the leaf todo check units
    leaf_size = FloatProperty(min=0, default=1, description="Size of the leaf. min=0, deafult=1")

    def init(self, context):
        """
        Initialization
        """
        self.name = MtreeTwig.bl_label

    def draw_buttons(self, context, layout):
        """
        Draws buttons in the UI
        """
        op = layout.operator("object.mtree_twig", text='execute')   # will call TwigOperator.execute
        op.node_group_name = self.id_data.name  # set name of node group to operator
        op.node_name = self.name

        layout.prop(self, "seed")
        layout.prop(self, "length")
        layout.prop(self, "radius")
        layout.prop(self, "branch_number")
        layout.prop(self, "randomness")
        layout.prop(self, "resolution")
        layout.prop(self, "gravity_strength")
        layout.prop(self, "flatten")
        layout.prop(self, "leaf_type")
        if self.leaf_type == "custom":
            layout.prop(self, "leaf_object")
        layout.prop(self, "leaf_size")

    def execute(self):
        """
        The function that is called when the twig has to be generated.

        This is the function that passes the parameters from the UI to the underlying tree generation functions.
        """
        addon_path = os.path.join(os.path.dirname(__file__), '..')
        leaf_path = addon_path + "/resources/materials.blend\\Object\\"
        material_path = addon_path + "/resources/materials.blend\\Material\\"

        seed(self.seed)

        if bpy.data.materials.get("twig") is None:
            bpy.ops.wm.append(filename="twig", directory=material_path)

        if self.leaf_type != "custom":
            bpy.ops.wm.append(filename=self.leaf_type, directory=leaf_path)
            self.leaf_object = bpy.context.view_layer.objects.selected[-1]

        tree = MTree()
        leaf_candidates = tree.twig(self.radius, self.length, self.branch_number, self.randomness,
                                    self.resolution, self.gravity_strength, self.flatten)
        twig_ob = bpy.context.object
        if twig_ob is not None and twig_ob.get("is_twig") is None:
            twig_ob = None
        twig_ob = generate_tree_object(twig_ob, tree, 8, "is_twig")
        twig_ob.active_material = bpy.data.materials.get("twig")
        scatter_object(leaf_candidates, twig_ob, self.leaf_object, self.leaf_size)
        if self.leaf_type != "custom" and self.leaf_object is not None:
            bpy.data.objects.remove(self.leaf_object, do_unlink=True)   # delete leaf object


class TwigOperator(Operator):
    """
    create a branch with leafs
    """
    bl_idname = "object.mtree_twig"
    bl_label = " Make Twig"
    bl_options = {"REGISTER", "UNDO"}
 
    node_group_name = StringProperty()
    node_name = StringProperty()

    def execute(self, context):        
        node = bpy.data.node_groups[self.node_group_name].nodes[self.node_name]
        node.execute()
        return {'FINISHED'}


def scatter_object(leaf_candidates, ob, dupli_object, leaf_size):
    if dupli_object is None:    # return when leaf object is not specified
        return
    leafs = []  # container for all created leafs
    collection = bpy.context.scene.collection   # get scene collection
    ob_transform = ob.matrix_world
    for position, direction, length, radius, is_end in leaf_candidates:
        new_leaf = dupli_object.copy()  # copy leaf object
        new_leaf.data = new_leaf.data.copy()
        dir_rot = Vector((1, 0, 0)).rotation_difference(direction)    # rotation of new leaf
        
        loc, rot, scale = new_leaf.matrix_world.decompose()
        mat_scale = Matrix()     # scale of new leaf
        random_scale = 1 + ((random()-.5) * .4)
        for i in range(3):
            mat_scale[i][i] = scale[i] * random_scale
        new_leaf.matrix_world = ob_transform @ ((Matrix.Translation(position) @ dir_rot.to_matrix().to_4x4() @ mat_scale))
        c =random()
        color_vertices(new_leaf, (c, c, c, c))
        leafs.append(new_leaf)
        collection.objects.link(new_leaf)

    # deselecting everything so no unwanted object will be joined as a leaf
    bpy.ops.object.select_all(action='DESELECT')
    for leaf in leafs:
        leaf.select_set(state=True)     # selecting all leafs
    ob.select_set(state=True)   # selecting twig
    bpy.context.view_layer.objects.active = ob  # make twig the active object so that leafs are joined to it
    bpy.ops.object.join()   # join leafs to twig


def color_vertices(ob, color):
    """
    Paints all vertices of object @ob with @color

    :param ob: The object that has to be coloured
    :param color: The color to use, a 4-tuple (r, g, b, a)
    """
    mesh = ob.data
    if mesh.vertex_colors:
        vcol_layer = mesh.vertex_colors.active
    else:
        vcol_layer = mesh.vertex_colors.new()

    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            vcol_layer.data[loop_index].color = color
