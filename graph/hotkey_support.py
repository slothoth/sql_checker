from PyQt5 import QtCore
import logging
import time
import json
from model import query_mod_db, organise_entries, load_files
from schema_generator import SQLValidator, lint_database
from graph.singletons.filepaths import LocalFilePaths
from graph.singletons.db_spec_singleton import db_spec
from graph.mod_conversion import extract_state_test
from graph.utils import LogPusher
from graph.no_context_widgets import Toast

log = logging.getLogger(__name__)


class ConfigTestWorker(QtCore.QObject):
    """
    Worker class to run the configuration test in a separate thread.
    """
    finished = QtCore.pyqtSignal()
    log_updated = QtCore.pyqtSignal(str)
    results_ready = QtCore.pyqtSignal(object)

    def __init__(self, age, extra_sql):
        super().__init__()
        self.age = age
        self.extra_sql = extra_sql

    def run(self):
        try:
            self.log_updated.emit(f"Running current mod setup when civ last launched in {self.age}...")
            start_time = time.time()

            engine = SQLValidator.make_base_db(f"{LocalFilePaths.app_data_path_form('current.sqlite')}",
                                               SQLValidator.prebuilt)

            database_entries = query_mod_db(age=self.age)
            modded_short, modded, dlc, dlc_files = organise_entries(database_entries)

            with open(LocalFilePaths.app_data_path_form('cached_base_game_sql.json')) as f:
                preloaded_sql = json.load(f)

            not_preloaded_dlc = [i for i in dlc_files if i not in preloaded_sql]
            preloaded_sql_statements_dlc = {k: v for k, v in preloaded_sql.items() if k in dlc_files}

            sql_statements_dlc, _, missed_dlc = load_files(not_preloaded_dlc, 'DLC')
            sql_statements_dlc.update(preloaded_sql_statements_dlc)

            self.log_updated.emit(
                f"Loaded dlc files: {len(sql_statements_dlc)}. Excluded empty files: {len(not_preloaded_dlc)}"
            )

            sql_statements_mods, _, missed_mods = load_files(modded, 'Mod')
            self.log_updated.emit(f"Loaded mod files: {len(sql_statements_mods)}. Missed: {len(missed_mods)}")

            sql_statements_dlc = {k: [{'sql': i} for i in v] for k, v in sql_statements_dlc.items()}
            self.log_updated.emit("Running SQL on Vanilla civ files...")
            dlc_status_info = lint_database(engine, sql_statements_dlc, keep_changes=True, database_spec=db_spec)

            self.results_ready.emit(dlc_status_info)

            sql_statements_mods = {k: [{'sql': i} for i in v] for k, v in sql_statements_mods.items()}
            self.log_updated.emit("Running SQL on Modded files...")
            mod_status_info = lint_database(engine, sql_statements_mods, keep_changes=True, database_spec=db_spec)

            self.results_ready.emit(mod_status_info)
            self.log_updated.emit("Finished running Modded Files")

            if self.extra_sql:
                with open(LocalFilePaths.app_data_path_form('main.sql'), 'r') as f:
                    graph_sql = f.readlines()
                extra_statements = {'graph_main.sql': graph_sql}
                mod_gui_status_info = lint_database(engine, extra_statements, keep_changes=False, database_spec=db_spec)

                self.results_ready.emit(mod_gui_status_info)
                self.log_updated.emit("Finished running Graph mod")

            self.log_updated.emit(f"model_run finished in {time.time() - start_time:.1f}s")

        except Exception as e:
            self.log_updated.emit(f"Error during threaded execution: {e}")
            log.error("Thread error", exc_info=True)
        finally:
            self.finished.emit()


def write_sql(sql_dict_list):                               # save SQL, then trigger main run model
    sql_lines = [i['sql'] + '\n' for i in sql_dict_list]
    with open(LocalFilePaths.app_data_path_form('main.sql'), 'w') as f:
        f.writelines(sql_lines)


def write_loc_sql(loc_lines):
    if loc_lines is not None:
        with open(LocalFilePaths.app_data_path_form('loc.sql'), 'w') as f:
            f.writelines(loc_lines)
