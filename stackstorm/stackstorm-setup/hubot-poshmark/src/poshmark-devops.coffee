# Description
#   Wrapper for commands to stackstorm through hubot
#
# Configuration:
#   LIST_OF_ENV_VARS_TO_SET
#
# Commands:
#   restart <qa|stage> - restart qa or stage from jenkins
#   deploy <qa|stage> <branch> - deploy a branch to qa or stage (branch defaults to qa for qa and master for stage if left out)
#   active-hosts <env> <type> - shows active hosts for the given environment and type (will list types and all hosts under env if left out)
#   transfer-log <target_host> <log_name.log> - transfers the log on the target host to rc-app1-2b
#   incident-update <devops|platform|web> - returns the last 12 hours of incidents for the specified team
#   oncall - responds with current on call personel for devops, platform, and web
#   check <host> <cpu|redis|elastic> - gets stats on host activities, type of stats defaults to cpu usage if not provided
#   discuss <hyphenated-topic> <user1 user2 ... > - creates channel & invites users if provided, try "discuss help" for more options
#   lunch <today|tomorrow> - displays the lunch offerings for either today or tomorrow
#   poshping - responds with poshpong
#   deploy-android-adhoc - format: deploy-android-adhoc <app-release-version> <flavour>
#   deploy-node-web <env> <branch> <pm_style_branch>: Node web deployment, runs the <devteam|stage|qa|qa-auto|wallaby>-web-docker jobs.
#   deploy-node-mapp <env> <branch>: Node MAPP deployment, runs the <devteam|stage|qa|qa-auto|wallaby>-mapp-docker jobs.
#   deploy-android-custom - format: deploy-android-custom <branch> <flavour>
#
# Notes:
#   <optional notes required for the script>
#
# Author(s):
#   Edward Lam
#   Roy Lin
#   Gopi Valleru
#   Emily O'Mahony

