import requests
import json
import base64
from datetime import datetime
from requests.auth import HTTPBasicAuth

# Configuration
ATHLETE_ID = ""  # Replace with your athlete ID
API_KEY = ""        # Replace with your API key
PLAN_NAME = "" # replace with your training plan name
BASE_URL = "https://intervals.icu/api/v1/athlete"

# Encode "API_KEY:api_key" in Base64 for the Authorization header
def encode_auth(api_key):
    token = f"API_KEY:{api_key}".encode("utf-8")
    return base64.b64encode(token).decode("utf-8")

HEADERS = {
    "Authorization": f"Basic {encode_auth(API_KEY)}",
    "Content-Type": "application/json"
}

# Load training data from JSON file
def load_trainings(file_path):
    with open(file_path, "r") as file:
        return json.load(file)

# Convert duration values handling time (m, s) and distance (km)
def convert_duration(duration):
    if "km" in duration:
        return float(duration.replace("km", "")) * 1000  # Convert km to meters
    elif "m" in duration and not duration.endswith("km"):
        return int(duration.replace("m", "")) * 60  # Convert minutes to seconds
    elif "s" in duration:
        return int(duration.replace("s", ""))  # Keep seconds as is
    else:
        return int(duration)  # Default for unknown formats

# Expand repeated intervals into separate blocks
def expand_repeats(steps):
    expanded_steps = []

    for step in steps:
        if "description" in step and step["description"][-2] == 'x':
            repeat_count = int(step["description"][-1])
            step["description"] = step["description"][:-2]
            for _ in range(repeat_count):
                expanded_steps.append(step)
        else:
            expanded_steps.append(step)
    return expanded_steps

# Format training data for API submission
def format_training_data(trainings, folder_id):
    formatted_data = []
    count = 0
    for training in trainings["trainings"]:
        description_lines = []

        expanded_steps = expand_repeats(training["steps"])
        for step in expanded_steps:
            description_lines.append(f"-{step['description']}  {step['distance']} {step['zone']}")
            #if "zone" in step:
            #    description_lines.append(f"- {step['distance']} {step['zone']}")
            if "cadence" in step:
                # description_lines.append(f"- {step['distance']} {step['cadence']}")
                description_lines.append(f" {step['cadence']}")
            if "pace" in step:
                description_lines.append(f" {step['pace']}")
            if "power" in step:
                description_lines.append(f" {step['power']}")

        formatted_data.append({
            "name": training["name"],
            "description": "\n".join(description_lines).strip(),
            "folder_id": folder_id,
            "type": training["type"].title(),
            "day":  training["day"],
        })
        count = count+1

    return formatted_data

# create training data to Intervals.icu
def create_plan():
    folder_payload = {
        "name": PLAN_NAME,
        "type": "PLAN",
        "parent_id": None,  # Use `None` for null in Python
        "description": "Folder for " + PLAN_NAME
    }
    url = f"{BASE_URL}/{ATHLETE_ID}/folders/"
    response = requests.post(url,  auth=('API_KEY', API_KEY), json=folder_payload)
    response_json = json.loads(response.text)
    folder_id = response_json['id']
    if response.status_code == 200:
        print(f"Trainings plan folder created successfully. Folder id: {folder_id}")
    else:
        print(f"Failed to create training plan folder. Status code: {response.status_code}")
        print(response.text)
    return folder_id

# Upload training data to Intervals.icu
def upload_trainings(data):
    url = f"{BASE_URL}/{ATHLETE_ID}/workouts/bulk"
    response = requests.post(url, headers=HEADERS, json=data)
    if response.status_code == 200:
        print("Trainings uploaded successfully.")
    else:
        print(f"Failed to upload trainings. Status code: {response.status_code}")
        print(response.text)

# Main function
def main():
    try:
        trainings = load_trainings("trainings.json")
        folder_id = create_plan()
        formatted_data = format_training_data(trainings, folder_id)
        upload_trainings(formatted_data)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
