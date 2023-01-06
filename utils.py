from os import system, getcwd, chdir, chmod, listdir
from os.path import exists, realpath
from tempfile import NamedTemporaryFile

BASE_PATH = 'terraform-provider-aws'
SERVICE_BASE_PATH = './internal/service'

BIN_PATH = 'test-bin'

PATCH_PATH = 'etc'
PATCH_FILES = ['001-hardcode-endpoint.patch']


def execute_command(cmd, env=None, cwd=None):
    """
    Execute a command and return the return code.
    """
    _lwd = getcwd()
    if isinstance(cmd, list):
        cmd = ' '.join(cmd)
    else:
        raise Exception("Please provide command as list(str)")
    if cwd:
        chdir(cwd)
    if env:
        _env = ' '.join([f'{k}="{str(v)}"' for k, v in env.items()])
        cmd = f'{_env} {cmd}'
    log_file = NamedTemporaryFile()
    _err = system(f'{cmd} &> {log_file.name}')
    _log_file = open(log_file.name, 'r')
    _out = _log_file.read()
    _log_file.close()
    chdir(_lwd)
    return _err, _out


def build_test_bin(service, tf_root_path):
    bin_path = f'./{BIN_PATH}/{service}.test'

    if exists(f"{realpath(BASE_PATH)}/{bin_path}"):
        return

    cmd = [
        "go",
        "test",
        "-c",
        f"{SERVICE_BASE_PATH}/{service}",
        "-o",
        bin_path,
    ]

    return_code, stdout = execute_command(cmd, cwd=tf_root_path)

    if exists(realpath(bin_path)):
        chmod(realpath(bin_path), 0o755)

    return return_code, stdout


def get_all_services():
    services = []
    for service in listdir(f'{BASE_PATH}/{SERVICE_BASE_PATH}'):
        services.append(service)
    return sorted(services)


def patch_repo():
    print(f'Patching {BASE_PATH}...')
    for patch_file in PATCH_FILES:
        cmd = [
            'git',
            'apply',
            f'{realpath(PATCH_PATH)}/{patch_file}',
        ]
        return_code, stdout = execute_command(cmd, cwd=realpath(BASE_PATH))
        if return_code != 0:
            print("----- error while patching repo -----")
        if stdout:
            print(f'stdout: {stdout}')
