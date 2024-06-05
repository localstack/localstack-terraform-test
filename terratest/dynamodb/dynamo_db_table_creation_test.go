package test

import (
	"github.com/gruntwork-io/terratest/modules/terraform"
	"github.com/localstack/localstack-terraform-test/terratest"
	"testing"
)

// From issue: https://github.com/localstack/localstack/issues/4716

func TestDynamoDbTableCreation(t *testing.T) {
	terratest.SetUpFakeAWSCredentials(t)
	awsRegion := "us-east-1"
	terraformOptions := &terraform.Options{
		TerraformDir: "./dynamo-db-table-creation/",
		Vars: map[string]interface{}{
			"region": awsRegion,
		},
	}
	defer terraform.Destroy(t, terraformOptions)
	terraform.InitAndApply(t, terraformOptions)
}
