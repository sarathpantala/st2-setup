# Simple unit test for parse_jenkins_notification.py
import parse_jenkins_notification


def pjn(data):
    test = parse_jenkins_notification.ParseJenkinsNotification()
    return test.run(data)


def test_pjn():
    input = {"url": "job/gopi-awsAuditTest/", "display_name": "gopi-awsAuditTest", "name": "gopi-awsAuditTest", "build": {"status": "SUCCESS", "scm": {"culprits": [], "changes": []}, "log": "", "url": "job/gopi-awsAuditTest/17/", "timestamp": 1562615773297, "notes": "", "number": 17, "artifacts": {}, "queue_id": 12025, "phase": "COMPLETED", "full_url": "https://friday.goshd.com/job/gopi-awsAuditTest/17/"}}
    input2 = {"url": "job/qa-deploy/", "display_name": "qa-deploy", "name": "qa-deploy", "build": {"status": "SUCCESS", "scm": {"culprits": [], "changes": []}, "log": "", "parameters": {"qw": "true", "app": "true", "batch": "true", "skip_asset_sync": "false", "branch": "qa", "vault": "true"}, "url": "job/qa-deploy/2802/", "timestamp": 1563951145044, "notes": "", "number": 2802, "artifacts": {}, "queue_id": 36078, "phase": "COMPLETED", "full_url": "https://friday.goshd.com/job/qa-deploy/2802/"}}

    output = {"color": "warning", "message": "Jenkins COMPLETED gopi-awsAuditTest build # 17 with status: SUCCESS", "result_url": "", "user_key": "", "slack_channel": "test_gopi"}
    output2 = {"color": "warning", "message": "Jenkins COMPLETED qa-deploy build # 2802 for branch: qa with status: SUCCESS", "result_url": "", "user_key": "jenkins-qa-deploy-qa", "slack_channel": "goshd-builds"}
    assert pjn(input) == output
    assert pjn(input2) == output2
