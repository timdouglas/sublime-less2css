# -*- coding: utf-8 -*-
import sublime, sublime_plugin
import subprocess, platform, re, os

#define methods to convert css, either the current file or all
class Compiler:
  def __init__(self, view):
    self.view = view

  # for command 'LessToCssCommand' and 'AutoLessToCssCommand'
  def convertOne(self, is_auto_save = False):
    fn = self.view.file_name().encode("utf_8")
    if not fn.endswith(".less"):
      return ''

    settings = sublime.active_window().active_view().settings() \
      .get("less2css", sublime.load_settings('less2css.sublime-settings'))
    lessc_command = settings.get("lesscCommand")
    base_dir = settings.get("lessBaseDir")
    output_dir = settings.get("outputDir")
    output_file = settings.get("outputFile")
    minimised = settings.get("minify", True)
    auto_compile = settings.get("autoCompile", True)
    main_file = settings.get("main_file", False)

    if auto_compile == False and is_auto_save == True:
      return ''

    dirs = self.parseBaseDirs(base_dir, output_dir)

    # if you've set the main_file (relative to current file), only that file gets compiled
    # this allows you to have one file with lots of @imports
    if main_file:
      fn = os.path.join(os.path.dirname(fn), main_file)

    return self.convertLess2Css(lessc_command, dirs = dirs, file = fn, minimised = minimised, outputFile = output_file)

  # for command 'AllLessToCssCommand'
  def convertAll(self):
    err_count = 0;

    #default_base
    settings = sublime.active_window().active_view().settings() \
      .get("less2css", sublime.load_settings('less2css.sublime-settings'))
    lessc_command = settings.get("lesscCommand")
    base_dir = settings.get("lessBaseDir")
    output_dir = settings.get("outputDir")
    output_file = settings.get("outputFile")
    minimised = settings.get("minify", True)

    dirs = self.parseBaseDirs(base_dir, output_dir)

    for r,d,f in os.walk(dirs['less']):
      for files in f:
        if files.endswith(".less"):
          #add path to file name
          fn = os.path.join(r, files)
          #call compiler
          resp = self.convertLess2Css(lessc_command, dirs, file = fn, minimised = minimised, outputFile = output_file)

          if resp != "":
            err_count = err_count + 1

    if err_count > 0:
      return "There were errors compiling all LESS files"
    else:
      return ''


  # do convert
  def convertLess2Css(self, lessc_command, dirs, file = '', minimised = True, outputFile = ''):
    out = ''

    # get the current file & its css variant
    if file == "":
      less = self.view.file_name().encode("utf_8")
    else:
      less = file

    if not less.endswith(".less"):
      return ''

    if outputFile != "":
      if not outputFile.endswith(".css"):
        css = outputFile + ".css"
      else:
        css = outputFile
    else:
      css = re.sub('\.less$', '.css', less)

    if (dirs['same_dir']):
      dirs['css'] = os.path.dirname(less)

    sub_path = os.path.basename(css) # css file name
    css = os.path.join(dirs['css'], sub_path)

    # create directories
    output_dir = os.path.dirname(css)
    if not os.path.isdir(output_dir):
      os.makedirs(output_dir)

    if lessc_command == False:
      lessc_command = "lessc"

    if minimised == True:
      cmd = [lessc_command, less, css, "-x", "--verbose"]
    else:
      cmd = [lessc_command, less, css, "--verbose"]

    platform_name = platform.system();

    if platform_name == 'Windows' and minimised == True:
      cmd[3] = '-compress'

    print "[less2css] Converting " + less + " to "+ css

    if lessc_command == "lessc":
      if platform.system() != 'Windows':
        # if is not Windows, modify the PATH
        env = os.getenv('PATH')
        env = env + ':/usr/local/bin:/usr/local/sbin'
        os.environ['PATH'] = env

        if subprocess.call(['which', lessc_command]) == 1:
          return sublime.error_message('less2css error: `lessc` is not avavailable')
      else:
        # change command from lessc to lessc.cmd on Windows,
        # only lessc.cmd works but lessc doesn't
        cmd[0] = 'lessc.cmd'

    #run compiler
    try:
      p = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE) #not sure if node outputs on stderr or stdout so capture both
    except OSError as err:
      return sublime.error_message('less2css error: ' + str(err))
    stdout, stderr = p.communicate()

    #blank lines and control characters
    blank_line_re = re.compile('(^\s+$)|(\033\[[^m]*m)', re.M)

    #decode and replace blank lines
    out = stderr.decode("utf_8")
    out = blank_line_re.sub('', out)

    if out != '':
      print '----[less2cc] Compile Error----'
      print out
    else:
      print '[less2css] Convert completed!'

    return out


  # try to find project folder,
  # and normalize relative paths such as /a/b/c/../d to /a/b/d
  def parseBaseDirs(self, base_dir = './', output_dir = ''):
    base_dir = './' if base_dir is None else base_dir
    output_dir = '' if output_dir is None else output_dir
    fn = self.view.file_name().encode("utf_8")
    file_dir = os.path.dirname(fn)


    # if output_dir is set to auto, try to find appropriate destination

    if output_dir == 'auto':
      current = os.path.split(file_dir)
      parent = os.path.split(current[0])

      #current[0] here will be the parrent folder, while current[1] is the current folder name
      #parent[1] will be the parent folder name, while parent[0] is the parent's parent path

      if current[1] == 'less':
        if parent[1] == 'css':
          # so the current folder is less and the parent folder is css
          output_dir = current[0]
        elif os.path.isdir(os.path.join(current[0],'css')):
          # so the current folder is less and there is a css folder in the parent folder
          output_dir = os.path.join(current[0],'css')
      else:
        #we tried to automate it but failed
        output_dir = ''


    # find project path
    # it seems that there is no shortcuts to get the active project folder,
    # it returns all, so need to find the active one
    proj_dir = ''
    window = sublime.active_window()
    proj_folders = window.folders()

    for folder in proj_folders:
      if fn.startswith(folder):
        proj_dir = folder
        break

    # normalize less base path
    if not base_dir.startswith('/'):
      base_dir = os.path.normpath(os.path.join(proj_dir, base_dir))

    if output_dir == '' or output_dir == './':
      same_dir = True
    else:
      same_dir = False
      
    # normalize css output base path
    if not output_dir.startswith('/'):
      output_dir = os.path.normpath(os.path.join(proj_dir, output_dir))

    return { 'project': proj_dir, 'less': base_dir, 'css' : output_dir, 'same_dir' : same_dir }

