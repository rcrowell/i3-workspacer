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

  def make_current(self):
    subprocess.run(['i3-msg', 'workspace {name}'.format(name=self.name)],
                   capture_output=True)

  def move_container(self):    
    subprocess.run(['i3-msg', 'move container to workspace {name}'.format(name=self.name)],
                   capture_output=True)


def fetch_workspaces(managed_names=()):
  result = subprocess.run(['i3-msg', '-t', 'get_workspaces'], capture_output=True)
  result = json.loads(result.stdout)
  workspaces = [Workspace.from_js(x) for x in result]
  # Ensure all managed_names appear in workspaces, even if they have not been created yet.
  managed_names = [str(x) for x in managed_names]
  for i, managed_name in enumerate(managed_names):
    created = [x.name for x in workspaces]
    if managed_name not in created:
      if i == 0:
        # Insert right before the smallest managed_name that exists, or at the end.
        index, _ = min(
            [(i, x) for i, x in enumerate(created) if x in managed_names],
            key=lambda x: managed_names.index(x[1]),
            default=(len(workspaces), None),
        )
      else:
        # Insert right after the previous managed_name.
        prev_name = managed_names[i-1]
        index = 1 + ([i for i, x in enumerate(workspaces) if x.name == prev_name][0])
      workspaces.insert(index, Workspace(name=managed_name, is_created=False))
  return workspaces


def current_workspace(workspaces):
  return [x for x in workspaces if x.is_visible and x.is_focused][0]


def prev_workspace(workspaces, workspace=None):
  workspace = workspace or current_workspace(workspaces=workspaces)
  prev_index = (workspaces.index(workspace) - 1) % len(workspaces)
  return workspaces[prev_index]


def next_workspace(workspaces, workspace=None):
  workspace = workspace or current_workspace(workspaces=workspaces)
  next_index = (workspaces.index(workspace) + 1) % len(workspaces)
  return workspaces[next_index]


class Dispatcher:
  @staticmethod
  def _to_digits(min_digit=None, max_digit=None):
    if (min_digit is None) ^ (max_digit is None):
      raise ValueError('min_digit and max_digit must both be set or unset')
    return range(min_digit, max_digit+1) if min_digit is not None else ()
        
  @staticmethod
  def handle_all(args):
    digits = Dispatcher._to_digits(min_digit=args.min_digit, max_digit=args.max_digit)
    workspaces = fetch_workspaces(managed_names=digits)
    print(workspaces)
    
  @staticmethod  
  def handle_current(args):
    workspaces = fetch_workspaces()
    workspace = current_workspace(workspaces=workspaces)
    print(workspace)

  @staticmethod
  def handle_prev(args):
    digits = Dispatcher._to_digits(min_digit=args.min_digit, max_digit=args.max_digit)
    workspaces = fetch_workspaces(managed_names=digits)
    prev_workspace_ = prev_workspace(workspaces=workspaces)
    if args.move_container:
      prev_workspace_.move_container()
    if args.make_current:
      prev_workspace_.make_current()
    print(prev_workspace_)

  @staticmethod
  def handle_next(args):
    digits = Dispatcher._to_digits(min_digit=args.min_digit, max_digit=args.max_digit)
    workspaces = fetch_workspaces(managed_names=digits)
    next_workspace_ = next_workspace(workspaces=workspaces)
    if args.move_container:
      next_workspace_.move_container()
    if args.make_current:
      next_workspace_.make_current()
    print(next_workspace_)
    

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.set_defaults(fn=Dispatcher.handle_current)
  subparsers = parser.add_subparsers()
  # Args: current
  current_p = subparsers.add_parser('current')
  current_p.set_defaults(fn=Dispatcher.handle_current)
  # Args: all
  all_p = subparsers.add_parser('all')
  all_p.set_defaults(fn=Dispatcher.handle_all)
  all_p.add_argument('--min-digit', type=int, default=None)
  all_p.add_argument('--max-digit', type=int, default=None)
  # Args: prev
  prev_p = subparsers.add_parser('prev')
  prev_p.set_defaults(fn=Dispatcher.handle_prev)
  prev_p.add_argument('--min-digit', type=int, default=None)
  prev_p.add_argument('--max-digit', type=int, default=None)
  prev_p.add_argument('--make-current', default=False, action='store_true')
  prev_p.add_argument('--move-container', default=False, action='store_true')
  # Args: next
  next_p = subparsers.add_parser('next')
  next_p.set_defaults(fn=Dispatcher.handle_next)
  next_p.add_argument('--min-digit', type=int, default=None)
  next_p.add_argument('--max-digit', type=int, default=None)
  next_p.add_argument('--make-current', default=False, action='store_true')
  next_p.add_argument('--move-container', default=False, action='store_true')
  # Run the requested fn.
  args = parser.parse_args()
  args.fn(args)
