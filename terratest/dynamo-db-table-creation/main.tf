provider "aws" {
  region                      = var.region
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    apigateway     = "http://localhost:4566"
    cloudformation = "http://localhost:4566"
    cloudwatch     = "http://localhost:4566"
    dynamodb       = "http://localhost:4566"
    es             = "http://localhost:4566"
    firehose       = "http://localhost:4566"
    iam            = "http://localhost:4566"
    kinesis        = "http://localhost:4566"
    lambda         = "http://localhost:4566"
    route53        = "http://localhost:4566"
    redshift       = "http://localhost:4566"
    s3             = "http://localhost:4566"
    secretsmanager = "http://localhost:4566"
    ses            = "http://localhost:4566"
    sns            = "http://localhost:4566"
    sqs            = "http://localhost:4566"
    ssm            = "http://localhost:4566"
    stepfunctions  = "http://localhost:4566"
    sts            = "http://localhost:4566"
    ec2            = "http://localhost:4566"
  }
}

terraform {
  required_version = ">= 0.12.26"
}

resource "aws_dynamodb_table" "example" {
  name         = var.table_name
  hash_key     = "userId"
  range_key    = "department"
  billing_mode = "PAY_PER_REQUEST"

  server_side_encryption {
    enabled = true
  }

  attribute {
    name = "userId"
    type = "S"
  }
  attribute {
    name = "department"
    type = "S"
  }

  ttl {
    enabled        = true
    attribute_name = "expires"
  }

  tags = {
    Environment = "production"
  }
}

variable "table_name" {
  description = "The name to set for the dynamoDB table."
  type        = string
  default     = "terratest-example"
}