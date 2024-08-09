import os

TF_REPO_NAME = "terraform-provider-aws"
TF_TEST_BINARY_FOLDER = "test-bin"
TF_REPO_SERVICE_FOLDER = "internal/service"

# absolute path to the terraform repo
TF_REPO_PATH = os.path.realpath(TF_REPO_NAME)
TF_TEST_BINARY_PATH = os.path.realpath(TF_TEST_BINARY_FOLDER)
TF_REPO_SERVICE_PATH = os.path.join(TF_REPO_PATH, TF_REPO_SERVICE_FOLDER)

# list of patch files to apply to the terraform repo
TF_REPO_PATCH_FILES = ["etc/0001-Patch-Hardcode-endpoints-to-local-server.patch"]

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
BLACKLISTED_SERVICES = ["controltower", "greengrass", "iotanalytics"]

# FIXME: check why all the tests are failing, and remove this list once fixed
# list of services that cause a timeout because every test fails against LocalStack
FAILING_SERVICES = ["emr", "sagemaker", "qldb"]
