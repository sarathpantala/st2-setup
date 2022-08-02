from st2common.runners.base_action import Action
import datetime
import json

class ProcessDatadogAlert(Action):
  def run(self, responsebody):
    if 'event_id' in responsebody:
        event_id = responsebody['event_id']
        monitor_id = responsebody['monitor_id']
        alert_type = str(responsebody['type']).capitalize()
        event_msg = responsebody['msg']
        event_title = responsebody['event_title']
        host = responsebody['host']
        tags = dict(tag.split(':') for tag in str(responsebody['tags']).split(',') if ':' in tag)
        extra = 'false'

        monitor_url = 'https://app.datadoghq.com/monitors#' + str(monitor_id)

        if 'env' in tags:
            env = tags['env']
        elif 'qa' in host:
            env = 'qa'
        elif 'stage' in host:
            env = 'stage'

        if 'region' in tags:
            ec_region = tags['region']
        else:
            ec_region = 'us-east-1'

        if alert_type in ['Warning', 'Error']:
            if alert_type == 'Warning':
                color = 'warning'
            elif alert_type == 'Error':
                color = 'danger'

            if 'MongoDB: Spike in MongoDb connections on' in event_title:
                job = 'fix_mongo_con_spike'

                now = datetime.datetime.utcnow().time()
                if now > datetime.time(01,59) and now < datetime.time(04,00):
                  extra = 'true'
                elif now > datetime.time(18,59) and now < datetime.time(20,00):
                  extra = 'true'
                elif now > datetime.time(22,59) and now < datetime.time(00,00):
                  extra = 'true'
                else:
                  extra = 'false'
            elif 'App server port check failed' in event_title:
                job = 'log_app_port_failure'
            elif 'EC2: Instance status check' in event_title:
                job = 'restart_ec2_instance'

                if tags['type'] in ['app', 'queueworker']:
                    extra = 'false'
                else:
                    extra = 'true'
            elif 'datadog agent status is Critical' in event_title:
                job = 'check_datadog_agent'
            elif 'System: High disk space used' in event_title:
                job = 'report_disk_usage'
            elif 'Datadog Agent check failed' in event_title:
                job = 'datadog_agent_failed'
            elif 'High system.cpu.user utilization on' in event_title:
                job = 'high_system_cpu'
            else:
                job = 'msg_slack'
                event_msg = 'Received ' + str(alert_type) + ' on ' + str(host)
        else:
            color = 'good'
            if event_msg == '':
              event_msg = 'Recovered! ' + event_title

            if alert_type == 'success' and 'MongoDB: Spike in MongoDb connections on' in event_title:
                job = 'cleanup_mongo_conn_spike'
            else:
              job = 'msg_slack'

        return [job, color, str(event_title), str(monitor_url), alert_type, str(event_msg), host, extra, env, ec_region]
