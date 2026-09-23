import json
import base64
import random
import urllib.request
import urllib.error
import os
from datetime import datetime, timedelta

# Configuration
# Path to your secrets file (adjust if necessary)
SECRETS_FILE = r"c:\Users\lchintal\OneDrive - Capgemini\Desktop\usecase3\backend\secrets.json"
# Try setting chunk size to 250 for a single API call, but if the instance throws an error about 
# max requests exceeded (default limit is usually 100), change this to 100 or 50.
BATCH_CHUNK_SIZE = 50  
TOTAL_INCIDENTS = 250

CATEGORIES_ISSUES = {
    "software": [
        "Application crashing on startup",
        "Login failing for ERP system",
        "Cannot access Office 365",
        "License expired for Visio",
        "Antivirus scan failing",
        "Email not syncing on desktop client",
        "SAP timeout errors"
    ],
    "hardware": [
        "Laptop screen flickering",
        "Keyboard not responding",
        "Mouse is broken",
        "Docking station not charging",
        "Printer out of toner",
        "Server beeping sound",
        "Hard drive making clicking noise"
    ],
    "network": [
        "VPN connection dropping constantly",
        "Cannot access shared drive",
        "Wi-Fi is slow in conference room",
        "IP address conflict detected",
        "Firewall blocking legitimate traffic",
        "Router needs restart",
        "Cannot ping local server"
    ],
    "database": [
        "Query performance severely degraded",
        "Database nightly backup failed",
        "Table space is full",
        "Deadlock errors on transaction",
        "Missing index on custom table",
        "Unable to connect to staging DB"
    ],
    "inquiry": [
        "How to request a new monitor?",
        "When is the next company holiday?",
        "Password reset request",
        "Benefits enrollment question",
        "How to access paystubs?",
        "Need access to the new project repository"
    ]
}

def get_random_date_past_7_to_180_days():
    """Generates a random datetime string between 7 days and 6 months ago."""
    end_date = datetime.now() - timedelta(days=7)
    start_date = datetime.now() - timedelta(days=180)
    time_between_dates = end_date - start_date
    random_days = random.randrange(time_between_dates.days)
    random_seconds = random.randrange(86400) # seconds in a day
    random_date = start_date + timedelta(days=random_days, seconds=random_seconds)
    # ServiceNow standard datetime format is 'YYYY-MM-DD HH:MM:SS'
    return random_date.strftime("%Y-%m-%d %H:%M:%S")

def generate_incident_data():
    category = random.choice(list(CATEGORIES_ISSUES.keys()))
    issue = random.choice(CATEGORIES_ISSUES[category])
    incident_date = get_random_date_past_7_to_180_days()
    
    return {
        "short_description": issue,
        "description": f"User reported the following issue: {issue}.\n\nCategory: {category}\nThis issue occurred around {incident_date} and needs attention.",
        "category": category,
        "urgency": str(random.randint(1, 3)),
        "impact": str(random.randint(1, 3)),
        # Setting opened_at and sys_created_on (note: sys_created_on may be ignored by SNOW unless you have admin privileges)
        "opened_at": incident_date,
        "sys_created_on": incident_date
    }

import urllib.request
import urllib.error

# ... existing code for requests replacement ...
def main():
    # 1. Load credentials
    if not os.path.exists(SECRETS_FILE):
        print(f"Error: Secrets file not found at {SECRETS_FILE}")
        return

    with open(SECRETS_FILE, "r") as f:
        secrets = json.load(f)

    instance_url = secrets.get("SERVICENOW_INSTANCE")
    username = secrets.get("SERVICENOW_USERNAME")
    password = secrets.get("SERVICENOW_PASSWORD")

    if not all([instance_url, username, password]):
        print("Error: Missing ServiceNow credentials in secrets.json")
        return

    instance_url = instance_url.rstrip("/")

    print(f"Generating {TOTAL_INCIDENTS} incidents...")
    rest_requests = []
    
    for i in range(TOTAL_INCIDENTS):
        incident_data = generate_incident_data()
        body_str = json.dumps(incident_data)
        body_b64 = base64.b64encode(body_str.encode('utf-8')).decode('utf-8')
        
        rest_requests.append({
            "id": str(i + 1),
            "headers": [
                {"name": "Content-Type", "value": "application/json"}
            ],
            "url": "/api/now/table/incident",
            "method": "POST",
            "body": body_b64
        })

    batch_url = f"{instance_url}/api/now/v1/batch"
    
    # Create basic auth header
    auth_str = f"{username}:{password}"
    auth_b64 = base64.b64encode(auth_str.encode('utf-8')).decode('utf-8')
    
    for i in range(0, len(rest_requests), BATCH_CHUNK_SIZE):
        chunk = rest_requests[i:i + BATCH_CHUNK_SIZE]
        
        batch_payload = {
            "batch_request_id": f"batch_{i//BATCH_CHUNK_SIZE + 1}",
            "rest_requests": chunk
        }
        
        print(f"Sending batch {(i//BATCH_CHUNK_SIZE) + 1} with {len(chunk)} incidents...")
        
        req = urllib.request.Request(batch_url)
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")
        req.add_header("Authorization", f"Basic {auth_b64}")
        
        try:
            with urllib.request.urlopen(req, data=json.dumps(batch_payload).encode('utf-8')) as response:
                if response.status in (200, 201):
                    result = json.loads(response.read().decode('utf-8'))
                    if "result" in result:
                        print("Batch successfully processed!")
                    else:
                        print("Batch processed but check response:", result)
        except urllib.error.HTTPError as e:
            print(f"Failed to process batch. Status Code: {e.code}")
            error_body = e.read().decode('utf-8')
            print("Response:", error_body)
            if e.code == 400 and "Max requests exceeded" in error_body:
                print("\n[!] The ServiceNow instance has a limit on the number of requests per batch.")
                print(f"Please change BATCH_CHUNK_SIZE to 100 or 50 on line 12 and run again.")

if __name__ == "__main__":
    main()