module.exports = (robot) ->
  robot.respond /lunch(.*)$/i, (msg) ->
      getLunch(msg)

  robot.respond /poshping/i, (msg) ->
      msg.send "poshpong"

  robot.respond /discuss (.*)$/i, (msg) ->
      if msg.match[1] is "help"
        msg.send '''Usage: discuss hyphenated-topic [hostname [redis|elastic|mongo]] [user1 user2 ...] [private] [sre-ticket | ir-ticket]
        Collects data on host if provided; type of data defaults to CPU usage & memory if no option specified.
        All users mentioned will be invited to the new slack channel.
        "private" flag makes the new channel private.
        "ticket" flag creates a JIRA ticket in SRE or IR with the same topic.
        '''
        return
      if (! whitelistCheck(msg.message.room))
        msg.send "Channel does not have permission to run command, try #1919"
        return
      params = msg.match[1]
      args = params.split " "
      if args[0].startsWith "@"
        msg.send "Please give hyphenated channel topic first"
        return

      topic = args[0]
      is_private = false
      if "private" in args
        is_private = true

      is_mongo = false
      if "redis" in args
        script_type = "redis"
      else if "elastic" in args
        script_type = "elastic"
      else if "mongo" in args
        is_mongo = true
        script_type = "cpu"
      else
        script_type = "cpu"

      args = args.filter (arg) -> arg not in ["redis","elastic","mongo","cpu","private"]

      invitees = (mention.id for mention in msg.message.mentions when mention.type is "user")
      sender = msg.envelope.user.id
      createChannel(topic, sender, invitees, is_private, is_mongo).then((result) ->
        # result contains [channel ID, channel name]
        if ! is_private
          msg.send "Join \##{result[1]} to discuss"

        if "sre-ticket" in args
          createTicket(topic, msg.message.user, is_private, result[1], "sre-ticket")
          args = args.filter (arg) -> arg isnt "sre-ticket"

        if "ir-ticket" in args
          createTicket(topic, msg.message.user, is_private, result[1], "ir-ticket")
          args = args.filter (arg) -> arg isnt "ir-ticket"

        if args[1] && ! args[1].startsWith "@"
          # get data from host
          host_name = args[1]
          if ! host_name.startsWith "tag_"
            # not an ansible host pattern
            host_name = args[1].replace /http:\/\//g, ""
            host_name = "tag_Name_#{host_name.replace /\.|-/g, '_'}"

          @exec = require('child_process').exec
          cmd = "st2 run poshmark_devops.run_jenkins_job_output job='collect-incident-data' buildenv='staging' params='#{host_name},#{script_type}'"
          @exec cmd, (error, stdout, stderr) ->
            if error
              console.error stderr
              response = "Exited with error, check st2 logs"
            else
              response = parseHostData(stdout, script_type)

            # send data to new channel
            WebClient = require('@slack/web-api').WebClient
            client = new WebClient(process.env.HUBOT_SLACK_TOKEN)
            client.chat.postMessage({
              channel: result[0],
              text: response
            })
      )

  robot.respond /check (.*)$/i, (msg) ->
      if (blacklistCheck(msg.message.room))
        msg.send "Channel does not have permission to run command"
        return
      args = msg.match[1].split " "
      if args.find((arg) -> arg is "redis")
        script_type = "redis"
      else if args.find((arg) -> arg is "elastic")
        script_type = "elastic"
      else
        script_type = "cpu"

      args = args.filter (arg) -> arg not in ["redis","elastic","cpu"]

      host_name = args[0]
      if ! host_name.startsWith "tag_"
        # not an ansible host pattern
        host_name = host_name.replace /http:\/\//g, ""
        host_name = "tag_Name_#{host_name.replace /\.|-/g, '_'}"

      msg.send "Working . . ."

      # get data from host
      @exec = require('child_process').exec
      cmd = "st2 run poshmark_devops.run_jenkins_job_output job='collect-incident-data' buildenv='staging' params='#{host_name},#{script_type}'"

      @exec cmd, (error, stdout, stderr) ->
        if error
          console.error stderr
          console.error stdout
          msg.send "Exited with error, check st2 logs"
          return
        else
          response = parseHostData(stdout, script_type)
          msg.send response


  robot.respond /update-host (.*)$/i, (msg) ->
      if (blacklistCheck(msg.message.room))
        msg.send "Channel does not have permission to run command"
        return
      @exec = require('child_process').exec
      hostname = msg.match[1]
      cmd = "st2 run poshmark_devops.jenkins_update_host hostname='#{hostname}'"
      user = msg.envelope.user.name

      @exec cmd, (error, stdout, stderr) ->
        if error
          msg.message.thread_ts = msg.message.rawMessage.ts
          msg.send error
          msg.send stderr
        else
          msg.message.thread_ts = msg.message.rawMessage.ts
          msg.send "@#{user} Executing your request...Please check #goshd-builds for updates"
          #msg.send "Executing your request...Please check #goshd-builds for updates"

  robot.respond /restart (.*)$/i, (msg) ->
      if (blacklistCheck(msg.message.room))
        msg.send "Channel does not have permission to run command"
        return
      @exec = require('child_process').exec
      buildenv = msg.match[1]
      cmd = "st2 run poshmark_devops.run_jenkins_job job='restart' buildenv='#{buildenv}'"
      user = msg.envelope.user.name

      @exec cmd, (error, stdout, stderr) ->
        if error
          msg.message.thread_ts = msg.message.rawMessage.ts
          msg.send error
          msg.send stderr
        else
          msg.message.thread_ts = msg.message.rawMessage.ts
          msg.send "@#{user} Executing your request...Please check #goshd-builds for updates"
          #msg.send "Executing your request...Please check #goshd-builds for updates"

  robot.respond /oncall/i, (msg) ->
      if (blacklistCheck(msg.message.room))
        msg.send "Channel does not have permission to run command"
        return
      @exec = require('child_process').exec
      user = msg.envelope.user.room
      cmd = "st2 run poshmark_devops.get_pagerduty_oncall user=#{user}"

      @exec cmd, (error, stdout, stderr) ->
        if error
          msg.message.thread_ts = msg.message.rawMessage.ts
          msg.send error
          msg.send stderr

  robot.respond /active-hosts (.*)$/i, (msg) ->
      if (blacklistCheck(msg.message.room))
        msg.send "Channel does not have permission to run command"
        return
      @exec = require('child_process').exec
      params = msg.match[1]
      user = msg.envelope.user.room

      if (/\s/.test(params))
        result = params.split " ", 2
        env = result[0]
        type = result[1]
        if (env.toLowerCase() == 'qa')
          env = 'qa'
        else if (env.toLowerCase() == 'stage')
          env = 'stage'
        # QA has lower case AWS key and values except for key Name
        if (env == 'qa')
          type = type.toLowerCase()
        else if(type.toLowerCase() == "queueworker")
          type = "QueueWorker"
        else if (env!= 'qa')
          type = result[1][0].toUpperCase() + result[1][1..-1].toLowerCase() # Make Type TitleCase
        cmd = "st2 run poshmark_devops.show_active_hosts env=#{env} type=#{type} user=#{user}"
      else
        env = params
        if (env.toLowerCase() == 'qa')
          env = 'qa'
        else if (env.toLowerCase() == 'stage')
          env = 'stage'
        cmd = "st2 run poshmark_devops.show_active_hosts env=#{env} user=#{user}"
      msg.send "Please wait, combing through active hosts!"
      @exec cmd, (error, stdout, stderr) ->
        if error
          msg.message.thread_ts = msg.message.rawMessage.ts
          msg.send error
          msg.send stderr

  robot.respond /transfer-log (.*)$/i, (msg) ->
      if (blacklistCheck(msg.message.room))
        msg.send "Channel does not have permission to run command"
        return
      @exec = require('child_process').exec
      params = msg.match[1]
      user = msg.envelope.user.name

      if (/\s/.test(params))
        result = params.split " ", 2
        host_name = result[0]
        log_name = result[1]
        cmd = "st2 run poshmark_devops.transfer_host_log host_name=#{host_name} log_name=#{log_name}"
        @exec cmd, (error, stdout, stderr) ->
          if error
            msg.message.thread_ts = msg.message.rawMessage.ts
            msg.send error
            msg.send stderr
          else
          msg.message.thread_ts = msg.message.rawMessage.ts
          msg.send "@#{user} Executing your request...Please check #devlogs for updates and `rc-app1-2b`: /goshposh/devlogs for log file."
      else
        msg.message.thread_ts = msg.message.rawMessage.ts
        user = msg.envelope.user.name
        msg.send "@#{user} Please have two arguments, the target host and the full log name"
        return

  robot.respond /incident-update (.*)$/i, (msg) ->
      if (blacklistCheck(msg.message.room))
        msg.send "Channel does not have permission to run command"
        return
      @exec = require('child_process').exec
      team = msg.match[1].toLowerCase()

      if (team == "devops")
        team = "DevOps"
      else if (team == "web")
        team = "Web"
      else if (team == "platform")
        team = "Platform"
      else
        user = msg.envelope.user.name
        msg.send "@#{user} Please choose only one of the following teams: devops, web, platform"
        return
      user = msg.envelope.user.room

      cmd = "st2 run poshmark_devops.pagerduty_notifications team=#{team} user=#{user}"

      msg.send "Calculating...Beep boop!"
      @exec cmd, (error, stdout, stderr) ->
        if error
          msg.message.thread_ts = msg.message.rawMessage.ts
          msg.send error
          msg.send stderr

  robot.respond /deploy (.*)$/i, (msg) ->
      if (blacklistCheck(msg.message.room))
        msg.send "Channel does not have permission to run command"
        return
      @exec = require('child_process').exec
      params = msg.match[1] #.replace /\s+$/g, ""
      user = msg.envelope.user.name
      if (/\s/.test(params))
        result = params.split " ", 2
        if (/-/.test(result[0]))
          build_result = result[0].split "-", 2
          buildtype = build_result[0]
          buildenv = build_result[1]
          buildjob = "#{buildtype}-deploy"
        else
          buildenv = result[0]
          buildjob = "deploy"
        branch = result[1]
        cmd = "st2 run poshmark_devops.run_jenkins_job job='#{buildjob}' buildenv='#{buildenv}' branch='#{branch}' && st2 run st2.kv.set key='jenkins-#{buildenv}-deploy-#{branch}' value='#{user}'"
      else
        if (/-/.test(params))
          result = params.split "-", 2
          buildtype = result[0]
          buildenv = result[1]
          buildjob = "#{buildtype}-deploy"
        else
          buildenv = params
          buildjob = "deploy"
        if buildenv in ['qa']
          cmd = "st2 run poshmark_devops.run_jenkins_job job='#{buildjob}' buildenv='#{buildenv}' branch='qa' && st2 run st2.kv.set key='jenkins-qa-deploy-qa' value='#{user}'"
        else if buildenv in ['devteam']
          cmd = "st2 run poshmark_devops.run_jenkins_job job='#{buildjob}' buildenv='#{buildenv}' branch='devteam' && st2 run st2.kv.set key='jenkins-dt-deploy-devteam' value='#{user}'"
        else
          cmd = "st2 run poshmark_devops.run_jenkins_job job='#{buildjob}' buildenv='#{buildenv}' branch='master' && st2 run st2.kv.set key='jenkins-stage-deploy-master' value='#{user}'"

      @exec cmd, (error, stdout, stderr) ->
        if error
          msg.message.thread_ts = msg.message.rawMessage.ts
          msg.send error
          msg.send stderr
        else
          msg.message.thread_ts = msg.message.rawMessage.ts
          msg.send "@#{user} Executing your request...Please check #goshd-builds for updates"

  robot.respond /deploy-android-adhoc (.*)$/i, (msg) ->
      if (blacklistCheck(msg.message.room))
        msg.send "Channel does not have permission to run command"
        return
      @exec = require('child_process').exec
      params = msg.match[1] #.replace /\s+$/g, ""
      user = msg.envelope.user.name
      buildjob = "android-adhoc-deployment"
      if (/\s/.test(params))
        result = params.split " ", 2
        branchspecifier = result[0]
        flavour = result[1]
        cmd = "st2 run poshmark_devops.run_android_adhoc_deploy_job job='#{buildjob}' branch_specifier='#{branchspecifier}' flavour='#{flavour}'"
      @exec cmd, (error, stdout, stderr) ->
        if error
          msg.message.thread_ts = msg.message.rawMessage.ts
          msg.send error
          msg.send stderr
        else
          msg.message.thread_ts = msg.message.rawMessage.ts
          msg.send "@#{user} Executing your request...Please check #apps-ci for updates"

  robot.respond /deploy-node-web (.*)$/i, (msg) ->
      if (blacklistCheck(msg.message.room))
        msg.send "Channel does not have permission to run command"
        return
      @exec = require('child_process').exec
      params = msg.match[1] #.replace /\s+$/g, ""
      user = msg.envelope.user.name
      if (/\s/.test(params))
        result = params.split " ", 3
        buildenv = result[0]
        branch = result[1]
        pm_style_branch = result[2]
        buildjob = "#{buildenv}-web-docker/#{branch}"
        cmd = "st2 run poshmark_devops.deploy_node_web job='#{buildjob}' pm_style_branch='#{pm_style_branch}'"
      else
        msg.message.thread_ts = msg.message.rawMessage.ts
        msg.send "@#{user} Usage: deploy-node-web <env> <branch>"
        return
      @exec cmd, (error, stdout, stderr) ->
        if error
          msg.message.thread_ts = msg.message.rawMessage.ts
          msg.send error
          msg.send stderr
          msg.send "@#{user} Note: For newly created branch deploy make sure branch exists in job or run Scan Multibranch Pipeline on Jenkins to add it."
        else
          msg.message.thread_ts = msg.message.rawMessage.ts
          msg.send "@#{user} Executing your request...Please check #web-node-release for updates"

  robot.respond /deploy-node-mapp (.*)$/i, (msg) ->
      if (blacklistCheck(msg.message.room))
        msg.send "Channel does not have permission to run command"
        return
      @exec = require('child_process').exec
      params = msg.match[1] #.replace /\s+$/g, ""
      user = msg.envelope.user.name
      if (/\s/.test(params))
        result = params.split " ", 3
        buildenv = result[0]
        branch = result[1]
        pm_style_branch = result[2]
        buildjob = "#{buildenv}-mapp-docker/#{branch}"
        cmd = "st2 run poshmark_devops.deploy_node_web job='#{buildjob}' pm_style_branch='#{pm_style_branch}'"
      else
        msg.message.thread_ts = msg.message.rawMessage.ts
        msg.send "@#{user} Usage: deploy-node-mapp <env> <branch>"
        return
      @exec cmd, (error, stdout, stderr) ->
        if error
          msg.message.thread_ts = msg.message.rawMessage.ts
          msg.send error
          msg.send stderr
          msg.send "@#{user} Note: For newly created branch deploy make sure branch exists in job or run Scan Multibranch Pipeline on Jenkins to add it."
        else
          msg.message.thread_ts = msg.message.rawMessage.ts
          msg.send "@#{user} Executing your request...Please check #web-node-release and #web-non-prod-deployments for updates"

  robot.respond /deploy-android-custom (.*)$/i, (msg) ->
      if (blacklistCheck(msg.message.room))
        msg.send "Channel does not have permission to run command"
        return
      @exec = require('child_process').exec
      params = msg.match[1] #.replace /\s+$/g, ""
      user = msg.envelope.user.name
      buildjob = "android-custom-deploy"
      if (/\s/.test(params))
        result = params.split " ", 2
        branchspecifier = result[0]
        flavour = result[1]
        cmd = "st2 run poshmark_devops.run_android_custom_deploy_job job='#{buildjob}' branch_specifier='#{branchspecifier}' flavour='#{flavour}'"
      @exec cmd, (error, stdout, stderr) ->
        if error
          msg.message.thread_ts = msg.message.rawMessage.ts
          msg.send error
          msg.send stderr
        else
          msg.message.thread_ts = msg.message.rawMessage.ts
          msg.send "@#{user} Executing your request...Please check #apps-ci for updates"

