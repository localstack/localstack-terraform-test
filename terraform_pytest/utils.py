import logging
import os
import subprocess
from typing import Dict, List, Optional, Tuple

from terraform_pytest.constants import (
    BLACKLISTED_SERVICES,
    FAILING_SERVICES,
    LS_COMMUNITY_SERVICES,
    LS_PRO_SERVICES,
    TF_REPO_NAME,
    TF_REPO_PATCH_FILES,
    TF_REPO_PATH,
    TF_REPO_SERVICE_PATH,
    TF_TEST_BINARY_PATH,
)

logging.basicConfig(level=logging.INFO)


def execute_command(
    cmd: List[str], env: Optional[Dict[str, str]] = None, cwd: Optional[str] = None
) -> Tuple[int, str]:
    """Execute a command and return the return code.

    :param list(str) cmd:
        command to execute
    :param dict env:
        environment variables
    :param str cwd:
        working directory
    """
    if not all(isinstance(c, str) for c in cmd):
        raise ValueError("cmd must be a list of strings")

    env_vars = os.environ.copy()
    if env:
        env_vars.update(env)

    try:
        process = subprocess.run(
            cmd, env=env_vars, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        return_code = process.returncode
        output = process.stdout + "\n" + process.stderr

        if return_code != 0:
            logging.error(
                f"Command {cmd} failed with return code {return_code} and output: {output}"
            )
            return return_code, output

        return return_code, output
    except Exception as e:
        logging.error(f"Command {cmd} failed with exception {e}")
        return 1, str(e)


def build_test_binary(
    service: str, tf_root_path: str, force_build: bool = False
) -> Tuple[int, str]:
    """
    Build the test binary for a given service.

    :param str service: Service name
    :param str tf_root_path: Path to the terraform repo
    :param bool force_build: Force build the binary

    :return: Tuple[int, str]
        Return code and stdout
    """

    def execute_and_check(command: list[str], working_dir: str, error_msg: str) -> Tuple[int, str]:
        """Execute a command and check its return code. Raise an exception with the provided error message if non-zero."""
        return_code, output = execute_command(command, cwd=working_dir)
        if return_code != 0:
            raise Exception(f"{error_msg}\ntraceback: {output}")
        return return_code, output

    test_binary = os.path.join(TF_TEST_BINARY_PATH, f"{service}.test")
    service_folder = os.path.join(TF_REPO_SERVICE_PATH, service)

    # Return if binary already exists and force_build is False
    if os.path.exists(test_binary) and not force_build:
        logging.info(f"Cache has been detected in the directory: {test_binary}.")
        return 0, ""

    # Clean and set up modules
    for _ in range(2):  # The sequence of commands seems to be repeated twice
        cmd = ["go", "mod", "tidy"]
        error_message = f"Error while executing 'go mod tidy' for {service}"
        execute_and_check(cmd, tf_root_path, error_message)

        cmd = ["go", "mod", "vendor"]
        error_message = f"Error while executing 'go mod vendor' for {service}"
        execute_and_check(cmd, tf_root_path, error_message)

    # Build the test binary
    logging.info(f"Initiating generation of testing binary in the {test_binary} directory.")
    error_message = f"Failed to build the test binary for the {service} service."
    build_cmd = ["go", "test", "-c", service_folder, "-o", test_binary]
    ret_code, output = execute_and_check(build_cmd, tf_root_path, error_message)

    if os.path.exists(test_binary):
        logging.info("Changing the permissions of the binary to 755.")
        os.chmod(test_binary, 0o755)

    return ret_code, output


def get_services(service: str):
    """
    Get the list of services to test.

    :param str service:
        Service names in comma-separated format or a predefined keyword
        example: ec2,lambda,iam or ls-community or ls-pro or ls-all

    :return: list:
        list of services
    """
    available_services = LS_COMMUNITY_SERVICES + LS_PRO_SERVICES
    skipped_services = BLACKLISTED_SERVICES + FAILING_SERVICES

    if service == "ls-community":
        services = [s for s in LS_COMMUNITY_SERVICES if s not in skipped_services]
    elif service == "ls-pro":
        services = [s for s in LS_PRO_SERVICES if s not in skipped_services]
    elif service == "ls-all":
        services = [s for s in LS_COMMUNITY_SERVICES + LS_PRO_SERVICES if s not in skipped_services]
    else:
        services = [s.strip() for s in service.split(",") if s.strip()]

    validated_services = []
    for s in services:
        if s not in available_services:
            logging.warning(f"Service {s} is not supported. Please check the service name")
        elif s in skipped_services:
            logging.warning(f"Service {s} doesn't have any (functioning) tests, skipping...")
        else:
            validated_services.append(s)
    return list(set(validated_services))


def patch_repository():
    """
    Patch a repository using a list of patch files.

    return: None
    """
    logging.info(f"Initiating patching process for repository: {TF_REPO_NAME}...")
    for patch_file in TF_REPO_PATCH_FILES:
        patch_file_path = os.path.realpath(patch_file)
        cmd = ["git", "apply", patch_file_path]
        return_code, stdout = execute_command(cmd=cmd, cwd=TF_REPO_PATH)

        if return_code != 0:
            logging.error("Failure encountered during repository patching.")
        if stdout:
            logging.info(f"Command output: {stdout}")
