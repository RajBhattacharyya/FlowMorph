from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os

# Load environment variables
slack_token = os.getenv("SLACK_BOT_TOKEN")
slack_channel = os.getenv("SLACK_CHANNEL")

# Initialize Slack client
slack_client = WebClient(token=slack_token)

def send_slack_notification(pr_url):
    """Sends a Slack notification with the PR link."""
    message = f":rocket: *New PR Created!* :github:\n{pr_url}"
    try:
        slack_client.chat_postMessage(channel=slack_channel, text=message)
        print("✅ Slack notification sent!")
    except SlackApiError as e:
        print(f"❌ Slack API Error: {e.response['error']}")
