## Description
This is a fork of the [modular_tree](https://github.com/MaximeHerpin/modular_tree) addon for blender, 
created by Maxime Herpin, to generate realistic trees using the node editor.

This fork is maintained by 
[Tejaswi Digumarti](https://tejaswid.github.io), 
[Lloyd Windrim](https://sydney.edu.au/engineering/about/our-people/academic-staff/lloyd-windrim.html) and 
[Mitch Bryson](http://www-personal.acfr.usyd.edu.au/m.bryson/)

## Overview of how the module works
The core unit of the tree is an object of the [MTreeNode](tree_node.py) class.
This object has properties that include its 
- position: <img src="https://render.githubusercontent.com/render/math?math=p_i">
- direction: <img src="https://render.githubusercontent.com/render/math?math=d_i">
- radius: <img src="https://render.githubusercontent.com/render/math?math=r_i">  
and others such as its creator and list of children.

### Tree
A Tree is a connection collection of objects of the **MTreeNode** class.
The entire tree can be split into meaningful *elements* which are the following
- Trunk 
- Branch
- Twig
- Root

#### Trunk
The Trunk is the most important part of the tree and is required to generate all the other *elements* of the tree.

A Trunk is created as follows.  
- The trunk is a collection of objects of the `MTreeNode` class.
- The first node, called the *stem* is an `MTreeNode` created at the location (0, 0, 0)
with its axis pointing vertically upwards i.e. along (0, 0, 1) and with the `radius` as specified.
- All the nodes (*segments*), except the node at the top are of length 1/`resolution`. 
The top node can be shorter based on the `length` of the trunk. 
- At every node 'j' after the *stem* a new node 'i' is created with the following parameters and appended
 to the list of `MTreeNode` objects; 
    - **direction** 
    <img src="https://render.githubusercontent.com/render/math?math=d_i = d_j%2Bt_j\cdot\frac{\text{randomness}}{\text{resolution}}%2B\text{axis_pull}_{ij}"> where   
        * <img src="https://render.githubusercontent.com/render/math?math=\text{axis_pull}_{ij}=Vec\(-p_j.x, -p_j.y, \frac{1}{d_i.z})\cdot\text{axis_attraction}">  
        * <img src="https://render.githubusercontent.com/render/math?math=t_j"> is a direction in the plane tangential to <img src="https://render.githubusercontent.com/render/math?math=d_j">.  
      This is followed by normalizing <img src="https://render.githubusercontent.com/render/math?math=d_i"> to a unit vector
    
    - **position**  (to the end of the previous node)
    <img src="https://render.githubusercontent.com/render/math?math=p_i=p_j%2B\frac{d_j}{\text{resolution}}">
    
    - **radius**
    <img src="https://render.githubusercontent.com/render/math?math=r_i=r_\text{stem}\cdot\ l^\text{shape}%2B(1-l)\cdot r_\text{end}">, where 
    <img src="https://render.githubusercontent.com/render/math?math=l=\frac{\text{remaining length}}{\text{length}}">
          
    - the remaining length along the curve of the trunk is updated as
    <img src="https://render.githubusercontent.com/render/math?math=\text{remaining_length}=\text{remaining_length} - \frac{1}{resolution}">
    - node 'i' is added as a child of node 'j'.
   
The parameters to tune the trunk are
- `length`: The length of the trunk, is metres, along its skeleton curve.
- `radius` (<img src="https://render.githubusercontent.com/render/math?math=r_\text{stem}">): The radius of the trunk, in metres, at the base
- `end_radius` (<img src="https://render.githubusercontent.com/render/math?math=r_\text{end}">): The radius of the trunk, in metres, at the top
- `shape`: The degree of the polynomial that maps the radius of the trunk as a function of the trunk's length.
- `resolution`: Number of segments per metre along the trunk's curve
- `randomness`: A value to tune how irregular the trunk is. Just a scale factor without any physical meaning.
- `axis_attraction`: A value to tune how vertical the trunk is. Just a scale factor without any physical meaning.