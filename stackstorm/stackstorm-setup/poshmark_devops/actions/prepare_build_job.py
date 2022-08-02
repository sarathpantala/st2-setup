from st2common.runners.base_action import Action
import json

class PrepareBuild(Action):
  def run(self, job, buildenv, branch, parameters):
    if job == 'collect-incident-data':
      action = job
      pythonParameters = {'hardened_ami':True}
      pythonParameters['host_name'] = parameters.split(',')[0]
      pythonParameters['script_type'] = parameters.split(',')[1]
    else: 
      pythonParameters = {'app':True, 'qw':True, 'batch':True, 'vault':True}
      # Adding branch to pythonParameters. If this needs to overridden then
      # one of the below if else conditions can do it if they deem necessary.
      if parameters == 'skip_asset_sync':
        pythonParameters['skip_asset_sync'] = True;
      elif parameters == 'None' and 'deploy' in job:
        pythonParameters['skip_asset_sync'] = False;
      elif branch in ['None', 'master'] and 'deploy' in job and buildenv == 'qa':
        pythonParameters['branch'] = 'qa';
      elif branch in ['None', 'master'] and 'deploy' in job and buildenv == 'devteam':
        pythonParameters['branch'] = 'devteam';
      elif not branch in ['None', 'master'] and 'deploy' in job and buildenv == 'stage':
        pythonParameters['branch'] = branch;
      else: #just to ensure skip_asset_sync parameter is not passed when restarting qa or stage
        pythonParameters.pop('skip_asset_sync', None)

      if 'node-' in buildenv:
          buildtype,buildenv = buildenv.split("-")
          job = buildtype + '-' + job
          pythonParameters = {'env_branch':branch}
          #pythonParameters['env_branch'] = branch;

      if buildenv == 'devteam':
        action = 'dt-' + job
      else:
        action = buildenv + '-' + job

    pythonParameters['branch'] = branch
    params = json.dumps(pythonParameters)

    return [action, params]
    