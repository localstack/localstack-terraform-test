import signal
from os import chdir, chmod, getcwd, listdir, system
from os.path import exists, realpath
from uuid import uuid4

TF_REPO_NAME = "terraform-provider-aws"

# absolute path to the terraform repo
TF_REPO_PATH = f"{realpath(TF_REPO_NAME)}"

# list of patch files to apply to the terraform repo
TF_REPO_PATCH_FILES = ["etc/001-hardcode-endpoint.patch"]

# folder name where the testing binaries are stored
TF_TEST_BINARY_FOLDER = "test-bin"
TF_REPO_SERVICE_FOLDER = "./internal/service"

# list of services that are supported by the localstack community edition
LS_COMMUNITY_SERVICES = [
    "acm",
    "apigateway",
    "lambda",
    "cloudformation",
    "cloudwatch",
    "configservice",
    "dynamodb",
    "ec2",
    "elasticsearch",
    "events",
    "firehose",
    "iam",
    "kinesis",
    "kms",
    "logs",
    "opensearch",
    "redshift",
    "resourcegroups",
    "resourcegroupstaggingapi",
    "route53",
    "route53resolver",
    "s3",
    "s3control",
    "secretsmanager",
    "ses",
    "sns",
    "sqs",
    "ssm",
    "sts",
    "swf",
    "transcribe",
]
# list of services that are supported by the localstack pro edition
LS_PRO_SERVICES = [
    "amplify",
    "apigateway",
    "apigatewayv2",
    "appconfig",
    "appautoscaling",
    "appsync",
    "athena",
    "autoscaling",
    "backup",
    "batch",
    "cloudformation",
    "cloudfront",
    "cloudtrail",
    "codecommit",
    "cognitoidp",
    "cognitoidentity",
    "docdb",
    "dynamodb",
    "ec2",
    "ecr",
    "ecs",
    "efs",
    "eks",
    "elasticache",
    "elasticbeanstalk",
    "elb",
    "elbv2",
    "emr",
    "events",
    "fis",
    "glacier",
    "glue",
    "iam",
    "iot",
    "iotanalytics",
    "kafka",
    "kinesisanalytics",
    "kms",
    "lakeformation",
    "lambda",
    "logs",
    "mediastore",
    "mq",
    "mwaa",
    "neptune",
    "organizations",
    "qldb",
    "rds",
    "redshift",
    "route53",
    "s3",
    "sagemaker",
    "secretsmanager",
    "serverlessrepo",
    "ses",
    "sns",
    "sqs",
    "ssm",
    "sts",
]

# list of services that doesn't contain any tests
BLACKLISTED_SERVICES = ["controltower", "greengrass"]


def execute_command(cmd, env=None, cwd=None):
    """Execute a command and return the return code.

    :param list(str) cmd:
        command to execute
    :param dict env:
        environment variables
    :param str cwd:
        working directory
    """
    _lwd = getcwd()
    if isinstance(cmd, list):
        cmd = " ".join(cmd)
    else:
        raise Exception("Please provide command as list(str)")
    if cwd:
        chdir(cwd)
    if env:
        _env = " ".join([f'{k}="{str(v)}"' for k, v in env.items()])
        cmd = f"{_env} {cmd}"
    log_file: str = "/tmp/%s" % uuid4().hex
    _err = system(f"{cmd} > {log_file} 2>&1")
    if _err == signal.SIGINT:
        print("SIGNINT is caught")
        raise KeyboardInterrupt
    _out = open(log_file, "r").read()
    chdir(_lwd)
    return _err, _out


def build_test_bin(service, tf_root_path, force_build=False):
    """Build the test binary for a given service.

    :param str service:
        service name
    :param str tf_root_path:
        path to the terraform repo
    :param bool force_build:
        force build the binary

    :return: int, str or None
        return code and stdout
    """
    _test_bin_abs_path = f"{TF_REPO_PATH}/{TF_TEST_BINARY_FOLDER}/{service}.test"
    _tf_repo_service_folder = f"{TF_REPO_SERVICE_FOLDER}/{service}"

    if exists(_test_bin_abs_path) and not force_build:
        return None

    cmd = ["go", "mod", "tidy"]
    return_code, stdout = execute_command(cmd, cwd=tf_root_path)
    if return_code != 0:
        raise Exception(f"Error while building test binary for {service}\ntraceback: {stdout}")

    cmd = ["go", "mod", "vendor"]
    return_code, stdout = execute_command(cmd, cwd=tf_root_path)
    if return_code != 0:
        raise Exception(f"Error while building test binary for {service}\ntraceback: {stdout}")

    cmd = ["go", "mod", "tidy"]
    return_code, stdout = execute_command(cmd, cwd=tf_root_path)
    if return_code != 0:
        raise Exception(f"Error while building test binary for {service}\ntraceback: {stdout}")

    cmd = ["go", "mod", "vendor"]
    return_code, stdout = execute_command(cmd, cwd=tf_root_path)
    if return_code != 0:
        raise Exception(f"Error while building test binary for {service}\ntraceback: {stdout}")

    cmd = [
        "go",
        "test",
        "-c",
        _tf_repo_service_folder,
        "-o",
        _test_bin_abs_path,
    ]
    return_code, stdout = execute_command(cmd, cwd=tf_root_path)
    if return_code != 0:
        raise Exception(f"Error while building test binary for {service}\ntraceback: {stdout}")

    if exists(_test_bin_abs_path):
        chmod(_test_bin_abs_path, 0o755)

    return return_code, stdout


def get_services(service):
    """Get the list of services to test.

    :param: str service:
        service names in comma separated format
        example: ec2,lambda,iam or ls-community or ls-pro or ls-all

    :return: list:
        list of services
    """
    result = []
    if service == "ls-community":
        services = LS_COMMUNITY_SERVICES
    elif service == "ls-pro":
        services = LS_PRO_SERVICES
    elif service == "ls-all":
        services = LS_COMMUNITY_SERVICES + LS_PRO_SERVICES
    else:
        if "," in service:
            services = service.split(",")
            services = [s for s in services if s]
        else:
            services = [service]
    for s in services:
        if s in LS_COMMUNITY_SERVICES + LS_PRO_SERVICES and s not in BLACKLISTED_SERVICES:
            result.append(s)
        else:
            print(f"Service {s} is not supported...\nPlease check the service name")
    return list(set(result))


def patch_repo():
    """Patches terraform repo.

    return: None
    """
    print(f"Patching {TF_REPO_NAME}...")
    for patch_file in TF_REPO_PATCH_FILES:
        cmd = [
            "git",
            "apply",
            f"{realpath(patch_file)}",
        ]
        return_code, stdout = execute_command(cmd, cwd=realpath(TF_REPO_NAME))
        if return_code != 0:
            print("----- error while patching repo -----")
            print("Patch has already been applied...")
            print("This operation is not idempotent.")
        if stdout:
            print(f"stdout: {stdout}")
