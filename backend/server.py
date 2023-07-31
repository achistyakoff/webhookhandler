import os
import json
import requests
from flask import Flask, request

app = Flask(__name__)

def get_state_from_action(action):
    return action.split(":")[1]

def transform_to_teams_message(data):

    openproject_url = os.environ.get('OP_URL')
    
    action = data.get('action')
    work_package_state = get_state_from_action(action)
    
    # Extracting fields from the incoming JSON
    workitem_id = data['work_package'].get('id')
    task_name = data['work_package'].get('subject')
    task_status = data['work_package']['_embedded']['status'].get('name')
    project_name = data['work_package']['_embedded']['project'].get('name')
    project_identifier = data['work_package']['_embedded']['project'].get('identifier')
    assigned_to = data['work_package']['_embedded']['assignee'].get('name')

    # Create JSON for MS Teams
    teams_message = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": "0076D7",
        "summary": f"Task '{task_name}' was {work_package_state}",
        "sections": [{
            "activityTitle": f"Task '{task_name}' was {work_package_state}",
            "activitySubtitle": "OpenProject",
            "activityImage": "https://adaptivecards.io/content/cats/3.png",
            "facts": [],
            "markdown": True
        }],
        "potentialAction": [{
                "@type": "OpenUri",
                "name": "View task",
                "targets": [
                    {
                        "os": "default",
                        "uri": f"{openproject_url}/projects/{project_identifier}/work_packages/{workitem_id}/activity"
                    }
                ]
            }]
    }

    # Update the "Status," "Task," "Project," and "Assigned to" fields in "facts"
    teams_message['sections'][0]['facts'].append({"name": "Status", "value": task_status})
    teams_message['sections'][0]['facts'].append({"name": "Task", "value": task_name})
    teams_message['sections'][0]['facts'].append({"name": "Project", "value": project_name})
    teams_message['sections'][0]['facts'].append({"name": "Assigned to", "value": assigned_to})
    
    return teams_message

@app.route('/webhook', methods=['POST'])
def webhook_handler():
    data = request.json
    teams_message = transform_to_teams_message(data)
    teams_message_str = json.dumps(teams_message, indent=4)

    # Choose the appropriate Teams webhook URL based on the project specified in the incoming JSON
    project_name = data['work_package']['_embedded']['project'].get('name')
    project_id = data['work_package']['_embedded']['project'].get('id')
    webhook_env_var_name = f'OP_PROJECT_{project_id}_WEBHOOK'
    
    teams_webhook_url = os.environ.get(webhook_env_var_name)
    
    if teams_webhook_url is None:
        print(f"Webhook URL for project '{project_name}' with id '{project_id}' is not set. Please provide it using the '{webhook_env_var_name}' environment variable.")
        return 'Webhook received successfully', 200

    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(teams_webhook_url, data=teams_message_str, headers=headers)
        response.raise_for_status()  # Raises an exception for non-2xx responses
        print("Message successfully sent to MS Teams!")
    except requests.exceptions.RequestException as e:
        print("Failed to send message to MS Teams:", e)

    return 'Webhook received successfully', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
