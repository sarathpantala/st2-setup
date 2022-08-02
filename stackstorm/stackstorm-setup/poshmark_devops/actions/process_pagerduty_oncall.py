from st2common.runners.base_action import Action
from pdpyras import APISession
from collections import OrderedDict

class ProcessPagerdutyNotifications(Action):
  def run(self):
    devops_primary = self.config['pd_devops_primary']
    platform_primary = self.config['pd_platform_primary']
    web_primary = self.config['pd_web_primary']
    api_token = self.config['pagerduty_api_key']
    session = APISession(api_token)
    on_call = []
    primary_schedules = OrderedDict([("DevOps", devops_primary),
                      ("Platform", platform_primary),
                      ("Web", web_primary)])
    for team in primary_schedules: 
        schedule_id = session.list_all('schedules', params={'query':primary_schedules[team]})[0]['id']
        on_call.append(session.list_all('oncalls', params={'earliest': True, 'include[]':['users'], 'schedule_ids[]':[schedule_id]})[0]['user']['name'])
    return on_call