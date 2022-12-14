from st2common.runners.base_action import Action

# Sample responsebody
# {"url": "job/qa-deploy/", "display_name": "qa-deploy", "name": "qa-deploy",
# "build": {"status": "SUCCESS", "scm": {"culprits": [], "changes": []},
# "log": "", "parameters": {"qw": "true", "app": "true", "batch": "true",
# "skip_asset_sync": "false", "branch": "qa", "vault": "true"},
# "url": "job/qa-deploy/2785/", "timestamp": 1563867679917, "notes": "",
# "number": 2785, "artifacts": {}, "queue_id": 34544, "phase": "FINALIZED",
# "full_url": "https://friday.goshd.com/job/qa-deploy/2785/"}}

KEY_PREFIX = "jenkins"
JOB_CHANNEL_MAP = {"-deploy": "goshd-builds",
                   "gopi-awsAuditTest": "test_gopi",
                   "transfer-host-log": "devlogs",
                   "default": "stackstorm"}


class ParseJenkinsNotification(Action):
    def run(self, responsebody):
        respBuild = responsebody['build']
        result = {}
        result['slack_channel'] = get_slack_channel(responsebody)
        result['message'] = get_message(responsebody)
        result['result_url'] = get_result_url(responsebody)
        result['user_key'] = get_user_key(responsebody)
        result['color'] = get_color(respBuild)
        return result


def get_slack_channel(resp_body):
    job_name = resp_body["name"]
    if "-deploy" in job_name:
        return JOB_CHANNEL_MAP["-deploy"]
    elif "gopi-awsAuditTest" in job_name:
        return JOB_CHANNEL_MAP["gopi-awsAuditTest"]
    elif "transfer-host-log" == job_name:
        return JOB_CHANNEL_MAP[job_name]
    else:
        return JOB_CHANNEL_MAP["default"]


def get_user_key(resp_body):
    '''
    Key format created by poshmark hubot: jenkins-#{buildenv}-deploy-#{branch}
    key format of script: <KEY_PREFIX>-<jenkinsJobName>-<buildBranchName>
    Make sure key name generated by poshmark hubot and this script are same.
    This is used to retrive slack username who invoked the command.
    ex: jenkins-qa-deploy-br357, jenkins-qa-deploy
    '''
    key = KEY_PREFIX + "-" + resp_body['name']
    if ('parameters' in resp_body['build'] and
            'branch' in resp_body['build']['parameters']):
        key += "-" + resp_body['build']['parameters']['branch']
    else:
        key = ''
    return key


def get_color(build):
    color = 'warning'
    if build['phase'] in ['FINALIZED']:
        if build['status'] == 'SUCCESS':
            color = 'good'
        else:
            color = 'danger'
    return color


def get_message(resp_body):
    build = resp_body['build']
    message = "Jenkins " + build['phase'] + " " + resp_body['name']
    if 'number' in build:
        message += " build # " + str(build['number'])
    if 'parameters' in build:
        if 'branch' in build['parameters']:
            message += " for branch: " + build['parameters']['branch']
        if 'hosts_to_update' in build['parameters']:
            message += " for HOST: " + build['parameters']['hosts_to_update']
    if build['phase'] in ['COMPLETED', 'FINALIZED']:
        message += " with status: " + build['status']
        if resp_body['name'] == "transfer-host-log":
            if build['phase'] == "FINALIZED":
                env = "Production" if "poshcrew" in build['full_url'] else "Non-Production"
                message += "\n Environment: " +  env
            if build['status'] == "FAILURE" and build['phase'] == "FINALIZED":
                message += "\n*Host name or log file not found. Please check error log:*"
    return message


def get_result_url(resp_body):
    build = resp_body['build']
    url = ''
    if build['phase'] in ['FINALIZED']:
        url = build['full_url'] + 'console'
    
    return url
