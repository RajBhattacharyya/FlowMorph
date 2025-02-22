from github import Github, InputGitTreeElement, GithubException
import os


github_token = os.getenv("GITHUB_TOKEN")
g = Github(github_token)
repo_name = "RajBhattacharyya/pv_app_api"
repo = g.get_repo(repo_name)
BOT_USERNAME = "RajBhattacharyya"
workflow_path = ".github/workflows/deploy.yml"



def get_latest_commit():
    """Fetches the latest commit SHA from the main branch."""
    return repo.get_commits()[0].sha

def fetch_commit_details(commit_sha):
    """Fetches the commit details including author and diff."""
    commit = repo.get_commit(commit_sha)
    commit_author = commit.author.login if commit.author else "Unknown"
    
    diff_files = {}
    for file in commit.files:
        diff_files[file.filename] = file.patch
    
    return {
        "author": commit_author,
        "diff_files": diff_files,
        "message": commit.commit.message
    }

def is_bot_commit(commit_details):
    return (commit_details["author"] == BOT_USERNAME or 
            "Optimized GitHub Actions for Carbon Efficiency" in commit_details["message"])

def analyze_commit_diff(diff_files):
    suspicious_changes = []
    for filename, diff in diff_files.items():
        if workflow_path in filename or "github/workflows" in filename:
            suspicious_changes.append((filename, diff))
    return suspicious_changes