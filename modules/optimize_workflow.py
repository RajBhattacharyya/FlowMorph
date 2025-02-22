from groq import Groq
from halo import Halo
import pandas as pd
import os
import time
import pyrebase
from modules.track_workflow_emissions import track_workflow_emissions
from rich.console import Console

llmk = os.getenv("API_KEY")
console = Console()

def optimize_workflow(original_yaml):
    """Uses AI to optimize the GitHub Actions workflow, track emissions, and store records in Firebase."""
    try:
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

        with Halo(text="AI analyzing and optimizing workflow...", spinner="dots"):
            client = Groq(api_key=llmk)
            chat_completion = client.chat.completions.create(
                messages=[{
                    "role": "user",
                    "content": f"""
                    Analyze the following GitHub Actions workflow changes. If the changes are 
                    resource-intensive (e.g., running unnecessary steps, redundant builds), 
                    optimize them for efficiency. Return only the modified YAML with comments.

                    Workflow Changes:
                    {original_yaml}
                    """
                }],
                model="llama-3.3-70b-versatile",
            )
            optimized_yaml = chat_completion.choices[0].message.content
            
            # Track emissions
            emissions_data = track_workflow_emissions(original_yaml, optimized_yaml)
            
            # Store workflow versions and emissions data in Firebase
            workflow_record = {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'original_yaml': original_yaml,
                'optimized_yaml': optimized_yaml,
                'emissions_data': emissions_data
            }
            
            # Store in Firebase under a new node called 'workflow_history'
            db.child("workflow_history").push(workflow_record)
            console.print("[cyan]✅ Workflow versions and emissions data stored in Firebase[/cyan]")
            
            # Continue with existing CSV storage
            try:
                emissions_df = pd.read_csv("emissions/historical_emissions.csv")
            except FileNotFoundError:
                emissions_df = pd.DataFrame(columns=['timestamp', 'original', 'optimized', 'saved', 'percentage'])
            
            new_row = {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                **emissions_data
            }
            emissions_df = pd.concat([emissions_df, pd.DataFrame([new_row])], ignore_index=True)
            
            os.makedirs("emissions", exist_ok=True)
            emissions_df.to_csv("emissions/historical_emissions.csv", index=False)
            
            return optimized_yaml
    except Exception as e:
        console.print(f"[red]Error in workflow optimization: {e}[/red]")
        return original_yaml