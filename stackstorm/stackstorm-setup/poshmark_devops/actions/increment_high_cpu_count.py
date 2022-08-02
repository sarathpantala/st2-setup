from st2common.runners.base_action import Action

class PrepareBuild(Action):
  def run(self, count):
    count = int(count) + 1
    count = str(count)
    return [count]
