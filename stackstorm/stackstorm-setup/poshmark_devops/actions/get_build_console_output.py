from st2common.runners.base_action import Action
import jenkins

import urllib3
from urllib3.exceptions import InsecureRequestWarning

class GetConsoleOutputAction(Action):
    def run(self, job, number):
        info = self.jenkins.get_build_info(job, int(number))
        while info['building']:
            info = self.jenkins.get_build_info(job, int(number))
        return self.jenkins.get_build_console_output(job, int(number))

    def __init__(self, config):
        super(GetConsoleOutputAction, self).__init__(config)
        urllib3.disable_warnings(InsecureRequestWarning)
        self.jenkins = self._get_client()

    def _get_client(self):
        url = self.config['friday_url']
        try:
            username = self.config['friday_user']
        except KeyError:
            username = None
        try:
            password = self.config['friday_password']
        except KeyError:
            password = None

        client = jenkins.Jenkins(url, username, password)
        return client
