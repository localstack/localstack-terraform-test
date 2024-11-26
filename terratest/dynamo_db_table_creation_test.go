package terratest

import (
	"github.com/gruntwork-io/terratest/modules/terraform"
	"testing"
)

// From issue: https://github.com/localstack/localstack/issues/4716

func TestDynamoDbTableCreation(t *testing.T) {
	t.Parallel()
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
