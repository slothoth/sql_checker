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
- ModifierArgs/RequirementArgs Value completions using Name   []
- ModifierArgs/RequirementArgs Name completions using ModifierType, EffectType from DynamicModifier  []
- pk fk connects done prior to making the connection or the downstream node get the value  [ ]
- Search highlights most used set (predefined/ user tracked?)     [ ]
- Sort port topdown so required ones are at the top                 [ ]
- Effect Attach Modifier, ModifierArgument Extra Connection             [ ]
- Searchable dropdown comboBox is prettier                 [ ]
- Types autofills KIND based on connecting module           []
- PK port connections with just the first PK value if combined PK  []
- setEditable on ComboxBox to add new values?
- Big Graphs compress tables of the same type into one node.
- Toggle Types nodes being added for performance/clarity. 
- backlink FK lists have duplicates, but seems covered where it matters, like port connections since it gets Dictionaried
  Big Features:
- Image imports
- Localisation entries (and displaying them as options in relevant gameplay graph)
- frontend modelling
- VI port (ahhh)
- Tabbed graphs, so you can see content in different criteria.
- Node connections can only happen between valid connectors (PK-FK), node.add_accept_port_type