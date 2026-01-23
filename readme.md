## Slothoth's DB Checker and Planner
This is a graph-based GUI modding tool. You can represent table insertions as Nodes, and visualise them by connecting 
foreign key connections. These connections link nodes, and allow updating a value in a node updating the downstream
node. It also allows importing any existing database mod as a graph. 

Possible foreign keys for a node are represented with Ports, which you can pull out to make a new node it references.

This graph representation can be saved and loaded, as well as exporting the graph to a simple modinfo for playtesting.

You will also need to edit the config.json file in this directory. 
You need to set CIV_INSTALL as the folder with your civilization VI.exe, WORKSHOP_FOLDER where your steam mods are, and last, your User civ directory.
Some sensible defaults are already in place, but at least the user civ directory will need to changed to whatever your username is.

Known Errors: 
- [x] Mods with Criteria like requiring Secret Society's are not caught.
- [x] Database currently does not absorb
