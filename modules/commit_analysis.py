from github import Github, InputGitTreeElement, GithubException
import os
import pyrebase


firebase_config = {
    "apiKey": os.getenv("FAPIKEY"),
    "authDomain": os.getenv("AUTHDOMAIN"),
    "databaseURL": os.getenv("DATABASEURL"),
    "projectId": os.getenv("PROJECTID"),
    "storageBucket": os.getenv("STORAGEBUCKET"),
    "messagingSenderId": os.getenv("MESSAGINGSENDERID"),
    "appId": os.getenv("APPID"),
    "measurementId": os.getenv("MEASUREMENTID"),
}


firebase = pyrebase.initialize_app(firebase_config)
db = firebase.database()


def get_repo_details():
    data = db.child("users").get().val()  
    
    if data and "owner_name" in data and "repo_name" in data:
        return data["owner_name"], data["repo_name"]
    else:
        raise ValueError("Firebase does not have required fields.")


def update_github_connection():
    global repo, BOT_USERNAME
    
    owner_name, repo_name = get_repo_details()
    github_token = os.getenv("GITHUB_TOKEN")
    g = Github(github_token)
    
    repo = g.get_repo(f"{repo_name}")
    BOT_USERNAME = owner_name  
    print(f"Connected to repo: {repo.full_name}")

def firebase_listener(message):
    print("Firebase update detected, updating repo connection...")
    update_github_connection()

repo, BOT_USERNAME = None, None
update_github_connection()  


db.child("users").stream(firebase_listener) 

workflow_path = ".github/workflows/deploy.yml"

def get_latest_commit():
    """Fetches the latest commit SHA from the main branch."""
    return repo.get_commits()[0].sha

def fetch_commit_details(commit_sha):
    """Fetches the commit details including author and diff."""
    commit = repo.get_commit(commit_sha)
    commit_author = commit.author.login if commit.author else "Unknown"
    
    diff_files = {file.filename: file.patch for file in commit.files}
    
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
