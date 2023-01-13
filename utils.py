import signal
from os import system, getcwd, chdir, chmod, listdir
from os.path import exists, realpath
from uuid import uuid4


TF_REPO_NAME = 'terraform-provider-aws'
TF_REPO_PATH = f'{realpath(TF_REPO_NAME)}'

TF_REPO_PATCH_FILES = ['etc/001-hardcode-endpoint.patch']

TF_TEST_BINARY_FOLDER = 'test-bin'
TF_REPO_SERVICE_FOLDER = './internal/service'

BLACKLISTED_SERVICES = ['controltower', 'greengrass']
LS_COMMUNITY_SERVICES = [
    "acm", "apigateway", "lambda", "cloudformation", "cloudwatch", "configservice", "dynamodb", "ec2", "elasticsearch",
    "events", "firehose", "iam", "kinesis", "kms", "logs", "opensearch", "redshift", "resourcegroups",
    "resourcegroupstaggingapi", "route53", "route53resolver", "s3", "s3control", "secretsmanager", "ses", "sns", "sqs",
    "ssm", "sts", "swf", "transcribe"
]
LS_PRO_SERVICES = [
    "amplify", "apigateway", "apigatewayv2", "appconfig", "appautoscaling", "appsync", "athena", "autoscaling",
    "backup", "batch", "cloudformation", "cloudfront", "cloudtrail", "codecommit", "cognitoidp", "cognitoidentity",
    "docdb", "dynamodb", "ec2", "ecr", "ecs", "efs", "eks", "elasticache", "elasticbeanstalk", "elb", "elbv2", "emr",
    "events", "fis", "glacier", "glue", "iam", "iot", "iotanalytics", "kafka", "kinesisanalytics", "kms",
    "lakeformation", "lambda", "logs", "mediastore", "mq", "mwaa", "neptune", "organizations", "qldb", "rds",
    "redshift", "route53", "s3", "sagemaker", "secretsmanager", "serverlessrepo", "ses", "sns", "sqs", "ssm", "sts"
]


def _get_test_bin_abs_path(service):
    return f'{TF_REPO_PATH}/{TF_TEST_BINARY_FOLDER}/{service}.test'


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
    log_file: str = '/tmp/%s' % uuid4().hex
    _err = system(f'{cmd} > {log_file} 2>&1')
    if _err == signal.SIGINT:
        print("SIGNINT is caught")
        raise KeyboardInterrupt
    _out = open(log_file, 'r').read()
    chdir(_lwd)
    return _err, _out


def build_test_bin(service, tf_root_path):
    _test_bin_abs_path = _get_test_bin_abs_path(service)
    _tf_repo_service_folder = f'{TF_REPO_SERVICE_FOLDER}/{service}'

    if exists(_test_bin_abs_path):
        return

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
        raise Exception(f"Error while building test binary for {service}")

    if exists(_test_bin_abs_path):
        chmod(_test_bin_abs_path, 0o755)

    return return_code, stdout


def get_all_services():
    services = []
    for service in listdir(f'{TF_REPO_PATH}/{TF_REPO_SERVICE_FOLDER}'):
        if service not in BLACKLISTED_SERVICES:
            services.append(service)
    return sorted(services)


def get_services(service):
    if service == 'ls-community':
        services = LS_COMMUNITY_SERVICES
    elif service == 'ls-pro':
        services = LS_PRO_SERVICES
    elif service == 'ls-all':
        services = LS_COMMUNITY_SERVICES + LS_PRO_SERVICES
    else:
        if ',' in service:
            services = service.split(',')
            services = [s for s in services if s]
        else:
            services = [service]
    services = [s for s in services if s not in BLACKLISTED_SERVICES]
    return list(set(services))


def patch_repo():
    print(f'Patching {TF_REPO_NAME}...')
    for patch_file in TF_REPO_PATCH_FILES:
        cmd = [
            'git',
            'apply',
            f'{realpath(patch_file)}',
        ]
        return_code, stdout = execute_command(cmd, cwd=realpath(TF_REPO_NAME))
        if return_code != 0:
            print("----- error while patching repo -----")
        if stdout:
            print(f'stdout: {stdout}')
