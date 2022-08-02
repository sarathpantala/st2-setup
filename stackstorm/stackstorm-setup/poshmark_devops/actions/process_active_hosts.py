from st2common.runners.base_action import Action
import re


class ProcessActiveHosts(Action):
    def run(self, instances, env_type):
        active_hosts = []
        for instance in instances:
            host_type = "None"
            for tag in instance["Instances"][0]["Tags"]:
                if tag["Key"] == "Name":
                    host = str(tag["Value"])
                    if env_type != "*" and env_type != "Access":
                        break
                if tag["Key"] == "Type" or tag["Key"] == "type":
                    host_type = tag["Value"]
                    if host_type == "Access":
                        public_ip = " | " + instance["Instances"][0]["PublicIpAddress"]
            if env_type == "*":
                host = host + " (Type: " + host_type + ")"
                if host_type == "Access":
                    host = host + public_ip
                elif re.match("jenkins", host_type, re.IGNORECASE) is not None:
                    continue
                elif env_type == "App" and "node" in tag["Value"]:
                    continue
                elif env_type == "Node" and "node" not in tag["Value"]:
                    continue
                elif env_type == "Access":
                    host = host + public_ip
            active_hosts.append(host)
        if not active_hosts:
            active_hosts.append("No active hosts found...")
        return active_hosts


def test_ProcessActiveHosts():
    test = ProcessActiveHosts()

    instances1 = [
        {"Instances": [{"Tags": [{"Key": "Name", "Value": "qa-app1"}, {"Key": "Type", "Value": "App"}]}]}
        ]
    output1 = ['qa-app1 (Type: App)']
    assert test.run(instances1, "*") == output1

    instances2 = [
        {"Instances": [{"Tags": [{"Key": "Name", "Value": "qa-node-app-1"}, {"Key": "Type", "Value": "App"}]}]},
        {"Instances": [{"Tags": [{"Key": "Name", "Value": "qa-app1"}, {"Key": "Type", "Value": "App"}]}]}
        ]
    output2 = ['qa-app1']
    assert test.run(instances2, "App") == output2

    instances3 = [
        {"Instances": [{"Tags": [{"Key": "Name", "Value": "qa-node-app-1"}, {"Key": "Type", "Value": "App"}]}]},
        {"Instances": [{"Tags": [{"Key": "Name", "Value": "qa-app1"}, {"Key": "Type", "Value": "App"}]}]}
        ]
    output3 = ['qa-node-app-1 (Type: App)', 'qa-app1 (Type: App)']
    assert test.run(instances3, "*") == output3
