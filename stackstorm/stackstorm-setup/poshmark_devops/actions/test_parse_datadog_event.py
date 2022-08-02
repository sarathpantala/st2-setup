# Simple unit test for parse_datadog_event.py.
import parse_datadog_event


def pde(data):
    test = parse_datadog_event.ParseDataDogEvent()
    return test.run(data)


def test_pde():
    input = {u'alert_type': u'success',
             u'tags': u'availability-zone:us-east-1c,cluster:nodeapp,env:qa,'
             'host:qa-node-app-2,image:ami-8e8faff1,instance-type:c4.large,'
             'instance:tomcat_server_port_check,kernel:none,'
             'logstash-type:logstash-producer,monitor,name:qa-node-app-2,'
             'region:us-east-1,security-group:sg-0727a373,type:app,'
             'url:http://localhost:9292/api',
             u'event_id': u'5015626807602845944',
             u'alert_id': u'4960770',
             u'event_title': u'[Recovered on {host:qa-node-app-2,'
             'instance:tomcat_server_port_check,url:http://localhost:9292/api}'
             '] App server port check failed for qa-node-app-2',
             u'host': u'qa-node-app-2',
             u'alert_title': u'App server port check failed for qa-node-app-2'
             ' on url:http://localhost:9292/api,'
             'instance:tomcat_server_port_check,host:qa-node-app-2',
             u'alert_status': u''}
    input2 = {u'alert_type': u'error', u'tags': u'availability-zone:us-east-1d,host:perf-node-app,image:ami-0bd804a215f07b8d0,instance-type:c4.xlarge,instance:tomcat_server_port_check,kernel:none,monitor,name:perf-node-app,region:us-east-1,security-group:sg-0727a373,url:http://localhost:9292/api', u'event_id': u'5015628655262939845', u'alert_id': u'4960770', u'event_title': u'[Triggered on {host:perf-node-app,instance:tomcat_server_port_check,url:http://localhost:9292/api}] App server port check failed for perf-node-app', u'host': u'perf-node-app', u'alert_title': u'App server port check failed for perf-node-app on host:perf-node-app,instance:tomcat_server_port_check,url:http://localhost:9292/api', u'alert_status': u''}
    input3 = {u'alert_type': u'error', u'tags': u'availability-zone:us-east-1c,cluster:nodeapp,env:qa,host:qa-node-app-2,image:ami-8e8faff1,instance-type:c4.large,instance:tomcat_server_port_check,kernel:none,logstash-type:logstash-producer,monitor,name:qa-node-app-2,region:us-east-1,security-group:sg-0727a373,type:app,url:http://localhost:9292/api', u'event_id': u'5015627166702377266', u'host': u'qa-node-app-2', u'event_title': u'[Triggered on {host:qa-node-app-2,instance:tomcat_server_port_check,url:http://localhost:9292/api}] App server port check failed for qa-node-app-2', u'alert_id': u'4960770', u'alert_title': u'App server port check failed for qa-node-app-2 on url:http://localhost:9292/api,instance:tomcat_server_port_check,host:qa-node-app-2', u'alert_status': u''}
    input4 = {"alert_type": "error", "tags": "availability-zone:us-east-1c,cluster:stackstorm,env:staging,host:i-0e665d3c4a3dff60b,image:ami-026c8acd92718196b,instance-type:t2.medium,instance:nginx_port_check,kernel:none,monitor,name:test-stackstorm,port:80,region:us-east-1,security-group:sg-069d0a4cfd5a0500b,target_host:localhost,type:stackstorm", "event_id": "5020570595071492150", "host": "test-stackstorm", "event_title": "[Triggered on {host:i-0e665d3c4a3dff60b,instance:nginx_port_check,port:80,target_host:localhost}] Nginx tcp check failed on i-0e665d3c4a3dff60b", "alert_id": "10556448", "alert_title": "Nginx tcp check failed on i-0e665d3c4a3dff60b on host:i-0e665d3c4a3dff60b,target_host:localhost,port:80,instance:nginx_port_check", "alert_status": ""}
    input5 = {"alert_type": "success", "tags": "availability-zone:us-east-1c,cluster:stackstorm,env:staging,host:test-stackstorm,image:ami-026c8acd92718196b,instance-type:t2.medium,instance:nginx_port_check,kernel:none,monitor,name:test-stackstorm,port:80,region:us-east-1,security-group:sg-069d0a4cfd5a0500b,target_host:localhost,type:stackstorm", "event_id": "5021509510693523095", "alert_id": "10556448", "event_title": "[Recovered on {host:test-stackstorm,instance:nginx_port_check,port:80,target_host:localhost}] Nginx tcp check failed on test-stackstorm", "host": "test-stackstorm", "alert_title": "Nginx tcp check failed on test-stackstorm on target_host:localhost,port:80,host:test-stackstorm,instance:nginx_port_check", "alert_status": ""}

    output = {'color': 'good', 'aws_region': 'us-east-1', 'env': 'qa', 'job': 'message_slack', 'service': 'goshposh', 'host': 'qa-node-app-2', 'event_title': '[Recovered on {host:qa-node-app-2,instance:tomcat_server_port_check,url:http://localhost:9292/api}] App server port check failed for qa-node-app-2'}
    output2 = {'color': 'danger', 'aws_region': 'us-east-1', 'env': 'perf', 'job': 'restart_service', 'service': 'goshposh', 'host': 'perf-node-app', 'event_title': '[Triggered on {host:perf-node-app,instance:tomcat_server_port_check,url:http://localhost:9292/api}] App server port check failed for perf-node-app'}
    output4 = {'service': 'nginx', 'color': 'danger', 'aws_region': 'us-east-1', 'host': 'test-stackstorm', 'job': 'restart_service', 'env': 'staging', 'event_title': '[Triggered on {host:i-0e665d3c4a3dff60b,instance:nginx_port_check,port:80,target_host:localhost}] Nginx tcp check failed on i-0e665d3c4a3dff60b'}
    output5 = {'service': 'nginx', 'color': 'good', 'aws_region': 'us-east-1', 'host': 'test-stackstorm', 'job': 'message_slack', 'env': 'staging', 'event_title': '[Recovered on {host:test-stackstorm,instance:nginx_port_check,port:80,target_host:localhost}] Nginx tcp check failed on test-stackstorm'}
    assert pde(input) == output
    assert pde(input2) == output2
    assert pde(input4) == output4
    assert pde(input5) == output5

test_pde()
