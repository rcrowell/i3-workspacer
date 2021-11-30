import argparse
import json
import subprocess


class Workspace:
  @classmethod
  def from_js(cls, js):
    return cls(
      name=js['name'],
      is_created=True,
      is_visible=js['visible'],
      is_focused=js['focused'],
    )

  def __init__(self, name, is_created=True, is_visible=False, is_focused=False):
    self.name = name
    self.is_created = is_created
    self.is_visible = is_visible
    self.is_focused = is_focused

  def __repr__(self):
    return '<Workspace {name}{cre}{vis}{foc}>'.format(
        name=json.dumps(self.name),
        cre=(' create' if not self.is_created else ''),
        vis=(' visible' if self.is_visible else ''),
        foc=(' focused' if self.is_focused else ''),
    )
    
  def __eq__(self, other):
    if isinstance(other, Workspace):
      return all([
          self.name == other.name,
          self.is_created == other.is_created,
          self.is_visible == other.is_visible,
          self.is_focused == other.is_focused,
      ])
    return False

  def next_workspace(self, workspaces, max_digit=9):
    my_index = workspaces.index(self)
    next_index = (my_index + 1) % len(workspaces)
    if max_digit is None:
      # May not create new workspaces; just return the next via round-robin.
      return workspaces[next_index]
    if self.name.isdigit():
      next_digit = (int(self.name) + 1) % (max_digit + 1)
    else:
      all_digits = set(int(x.name) for x in workspaces if x.name.isdigit())
      for i in range(max_digit + 1):
        next_digit = (i + 1) % (max_digit + 1)
        if next_digit not in all_digits:
          break
    # May not create workspace if next_digit already exists someplace in workspaces.
    digit_matches = [x for x in workspaces if x.name == str(next_digit)]
    if digit_matches:
      return workspaces[next_index]
    # May not create workspace if self.name != (next_digit - 1) modulo max_digit.
    prev_digit = (next_digit - 1) % (max_digit + 1)
    if (self.name != str(prev_digit)):
      return workspaces[next_index]
    # Create new workspace here!
    return Workspace(name=str(next_digit), is_created=False)

  def make_current(self):
    subprocess.run(['i3-msg', 'workspace {name}'.format(name=self.name)])

  def move_container(self):    
    subprocess.run(['i3-msg', 'move container to workspace {name}'.format(name=self.name)])


def fetch_workspaces():
  result = subprocess.run(['i3-msg', '-t', 'get_workspaces'], capture_output=True)
  result = json.loads(result.stdout)
  return [Workspace.from_js(x) for x in result]


def current_workspace(workspaces):
  return [x for x in workspaces if x.is_visible and x.is_focused][0]


class Dispatcher:
  @staticmethod
  def handle_all(args):
    workspaces = fetch_workspaces()
    print(workspaces)
    
  @staticmethod  
  def handle_current(args):
    workspaces = fetch_workspaces()
    workspace = current_workspace(workspaces=workspaces)
    print(workspace)

  @staticmethod
  def handle_next(args):
    workspaces = fetch_workspaces()
    workspace = current_workspace(workspaces=workspaces)
    next_workspace = workspace.next_workspace(workspaces=workspaces)
    if args.move_container:
      next_workspace.move_container()
    if args.make_current:
      next_workspace.make_current()
    print(next_workspace)


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.set_defaults(fn=Dispatcher.handle_all)
  subparsers = parser.add_subparsers()
  # Args: all
  all_p = subparsers.add_parser('all')
  all_p.set_defaults(fn=Dispatcher.handle_all)
  # Args: current
  current_p = subparsers.add_parser('current')
  current_p.set_defaults(fn=Dispatcher.handle_current)
  # Args: next
  next_p = subparsers.add_parser('next')
  next_p.set_defaults(fn=Dispatcher.handle_next)
  next_p.add_argument('--make-current', default=False, action='store_true')
  next_p.add_argument('--move-container', default=False, action='store_true')
  # Run the requested fn.
  args = parser.parse_args()
  args.fn(args)
