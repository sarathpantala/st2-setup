from st2common.runners.base_action import Action

# Make sure any key in this dict is not a subset of another other key.
# Ref. to get_job_dict function.
# This dict maps datadog alert title with a stackstorm workflow job name and a linux
# service name if there is one or needed.
ALERT_TITLE_JOB_MAP = {
    "MongoDB: Spike in MongoDb connections on": {"job": "fix_mongo_con_spike",
                                                 "service": "mongod"},
    "datadog agent status is Critical": {"job": "restart_service",
                                         "service": "datadog-agent"},
    "Datadog Agent check failed": {"job": "restart_service",
                                   "service": "datadog-agent"},
    "Nginx tcp check failed": {"job": "restart_service", "service": "nginx"},
    "App server port check failed": {"job": "restart_service",
                                     "service": "goshposh"},
    "EC2: Instance status check": {"job": "restart_ec2_instance",
                                   "black_list": ""},
    "System: High disk space used": {"job": "report_disk_usage"},
    "High system.cpu.user utilization on": {"job": "high_system_cpu"},
    "default": {"job": "message_slack"}
}


class ParseDataDogEvent(Action):
    def run(self, responsebody):
        result = {}
        # take_action: Specifies if stackstorm has to take any action or sent a message to slack or pagerduty.
        # take_action = 'false'
        # Converting tags value to dict
        if "tags" in responsebody:
            responsebody["tags"] = to_dict(responsebody["tags"])
            result["env"] = get_env(responsebody)
        result["aws_region"] = get_region(responsebody["tags"])
        result["color"] = get_color(responsebody)
        
        # Adding job and service keys to result
        result.update(get_job_dict(responsebody["alert_title"], result["color"]))
        result["host"] = responsebody["host"]
        result["event_title"] = responsebody["event_title"]
        print(result)
        return result


def to_dict(tags_):
    # converting string to list by using "," as sperator
    tags_list = tags_.split(",")
    # converting list to dict by using ":" as key value seperator
    tags_dict = {i.split(":")[0]: i.split(":")[1] for i in tags_list
                 if ":" in i}
    return tags_dict


def get_env(resp_body):
    if "env" in resp_body["tags"]:
        return resp_body["tags"]["env"]
    elif "host" in resp_body:
        return resp_body["host"].split("-")[0]
    else:
        return "None"


def get_region(tags_, env_="None"):
    # check if region key is in tags, else get it from env key.
    if "region" in tags_:
        return tags_["region"]
    elif env_:
        if env_ == "Prod" or "production" or "rc":
            return "us-west-2"
        else:
            return "us-east-1"
    else:
        return "us-east-1"


def get_color(resp_body):
    if "alert_type" in resp_body:
        print("alert_type in resp_body")
        if resp_body["alert_type"] == 'warning':
            color = "warning"
        elif resp_body["alert_type"] == 'error':
            color = "danger"
        elif resp_body["alert_type"] == 'success':
            color = "good"
        else:
            color = "warning"
    else:
        color = "warning"
    return color


def get_job_dict(alert_title, color):
    resp = {"job": "", "service": "", "job_key": "None"}
    # If alert_title starts with a key then return the value.
    # If "None" matches then return value of default key.
    for key in ALERT_TITLE_JOB_MAP.keys():
        if alert_title.startswith(key):
            resp["job_key"] = key
            resp["job"] = ALERT_TITLE_JOB_MAP[key]["job"]
            if "service" in ALERT_TITLE_JOB_MAP[key].keys():
                resp["service"] = ALERT_TITLE_JOB_MAP[key]["service"]
            # If color is good then job is set to default.
            # No need for any action.
            if color == "good":
                resp["job"] = ALERT_TITLE_JOB_MAP["default"]["job"]
            return resp
    return resp
