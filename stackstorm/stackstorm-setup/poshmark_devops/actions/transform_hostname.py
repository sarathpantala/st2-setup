from st2common.runners.base_action import Action
import json
import re

class TransformHostname(Action):
  def run(self, hostname):
    if hostname != 'all':
      hostname = "tag_NAME_" + re.sub(r'-', r'_', hostname)
    pythonParameters = {'hosts_to_update': hostname}
    
    params = json.dumps(pythonParameters)
    return params