## Slothoth's DB Checker and Planner
The purpose of this program is to debug a given mod setup in Civ VII to get a better log of what is causing the error.

It also includes a graph GUI where you can package and plan your own mod.

# TODO:
- package a given graph into a user friendly configuration with a .modinfo file and a main.sql  [x]
- Dialog traps mouse [X]
- Change integer columns that are 0 or 1 into checkbox      [x]
- Searchable dropdown in comboBox                                   [x]
- Metadata setter window. Also if this determines age, we should change possible values.   [x]
- ALWAYS mode uses subset of possible values present in all 3 ages   [x]
- Include some hotkeys in top section, like File [x]
- Convert existing mod to diagram[x]
- Toggle Types nodes being added for performance/clarity. [x]
- Dialogs converted into toasts where possible [x]
- ModifierArgs/RequirementArgs Value completions using Name   [x]
- ModifierArgs/RequirementArgs Name completions using ModifierType, EffectType from DynamicModifier  [x]
- Search highlights most used set (predefined/ user tracked?)     [ ]
- Sort port topdown so required ones are at the top                 [ ]
- Effect Attach Modifier, ModifierArgument Extra Connection             [ ]
- refactor state validation to be threaded on start up, or at least only when graph planner opened []
- Make it so arg values are highlighted if they are set to the default one. [ ]
- make it so fields that cannot be left default show red when unedited or empty string. []
- colour combination logic for if red and blue because localised [ ]
- Updates and Deletes get imported as a type of node of 2 columns, with the PK values on one side being updated/deleted and the values themselves being changed [ ]
- autocompletes for Value on database [x]
# Big Features TODO:
- Image imports
- Localisation entries (and displaying them as options in relevant gameplay graph) [x]
- frontend modelling
- VI port (ahhh)
- Tabbed graphs, so you can see content in different criteria.
- Node connections can only happen between valid connectors (PK-FK), node.add_accept_port_type [x]
- Big Graphs compress tables of the same type into one node.
## Known bugs
- Can double click when making new node to get two
- not a bug, but writing with shift toggles a mode in graph which is pain