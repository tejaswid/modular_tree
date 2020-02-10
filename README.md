### Description
This is a fork of the [modular_tree](https://github.com/MaximeHerpin/modular_tree) addon for blender, 
created by Maxime Herpin, to generate realistic trees using the node editor.

This fork is maintained by 
[Tejaswi Digumarti](https://tejaswid.github.io), 
[Lloyd Windrim](https://sydney.edu.au/engineering/about/our-people/academic-staff/lloyd-windrim.html) and 
[Mitch Bryson](http://www-personal.acfr.usyd.edu.au/m.bryson/)

### Overview of how the module works
The core unit of the tree is an object of the [MTreeNode](tree_node.py) class.
This object has properties that include its position, direction, radius, its creator (parent) and its children.

The entire tree is generated as a connected collection of MTreeNode objects.

### Code overview