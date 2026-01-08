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
- backlink FK lists have duplicates, but seems covered where it matters, like port connections since it gets Dictionaried
- refactor state validation to be threaded on start up, or at least only when graph planner opened
- Make it so arg values are highlighted if they are set to the default one.
- need to improve type system for args using statistical harvesting as some GameEffectsArguments are wrong. like EFFECT_ADJUST_UNIT_RESOURCE_DAMAGE:ResourceClassType is int_2
# Big Features TODO:
- Image imports
- Localisation entries (and displaying them as options in relevant gameplay graph)
- frontend modelling
- VI port (ahhh)
- Tabbed graphs, so you can see content in different criteria.
- Node connections can only happen between valid connectors (PK-FK), node.add_accept_port_type
- Big Graphs compress tables of the same type into one node.
- Auto build Localisation. You put the name/description that you want to show, and the build process converts it and adds values to the localized db based on the PK name. For this we need to do some mining of which columns are used in loc db. Also deal with ModifierString context so no need to think abt it.
## Known bugs
- Some uncommonly used integers are viewed as Bools, like Ages.AgeTechBackgroundTextureOffsetX, mined_bools issue.
- Can double click when making new node to get two
- importing shows hidden widgets in ugly way by default before click
- custom requirements doesnt change params correctly on switch requirementtyp
- Requirements sqwitching is going really weird not showing anything
- Effects and Requirement Types should use fuzzy finder.
- Effects and Requirements should not include text like EFFECT or REQUIREMENT at start for visibility and clarity
- when importing, just skip anything that is an UPDATE or DELETE