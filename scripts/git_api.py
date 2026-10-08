import os

from dotenv import load_dotenv
from github import Auth, Github

load_dotenv()  # Load environment variables from .env file
auth = Auth.Token(os.environ.get("GITHUB_TOKEN"))
github_client = Github(auth=auth)

github_user = github_client.get_user()  # Get the authenticated user
print(f"Authenticated as: {github_user.login}")

query = "machine-learning language:python"
repositories = github_client.search_repositories(query=query)

# Print the top 10 results
for repo in repositories[:10]:
    print(f"Name: {repo.full_name}")
    print(f"Stars: {repo.stargazers_count}")
    print(f"URL: {repo.html_url}\n")
