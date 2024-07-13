## Slothoth's DB Checker
The purpose of this script is to use it if you have had a modding conflict, and the Database.log has not been useful.

For initial setup, first load into a game using Play Now in complete vanilla, no mods, no DLC at all. 
Then run the migrate.py script which copies the DebugGameplay.sqlite file into this directory for use.
This is a one-time thing, and you should be able to run the main script without this from now on.

make sure you have tried to run with the set of mods you want, try loading into a game with all the Modes
(Secret Society etc.) that you want on.

You will also need to edit the config.json file in this directory. 
You need to set CIV_INSTALL as the folder with your civilization VI.exe, WORKSHOP_FOLDER where your steam mods are, and last, your User civ directory.
Some sensible defaults are already in place, but at least the user civ directory will need to changed to whatever your username is.

Known Errors: 
- [x] Mods with Criteria like requiring Secret Society's are not caught.
- [x] Database currently does not absorb