getLunch = (msg) ->
  poshmark_id = "24d12d10aff647bba0f9669f6b2f24e7"
  day = if !msg.match[1] then 'today' else msg.match[1].trim().toLowerCase()
  time =  Math.floor(new Date().getTime() / 1000)
  if (day == "tomorrow")
    time = time + 43200 # Move clock to next day
  endpoint = "https://app.zerocater.com/api/v3/companies/#{poshmark_id}/meals"
  msg.http(endpoint).get() (err, res, body) ->
    meals = JSON.parse(body)
    meal = (m for m in meals when m.time > time - 14400)[0]
    details = "https://zerocater.com/m/#{poshmark_id}/#{meal.id}"
    msg.http("#{meal.url}").get() (err, res, meal) ->
      meal = JSON.parse(meal)
      selections = (choice.name for choice in meal.items).join(', ')
      # Handling when vendor_image_url is null
      if (meal.vendor_image_url == null)
        image = ""
      else
        image = meal.vendor_image_url.replace /upload/, "upload/c_fill,h_250,w_400"
      msg.send "Lunch #{day}: #{meal.name} (from #{meal.vendor_name})\n#{selections}\nDetails: #{details}\n#{image}"

blacklistCheck = (channel) ->
  # Blacklist Channel: (G0P5QPYGZ: casesmashers)
  return (channel == "G0P5QPYGZ")

