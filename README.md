shapeoko
========
Python utilities to communicate with the Shapeoko desktop CNC machine
and its GRBL controller.

bin/
----
shapeoko commandline utilities. run with --help option for more info.

- gcat: send a gcode file to the grbl controller
- gdraw: use keypresses to interactively move the shapeoko tool.
- gsh:  send gcode commands to the grbl controller

lib/
----
- grblstuff.py: library for chatting with the grbl.
- getch.py: get a keypress

data/
----
sample gcode files (give these to gcat), including the shapeoko hello world.

