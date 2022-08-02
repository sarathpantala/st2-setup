from st2common.runners.base_action import Action

HOSTS_WHITELIST = ["st2", "test"]


class CheckEc2RestartAuthorization(Action):
    def run(self, host):
        result = {"restart": "false"}
        my_list = []
        my_list = [val for val in HOSTS_WHITELIST if val in host]
        if len(my_list) > 0:
            result["restart"] = "true"
        return result