whitelistCheck = (channel) ->
  # only 1919, prod-critical-alerts, cloudops-chatter, slack-bot-playground for "discuss"
  return (channel in ["C0LAXE4RW","C359PV83S","G4HQW1RN0","C026ZUD1JLB"])

# name is a string with no spaces
# invitees is a list of user IDs
createChannel = (name, sender, invitees, _private, is_mongo) ->
  # initiate Hermes client
  WebClient = require("@slack/web-api").WebClient
  client = new WebClient(process.env.HELPER_SLACK_TOKEN)

  # get date for channel name
  today = new Date
  month = today.getMonth() + 1
  month = if month < 10 then '0' + month else month
  day = today.getDate()
  day = if day < 10 then '0' + day else day

  if (process.env.HUBOT_NAME == "Edith")
    bot_id = "U028GJJJ93Q"
  else if (process.env.HUBOT_NAME == "Jarvis")
    bot_id = "UAD8LEUA1"

  invitees = invitees.filter (id) -> id isnt bot_id
  invitees.push bot_id
  invitees.push sender
  if is_mongo
    topic = "See mongo dashboard: https://app.datadoghq.com/dashboard/y3f-tv9-rdi"
  else
    topic = name.replace /-/g, " "

  channel_name = today.getFullYear() + '-' + month + '-' + day + '-' + name.toLowerCase()
  client.conversations.create({
    name: channel_name,
    is_private: _private
  }).then((value) =>
    client.conversations.invite({
      channel: value.channel.id,
      users: "#{invitees.toString()}"
    })
    client.conversations.setTopic({
      channel: value.channel.id,
      topic: "Incident: #{topic}"
    })
    return [value.channel.id, value.channel.name]
  );

