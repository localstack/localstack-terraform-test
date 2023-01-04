from subprocess import Popen, PIPE
from constants import BASE_PATH, PATCH_PATH, PATCH_FILES
from os.path import realpath


def patch_repo():
    print(f'Patching {BASE_PATH}...')
    for patch_file in PATCH_FILES:
        cmd = [
            'git',
            'apply',
            f'{realpath(PATCH_PATH)}/{patch_file}',
        ]
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True, cwd=realpath(BASE_PATH))
    stdout, stderr = proc.communicate()
    proc.terminate()
    if stdout:
        print(f'stdout: {stdout}')
    if stderr:
        print('----- error while patching repo -----')
        print(stderr)
        print('Note: This usually happens when the patch has already been applied')
