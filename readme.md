## Slothoth's DB Checker and Planner
This is a graph-based GUI modding tool. You can represent table insertions as Nodes, and visualise them by connecting 
foreign key connections. These connections link nodes, and allow updating a value in a node updating the downstream
node. It also allows importing any existing database mod as a graph. 

Possible foreign keys for a node are represented with Ports, which you can pull out to make a new node it references.

This graph representation can be saved and loaded, as well as exporting the graph to a simple modinfo for playtesting.

The mod also has a robust testing framework for valid SQL statements. A given node will highlight fields red if they
would lead to rejections. In addition, you can test the full mod you have built across the nodes, identifying foreign
key errors, and even explaining foreign key errors that result from a failed entry elsewhere.

The GUI also boasts advanced completions. Most every column that has a foreign key will let you select from existing values.
Even those without foreign keys that are in a small range (like Domain) will give you those options.

Non-insertion statements like UPDATE or DELETE are handled in their own node, which allows you to write your own SQL,
and see the effects of that statement on the database state of that specific age.

In addition to this graph planner, you can also run on an empty graph to debug other database problems with your existing
civ configuration. It harvests the current mod and DLC configuration you last had when you played civ and runs it manually
line by line, allowing you to find the causes of a mode failure.

You can set metadata about the generated mod like Mod id, description, name etc.

Currently the mod only allows loading one age at a time. In future, you will be able to have different graphs as different
tabs for different ages.

Localisation support is enabled. Fields in blue are fields that can be localised. Simply write the actual text you want to use and it will be converted into a LOC value when building the mod, and the LOC value will be inserted into the Localisation database under English.

I have implemented two Custom nodes, one is a GameEffects node that combines DynamicModifiers, Types, Modifiers,
ModifierArguments and ModifierStrings. It dynamically lists all possible Argument Names that can be specified.

I am likely going to implement similar nodes for Narratives, and for Units, and for Buildings. If you have any other
ideas for custom nodes, please suggest them.

# Features:
- package a given graph into a user friendly configuration with a .modinfo file and a main.sql  [x]
- Searchable dropdown in comboBox                                   [x]
- Metadata setter window. Also if this determines age, we should change possible values.   [x]
- ALWAYS mode uses subset of possible values present in all 3 ages   [x]
- Include some hotkeys in top section, like File [x]
- Convert existing mod to diagram[x]
- Toggle Types nodes being added for performance/clarity. [x]
- Dialogs converted into toasts where possible [x]
- ModifierArgs/RequirementArgs Value completions using Name   [x]
- ModifierArgs/RequirementArgs Name completions using ModifierType, EffectType from DynamicModifier  [x]
- autocompletes for Value on database [x]
- Effect Attach Modifier, ModifierArgument Extra Connection             [x]
- ModifierArguments entry                                               [x]
- make it so fields that cannot be left default show red when unedited or empty string. [x]
- colour combination logic for if red and blue because localised [x]
- Localisation entries (and displaying them as options in relevant gameplay graph) [x]
- harvest all possible values and store if the number of values is under 30. Use as suggestions for dynamic nodes [x]
- Updates and Deletes get imported as a type of node of 2 columns, with the PK values on one side being updated/deleted and the values themselves being changed [x]
- Updates and Deletes alter suggestible lists [ ]
- Updates and Deletes have chronology, requiring separate engine state we throw away [ ]
- Search highlights most used set (predefined/ user tracked?)     [ ]
- Sort port topdown so required ones are at the top                 [ ]
- refactor state validation to be threaded on start up, or at least only when graph planner opened [ ]
- Make it so arg values are highlighted if they are set to the default one. [ ]
- custom effect node uses colour to display which args need filled, and which are optional (deal with no lineedit) and default [x]
- About window.
- Clump graph closer together
- completions on PropertiesBinWidget values [x]
- Updating completions on PropertiesBinWidget values [ ]
- reinstating sql_form, loc_form and dict_form once we find a way to make them not update in prop_bin_widget. []
- expand into real estate of ports [ ]
- add priority property to all nodes[]

# Big Features TODO:
- Image imports
- frontend modelling
- VI port (ahhh)
- Tabbed graphs, so you can see content in different criteria, and frontend
- Node connections can only happen between valid connectors (PK-FK), node.add_accept_port_type [x]
- Big Graphs compress tables of the same type into one node.
- Object context with reqs/effects
- Narrative Node
- Unit Node
- Constructible node?
## Known bugs
- Can double click when making new node to get two
- not a bug, but writing with shift toggles a mode in graph which is pain
- xml handler needs to handle line by line xml, because of the Matts scotland example where 
- gameeffects xml can work in game but the tags are wrong on the String section. yet it parses everything else! fixed for gameeffects only
- some types missing like UnitAbilities has no link to Types, NarrativeStories Reqsets arent, since they have a weird Met value
- redraw on breaking port connections from arg change looks weird
- side panel is weird, button is too far out, doesnt minimise properly
- sometimes drawing connections still causes dropdown to appear
- was setting None on properties as default, cant do that as get_Property() returns None if widget dont exist