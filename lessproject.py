import sublime, re, os, json

# class to allow saving output directory on a per-project basis
# borrowed heavily from sidebarEnhancements plugin
# https://github.com/titoBouzout/SideBarEnhancements
#
# HUGE THANKS to those guys, as their source code helped solve a
# massive achilles heel in less2css
class LessProject:

  def getDirectories(self):
    return sublime.active_window().folders()

  def getProjectFile(self):
    if not self.getDirectories():
      return None
    
    data = file(os.path.normpath(os.path.join(sublime.packages_path(), '..', 'Settings', 'Session.sublime_session')), 'r').read()
    data = data.replace('\t', ' ')
    data = json.loads(data, strict=False)
    projects = data['workspaces']['recent_workspaces']

    if os.path.lexists(os.path.join(sublime.packages_path(), '..', 'Settings', 'Auto Save Session.sublime_session')):
      data = file(os.path.normpath(os.path.join(sublime.packages_path(), '..', 'Settings', 'Auto Save Session.sublime_session')), 'r').read()
      data = data.replace('\t', ' ')
      data = json.loads(data, strict=False)

      if 'workspaces' in data and 'recent_workspaces' in data['workspaces'] and data['workspaces']['recent_workspaces']:
        projects += data['workspaces']['recent_workspaces']

      projects = list(set(projects))
      
    for project_file in projects:
      project_file = re.sub(r'^/([^/])/', '\\1:/', project_file);
      project_json = json.loads(file(project_file, 'r').read(), strict=False)

      if 'folders' in project_json:
        folders = project_json['folders']
        found_all = True

        for directory in self.getDirectories():
          found = False

          for folder in folders:
            folder_path = re.sub(r'^/([^/])/', '\\1:/', folder['path']);

            if folder_path == directory.replace('\\', '/'):
              found = True
              break;

          if found == False:
            found_all = False
            break;

      if found_all:
        return project_file

    return None

  def getProjectJson(self):
    project = self.getProjectFile()

    if not project:
      print '[less2css] Project file not found'
      return None

    #Try these:

    #file = open(project, 'r')
    #content = json.loads(file, strict=False)
    #file.close()

    #with open(project, 'r') as file:
    #  content = json.load(file)

    content = json.loads(file(project, 'r').read(), strict=False)

    print '[less2css] project JSON:'
    print content

    return content

  def getProjectLessOutputDir(self):
    project_json = self.getProjectJson()

    if not project_json:
      return None

    if 'settings' not in project_json:
      return None

    if 'less2css' not in project_json['settings']:
      return None

    if 'outputDir' not in project_json['settings']['less2css']:
      return None

    return project_json['settings']['less2css']['outputDir']

  def setProjectLessOutputDir(self, output_dir):
    project_json = self.getProjectJson()

    if not project_json:
      return None

    if "settings" in project_json:
      if "less2css" in project_json['settings']:
        project_json['settings']['less2css']['outputDir'] = output_dir
      else:
        project_json['settings']['less2css'] = {}
        project_json['settings']['less2css']['outputDir'] = output_dir
    else:
      project_json['settings'] = {}
      project_json['settings']['less2css'] = {}
      project_json['settings']['less2css']['outputDir'] = output_dir

    project_file = self.getProjectFile()
    
    with open(project_file, 'w') as outfile:
      json.dump(project_json, outfile)

    return True