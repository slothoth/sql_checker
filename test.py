from model import model_run


class LogQueueDummy:
    def __init__(self):
        self.queue = []
        return

    def put(self, entry):
        self.queue.append(entry)

civ_install = "/Users/samuelmayo/Library/Application Support/Steam/steamapps/common/Sid Meier's Civilization VII/CivilizationVII.app/Contents/Resources"
civ_config_folder = "/Users/samuelmayo/Library/Application Support/Civilization VII/"
workshop_folder = "/Users/samuelmayo/Library/Application Support/Steam/steamapps/workshop/content/1295560/"
loq_q = LogQueueDummy()
model_run(civ_install, civ_config_folder, workshop_folder, loq_q)