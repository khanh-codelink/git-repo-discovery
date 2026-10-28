import os

TEST_ENV = {
    "GITHUB_TOKEN": "test-token",
    "SUPABASE_URL": "http://127.0.0.1:54321",
    "SUPABASE_KEY": "test-key-abcd",
    "AZURE_OPENAI_API_KEY": "test-key-efgh",
    "AZURE_OPENAI_ENDPOINT": "https://example.invalid",
    "AZURE_OPENAI_MODEL_NAME": "test-model",
    "AZURE_OPENAI_DEPLOYMENT_NAME": "test-deployment",
}

os.environ.update(TEST_ENV)
