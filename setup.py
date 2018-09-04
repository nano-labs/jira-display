import json
from jira import JIRA

def save_config(config):
    with open("config.json", "w") as config_file:
        json.dump(config, config_file, indent=4)


current_config = {}
with open("config.json", "r") as config_file:
    config_file = config_file.read() or '{}'
    current_config = json.loads(config_file)

# SETUP ACCOUNT URL
print("Jira account URL [{}]:".format(
    current_config.get("account_url", "https://stelapoint.atlassian.net"))
)
account_url = input()
if not account_url:
    account_url = current_config.get("account_url", "https://stelapoint.atlassian.net")
current_config["account_url"] = account_url
save_config(current_config)

# SETUP USERNAME
print("Username [{}]:".format(current_config.get("username", "")))
username = input()
if not username:
    username = current_config.get("username")
current_config["username"] = username
save_config(current_config)

# SETUP TOKEN
print("Token [{}]:".format(current_config.get("token", "")))
token = input()
if not token:
    token = current_config.get("token")
current_config["token"] = token
save_config(current_config)

JIRA_API = JIRA(account_url, basic_auth=(username, token))

# SETUP PROJECT ID
print("Project ID [{}]:".format(current_config.get("project_id", "")))
for project in JIRA_API.projects():
    print("\t{} - {} ({})".format(project.id, project.name, project.key))
project_id = input()
if not project_id:
    project_id = current_config.get("project_id")
current_config["project_id"] = project_id
save_config(current_config)

# SETUP STATUS IDS
print("Setup status IDs")
for status in JIRA_API.statuses():
    print("\t{} - {}".format(status.id, status.name))
if "status" not in current_config:
    current_config["status"] = {"todo": "", "in_progress": "", "done": ""}
print("TODO ID [{}]:".format(current_config["status"]["todo"]))
todo_id = input()
if not todo_id:
    todo_id = current_config["status"]["todo"]
current_config["status"]["todo"] = todo_id
save_config(current_config)
print("In Progress ID [{}]:".format(current_config["status"]["in_progress"]))
in_progress_id = input()
if not in_progress_id:
    in_progress_id = current_config["status"]["in_progress"]
current_config["status"]["in_progress"] = in_progress_id
save_config(current_config)
print("Done ID [{}]:".format(current_config["status"]["done"]))
done_id = input()
if not done_id:
    done_id = current_config["status"]["done"]
current_config["status"]["done"] = done_id
save_config(current_config)

# SETUP SERIAL PORT
print("Arduino USB port [{}]:".format(current_config.get("serial_port", "")))
serial_port = input()
if not serial_port:
    serial_port = current_config.get("serial_port")
current_config["serial_port"] = serial_port
save_config(current_config)
