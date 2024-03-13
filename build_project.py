from subprocess import PIPE, STDOUT, Popen
from pathlib import Path
from shutil import rmtree
import PyInstaller.__main__ as make_exe
from multiprocessing import Pool, cpu_count
import os


ROOT_DIR = Path(__file__).parent
BUILD_DIR = Path(ROOT_DIR, "build")
SPEC_DIR = Path(BUILD_DIR, "spec")
INSTALL_DIR = Path(BUILD_DIR, "install")
TMP_DIR = Path(BUILD_DIR, "tmp")
PROJECT_FILES = [
    ('', 'main.spec'),
]


def generate_ui_files():
    print(os.environ['VIRTUAL_ENV'])
    commands = []
    for path_object in ROOT_DIR.glob('**/*.ui'):
        if path_object.is_file() and path_object.parent.name == 'ui':
            file_to_convert = path_object.absolute()
            file_dir = file_to_convert.parent
            file_name = path_object.stem
            output_file = file_dir.parents[0].joinpath(file_name + '.py')
            print(f"Generating .py file for {file_to_convert}")
            command = (f"pyside6-uic {file_to_convert} -o {output_file} "
                       f"--rc-prefix")
            print(command)
            commands.append(command)
    with Pool(processes=cpu_count()) as p_pool:
        p_pool.map(run_external, commands)


def del_tree(dir_path: Path):
    try:
        rmtree(dir_path)
    except FileNotFoundError:
        pass


def cleanup_previous_installation_files():
    del_tree(Path(INSTALL_DIR, "dmcServer"))


def cleanup_build_dir():
    del_tree(TMP_DIR)


def build_app(install_dir: str, spec_file: str):
    make_exe.run([
        '-y',
        '--workpath', str(TMP_DIR),
        '--distpath', str(Path(INSTALL_DIR, install_dir)),
        '--clean',
        str(Path(SPEC_DIR, spec_file))
    ])


def build_modules():
    with Pool(processes=cpu_count()) as p_pool:
        p_pool.starmap(build_app, PROJECT_FILES)


def run_external(command: str):
    proc = Popen(command, shell=True, stdout=PIPE, stderr=STDOUT)
    while proc.poll() is None:
        line = proc.stdout.readline().strip()
        if line:
            try:
                l_d = line.decode("cp866")
            except UnicodeDecodeError:
                try:
                    l_d = line.decode('cp1251')
                except UnicodeDecodeError:
                    try:
                        l_d = line.decode('utf-8')
                    except UnicodeDecodeError:
                        l_d = line
            print(l_d)


def main():
    cleanup_previous_installation_files()
    generate_ui_files()
    build_modules()
    cleanup_build_dir()


if __name__ == "__main__":
    # main()
    generate_ui_files()
