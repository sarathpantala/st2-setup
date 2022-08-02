# Poshmark Devops Integration Pack

This pack creates a basic integration with Stackstorm for use by Poshmark DevOps team

## Actions
* Run Jenkins Jobs on friday.goshd.com
	* Prepares the parameters needed by qa-deploy, stage-deploy, qa-restart and stage-restart jobs so they can be launched from slack
		* hubot-poshmark currently handles all slack interaction for chatops
* Auto Remediate Frequent Alerts
	* MongoDB Connection Spikes
        * 1) Check if it is currently during a Party (between 12-1, 4-5, and 7-9)
        * 2) if it is schedule for 1:05, 5:05, 9:05 respetively else restart app and qw (excluding webapp)
        * 3) notify 1919 and production-alerts channels on slack
	* EC2 Instance Check Failure
        * 1) Get the instance id and volume id to create an aws support ticket
        * 2) Check that the instance failure isn't transient
            * If instnace is not an app or qw instance create pagerduty alert.
        * 3) Stop the instance and wait for it to report that it has stopped
        * 4) Start the instance and wait for it to report that is is running
        * 5) Notify Production-alerts channel that the instance has been stopped and started
        * 6) unmute the host in datadog
        * 7) Create an aws support ticket asking if there was a hardware failure that lead to the instance check failing with sysops@poshmark.com being cc'd on all correspondence.
    * High CPU
        * Logs a count of the High CPU errors and raises a pagerduty alert if the same hosts gets 2 alerts within 15 mins or if 10 total alerts come in within a minute.
    * Datadog Agent is critical
        * 1) Checks if the datadog agent is running
          2) if running sends a slack message to production-alerts requesting someone check the integrations on the host
          3) Restart agent if not running
          4) Ensure that the agent is running else raise pagerduty
    * Disk Low
        * 1) Slack production-critical channel with top 10 items taking up diskspace on the host.
    * App Port Check Failed
        * 1) Log Failure and alert pagerduty if it's a redis instance or if there are 10 or more failures in 60 mins.