parseHostData = (stdout, script_type) ->
  response = ""
  if script_type == "redis"
    re = /Host: ((.*)\n)((.*)\r\\\n){7}((.*)\\\n)/g
    memory = stdout.match re
    re = /role((.*)\r\\\n){5}/g
    connectivities = stdout.match re
    re = /role(.*)/g
    roles = stdout.match re

    if !(memory && memory[0] && \
        connectivities && connectivities[0] && \
        roles && roles[0])
      return "Can't get data, check job details"

    for role, i in roles
      if /master/.test role
        re = /role((.*)\r\\\n){2}(slave[0-9]+(.*)\r\\\n)*/g
      else # slave
        re = /role(.*\r\\\n){4}/g
      connectivity = connectivities[i].match re
      if !(connectivity && connectivity[0])
        return "Can't get data, check job details"
      response = response.concat "#{memory[i]}#{connectivity[0]}"
      if i < roles.length - 1
        response = response.concat "\n"

  else if script_type == "elastic"
    re = /name(.*)node.role(([^{}]*)\n)*elastic((.*)\n)/g
    data = stdout.match re
    if !(data && data[0])
      return "Can't get data, check job details"
    for item, i in data
      response = response.concat "#{item}"
      if i < data.length - 1
        response = response.concat "\n"

  else # script_type == "cpu"
    re = /Host: ((.*)\n){7}(.*)memory free/g
    usage = stdout.match re
    if !(usage && usage[0])
      return "Can't get data, check job details"
    for item, i in usage
      response = response.concat "#{item}\n"
      if i < usage.length - 1
        response = response.concat "\n"

  return "```#{response.replace /[\\\r]/g, ''}```"

createTicket = (topic, reporter, is_private, channel_name, ticket_board) ->
  description = "#{process.env.HUBOT_NAME} created this ticket for #{reporter.name}."
  if ! is_private
    description = description.concat " Relevant Slack channel is \##{channel_name}."

  # create ticket in SRE project
  if ticket_board == "sre-ticket"
    dst = "devops-support@poshmark.com"
    ticket = topic.replace /-/g, ' '

  # create ticket in IR project
  if ticket_board == "ir-ticket"
    dst = "guardduty@poshmark.com"
    ticket = channel_name

  cmd = "echo '#{description}' | mail #{dst} -s '#{ticket}' -r #{reporter.email_address}"
  @exec = require('child_process').exec
  @exec cmd, (error, stdout, stderr) ->
    if error
      console.error "Unable to create JIRA ticket"
      console.error stderr
    else
      console.error "Created JIRA ticket"
      console.error stdout
