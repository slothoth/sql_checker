from unittest.mock import patch, MagicMock
import sys
from PyQt5.QtWidgets import QApplication, QDialog

import graph.singletons.filepaths as patch_fp
from graph.windows import PathSettingsDialog

app = QApplication.instance() or QApplication(sys.argv)

def test_manual_bad_path():
    patch_fp.LocalFilePaths.initialize_paths()
    patch_fp.LocalFilePaths.save_appdata_path = patch_fp.LocalFilePaths.setup_appdata('CivVII_Test')
    from graph.singletons.db_spec_singleton import db_spec
    db_spec.initialize(False)

    with patch.object(patch_fp.LocalFilePaths, '_find_steam_install', return_value=None), patch.object(patch_fp.LocalFilePaths, '_find_civ_config', return_value=None):
        from main import MainController
        controller = MainController()
        controller.run()

def test_deal_with_bad_paths():
    patch_fp.LocalFilePaths.initialize_paths()
    patch_fp.LocalFilePaths.save_appdata_path = patch_fp.LocalFilePaths.setup_appdata('CivVII_Test')
    from graph.singletons.db_spec_singleton import db_spec
    db_spec.initialize(False)

    with patch.object(patch_fp.LocalFilePaths, '_find_steam_install', return_value=None):
        from main import SetupWorker
        worker = SetupWorker()

        def side_effect_logic(paths):
            dialog = PathSettingsDialog(paths=paths)
            dialog.text_fields['config'].setText('test/test_folder_paths')
            dialog.text_fields['workshop'].setText('1295660')
            dialog.text_fields['install'].setText('test/test_folder_paths')
            is_button_enabled = dialog.ok_button.isEnabled()
            assert is_button_enabled
            dialog.accept()
            dialog.exec_ = MagicMock(return_value=1)

        mock_slot = MagicMock(side_effect=side_effect_logic)
        worker.request_paths.connect(mock_slot)
        worker.run()

    mock_slot.assert_called_once()


def test_graceful_exit():
    patch_fp.LocalFilePaths.initialize_paths()
    patch_fp.LocalFilePaths.save_appdata_path = patch_fp.LocalFilePaths.setup_appdata('CivVII_Test')
    from graph.singletons.db_spec_singleton import db_spec
    db_spec.initialize(False)

    with patch.object(patch_fp.LocalFilePaths, '_find_steam_install', return_value=None):
        from main import SetupWorker
        worker = SetupWorker()

        def side_effect_logic(paths):
            dialog = PathSettingsDialog(paths=paths)
            dialog.button_box.rejected.emit()
            worker.condition.wakeAll()

        mock_slot = MagicMock(side_effect=side_effect_logic)
        worker.request_paths.connect(mock_slot)

        worker.run()

    mock_slot.assert_called_once()
# /Users/samuelmayo/Library/Application Support/Steam/steamapps/workshop/content/1295660