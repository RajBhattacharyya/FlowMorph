import os
import time
import psutil
import pyrebase
import GPUtil
from github import Github
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from modules.commit_analysis import fetch_commit_details, get_latest_commit, is_bot_commit
from modules.optimize_workflow import optimize_workflow
from modules.pr_analyse import create_pr, merge_pr

load_dotenv()
github_token = os.getenv("GITHUB_TOKEN")

console = Console()

os.makedirs("emissions", exist_ok=True)

ascii_banner = """
██████╗ ███████╗██╗   ██╗ ██████╗  ██████╗ ███████╗
██╔══██╗██╔════╝██║   ██║██╔═══██╗██╔═══██╗██╔════╝
██████╔╝█████╗  ██║   ██║██║   ██║██║   ██║███████╗
██╔═══╝ ██╔══╝  ╚██╗ ██╔╝██║   ██║██║   ██║╚════██║
██║     ███████╗ ╚████╔╝ ╚██████╔╝██████╔╝███████║
╚═╝     ╚══════╝  ╚═══╝   ╚═════╝  ╚═════╝ ╚══════╝
"""
console.print(Panel(ascii_banner, title="[bold cyan]DEVOPS-BUD[/bold cyan]", expand=False))

# Initialize GitHub client
g = Github(github_token)
repo_name = "RajBhattacharyya/pv_app_api"
repo = g.get_repo(repo_name)
workflow_path = ".github/workflows/deploy.yml"

last_checked_commit = None

# Initialize Firebase
firebase_config = {
    "apiKey": os.getenv("FAPIKEY"),
    "authDomain": os.getenv("AUTHDOMAIN"),
    "databaseURL": os.getenv("DATABASEURL"),
    "projectId": os.getenv("PROJECTID"),
    "storageBucket": os.getenv("STORAGEBUCKET"),
    "messagingSenderId": os.getenv("MESSAGINGSENDERID"),
    "appId": os.getenv("APPID"),
    "measurementId": os.getenv("MEASUREMENTID")
}
firebase = pyrebase.initialize_app(firebase_config)
db = firebase.database()

def send_cpu_ram_gpu_stats():
    cpu_usage = psutil.cpu_percent(interval=1)
    ram_usage = psutil.virtual_memory().percent
    gpus = GPUtil.getGPUs()
    gpu_usage = round(gpus[0].load * 100, 2) if gpus else 0

    stats = {
        "cpu_usage": cpu_usage,
        "ram_usage": ram_usage,
        "gpu_usage": gpu_usage,
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
    }
    db.child("system_stats").set(stats)
    console.print(f"[blue]CPU Usage: {cpu_usage}%[/blue] [green]RAM Usage: {ram_usage}%[/green] [magenta]GPU Usage: {gpu_usage}%[/magenta]", end="\r")

def send_optimization_note(note):
    db.child("optimizations").push(note)
    console.print(f"[cyan]Optimization Note: {note}[/cyan]")

console.print("\n[bold green]🔄 Listening for new commits...[/bold green]\n")

while True:
    try:
        latest_commit = get_latest_commit()

        if latest_commit != last_checked_commit:
            commit_details = fetch_commit_details(latest_commit)
            
            if is_bot_commit(commit_details):
                console.print(f"\n[yellow]📌 Detected own commit by {commit_details['author']}. Skipping optimization.[/yellow]")
                last_checked_commit = latest_commit
                time.sleep(60)
                continue
                
            console.print(f"\n[cyan]📌 New commit detected by {commit_details['author']}: {latest_commit}[/cyan]")
            
            console.print("[yellow]⚠️ Optimizing workflow...[/yellow]")
            original_yaml = repo.get_contents(workflow_path).decoded_content.decode()
            optimized_yaml = optimize_workflow(original_yaml, repo_name)
            console.print("[cyan]✅ AI has optimized the workflow.[/cyan]")
            
            pr = create_pr(optimized_yaml)
            console.print(f"[bold green]🎉 Pull Request created: [underline]{pr.html_url}[/underline][/bold green]")
            # merge_pr(pr)

            last_checked_commit = latest_commit

        send_cpu_ram_gpu_stats()
        time.sleep(3)

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        time.sleep(60)