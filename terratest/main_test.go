package terratest

import (
	"fmt"
	"os"
	"testing"
)

func TestMain(m *testing.M) {
	SetUpFakeAWSCredentials()
	os.Exit(m.Run())
}

func SetUpFakeAWSCredentials() {
	if err := os.Setenv("AWS_ACCESS_KEY_ID", "mock_key_id"); err != nil {
		panic(fmt.Errorf("failed to set AWS_ACCESS_KEY_ID env variable"))
	}
	if err := os.Setenv("AWS_SECRET_ACCESS_KEY", "mock_secret_access_key"); err != nil {
		panic(fmt.Errorf("failed to set AWS_SECRET_ACCESS_KEY env variable"))
	}
}
