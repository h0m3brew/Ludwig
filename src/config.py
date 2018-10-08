from pathlib import Path

from src import PROJECT_NAME


class Dirs:
    project = Path('/') / 'media' / 'lab' / PROJECT_NAME
    runs = project / 'runs'
    backup_runs = project / 'backup_runs'  # TODO don't backup by default - too much data
    log = project / 'log'
    stdout = project / 'stdout'
    user = Path().cwd() / 'user'
    src = Path().cwd() / 'src'

class Interface:
    common_timepoint = 1