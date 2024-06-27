from PySide6.QtGui import QIcon

import client_info

MAIN_ICON = 'logo.ico'


def get_path_to_media(media_name: str) -> str:
    root_dir = client_info.WORKDIR / 'media'
    if not root_dir.exists():
        root_dir = client_info.RUNDIR / 'media'
    return str(root_dir / media_name)


def get_icon() -> QIcon:
    return QIcon(get_path_to_media(MAIN_ICON))
