package terratest

import (
	"github.com/stretchr/testify/require"
	"os"
	"testing"
)

func SetUpFakeAWSCredentials(t *testing.T) {
	t.Helper()
	require.NoError(t, os.Setenv("AWS_ACCESS_KEY_ID", "mock_key_idi"))
	require.NoError(t, os.Setenv("AWS_SECRET_ACCESS_KEY", "mock_secret_access_key"))
}
