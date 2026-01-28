import graph.singletons.filepaths as patch_fp
import main


def test_popup_when_failed(qtbot):
    patch_fp.LocalFilePaths.civ_config = None
    patch_fp.LocalFilePaths.civ_install = None
    patch_fp.LocalFilePaths.workshop = None
    worker = main.SetupWorker()
    worker.run()
    # uhh
