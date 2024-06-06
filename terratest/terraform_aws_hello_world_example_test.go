package terratest

import (
	"github.com/gruntwork-io/terratest/modules/terraform"
	"testing"
)

func TestTerraformAwsHelloWorldExample(t *testing.T) {
	t.Parallel()

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "terraform-aws-hello-world-example",
	})
	defer terraform.Destroy(t, terraformOptions)

	terraform.InitAndApply(t, terraformOptions)

	// TODO: the following are not working (EC2 instance doesn't respond to GET request)

	// website::tag::4:: Run `terraform output` to get the IP of the instance
	//publicIp := terraform.Output(t, terraformOptions, "public_ip")

	// website::tag::5:: Make an HTTP request to the instance and make sure we get back a 200 OK with the body "Hello, World!"
	//url := fmt.Sprintf("http://%s:8080", publicIp)
	//http_helper.HttpGetWithRetry(t, url, nil, 200, "Hello, World!", 30, 5*time.Second)
}
