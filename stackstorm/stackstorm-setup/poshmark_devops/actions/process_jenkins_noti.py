from st2common.runners.base_action import Action
import sys
import json
import ast

class ProcessNoti(Action):
  def run(self, responsebody):
  #print "Jenkins " + build['phase'] + " build # " + str(build['number']) + " for " + parameters['branch'] + " with a status: " + build['status']
    respBuild = responsebody['build']
    respParams = respBuild['parameters']

    result = "Jenkins " + respBuild['phase'] + " " + responsebody['name'] + " build # " + str(respBuild['number'])
    result_url = ''
    color = 'warning'

    if 'branch' in respParams:
      result = result + " for branch: " + respParams['branch']

    if 'hosts_to_update' in respParams:
      result = result + " for HOST: " + respParams['hosts_to_update']
      
    if respBuild['phase'] in ['COMPLETED']:
      result = result + " with status: " + respBuild['status']

    if respBuild['phase'] in ['FINALIZED']:
      result = result + " with status: " + respBuild['status']
      result_url = 'URL: https://friday.goshd.com/job/' + responsebody['name'] + '/' + str(respBuild['number']) + '/console'
      if respBuild['status'] == 'SUCCESS':
          color = 'good'
      else:
          color = 'danger'

    if '-deploy' in responsebody['name']:
        key =  "jenkins-" + responsebody['name'] + "-" + respParams['branch']
    else:
        key = " "

    return[result, result_url, key, color]
