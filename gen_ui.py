from PyQt6.uic import pyuic
from pathlib import Path


ROOT_DIR = Path(__file__).parent


def generate_ui_files():
    for path_object in ROOT_DIR.glob('**/*.ui'):
        if not (path_object.is_file() and path_object.parent.name == 'ui'):
            continue
        file_to_convert = path_object.absolute()
        file_dir = file_to_convert.parent
        file_name = path_object.stem
        output_file = file_dir.parents[0].joinpath(file_name + '.py')
        print(f"Generating .py file for {file_to_convert}")
        pyuic.generate(file_to_convert, output_file, 4, False, 4)


if __name__ == '__main__':
    generate_ui_files()
