from st2common.runners.base_action import Action
from pdpyras import APISession
import datetime
from pytz import timezone

class ProcessPagerdutyNotifications(Action):
  def process_incidents(self, on_call, incidents_last_shift):
    triggered = []
    acknowledged = []
    resolved = []
    for incident in incidents_last_shift:
      status = incident['status']
      if status == 'triggered':
        triggered.append('- *[{incident_number}]* {title} \n({url})'.format(incident_number=incident["incident_number"], title=incident["title"], url=incident["html_url"]))
      elif status == 'acknowledged':
        acknowledged.append('- *[{incident_number}]* {title} \n({url})'.format(incident_number=incident["incident_number"], title=incident["title"], url=incident["html_url"]))
      elif status == 'resolved':
        resolved.append('- *[{incident_number}]* {title} \n({url})'.format(incident_number=incident["incident_number"], title=incident["title"], url=incident["html_url"]))

    noti_count = len(triggered)
    slack_message_limit = 30
    if noti_count > slack_message_limit:
      return[on_call, triggered[0:slack_message_limit + 1], [], []]
    if noti_count + len(acknowledged) > slack_message_limit:
      return[on_call, triggered, acknowledged[0:(slack_message_limit-noti_count)], []]
    noti_count = noti_count + len(acknowledged)
    if noti_count + len(resolved) > slack_message_limit:
      return[on_call, triggered, acknowledged, resolved[0:(slack_message_limit-noti_count)]]
    return [on_call, triggered, acknowledged, resolved]

  def run(self, team):
    devops_primary = self.config['pd_devops_primary']
    platform_primary = self.config['pd_platform_primary']
    web_primary = self.config['pd_web_primary']
    api_token = self.config['pagerduty_api_key']
    session = APISession(api_token)
    primary_schedules = {
        "DevOps": devops_primary,
        "Platform": platform_primary,
        "Web": web_primary
    }
    team_id = session.list_all('teams', params={'query':team})[0]['id']
    schedule_id = session.list_all('schedules', params={'query':primary_schedules[team]})[0]['id']
    on_call = session.list_all('oncalls', params={'earliest': True, 'include[]':['users'], 'schedule_ids[]':[schedule_id]})[0]['user']['name']

    iso_8601_last_12_hours = (datetime.datetime.now(timezone('US/Pacific')) - datetime.timedelta(hours=12)).isoformat()
    incidents_last_shift = session.iter_all('incidents', params={'since':iso_8601_last_12_hours, 'team_ids[]':[team_id]})

    return self.process_incidents(on_call, incidents_last_shift)

def test_ProcessPagerdutyNotifications():
  test = ProcessPagerdutyNotifications()

  incidents1 = [{"incident_number": 1, "title":"High error count", "html_url":"test.com", "status":"resolved"}]
  output1 = ['Bhavin', [], [], ['- *[1]* High error count \n(test.com)']]
  assert test.process_incidents("Bhavin", incidents1) == output1

  incidents2 = []
  output2 = ["Edward", [], [], []]
  assert test.process_incidents("Edward", incidents2) == output2