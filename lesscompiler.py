# -*- coding: utf-8 -*-
from __future__ import print_function
import sublime
#import sublime_plugin
import subprocess
import platform
import re
import os
import sys

# these constants are for the settings of less2css
SETTING_AUTOCOMPILE = "autoCompile"
SETTING_LESSBASEDIR = "lessBaseDir"
SETTING_IGNOREPREFIXEDFILES = "ignorePrefixedFiles"
SETTING_LESSCCOMMAND = "lesscCommand"
SETTING_MAINFILE = "main_file"
SETTING_MINIFY = "minify"
SETTING_MINNAME = "minName"
SETTING_OUTPUTDIR = "outputDir"
SETTING_OUTPUTFILE = "outputFile"


#define methods to convert css, either the current file or all
class Compiler:
  def __init__(self, view):
    self.view = view

  def getSettings(self):
    # get the user settings for the plugin
    settings = sublime.load_settings('less2css.sublime-settings')
    # get the less2css settings from the project file
    project_settings = sublime.active_window().active_view().settings().get("less2css")
    if project_settings is None:
      project_settings = {}

    # we will combine the settings from the project with the user settings. The project settings take precedence over
    # the user settings. If there is no project specific value for a setting, the user setting will be used. If the user
    # setting doesn't exist it will use the specified default value for the setting
    return {
        'auto_compile': project_settings.get(SETTING_AUTOCOMPILE, settings.get(SETTING_AUTOCOMPILE, True)),
        'base_dir': project_settings.get(SETTING_LESSBASEDIR, settings.get(SETTING_LESSBASEDIR)),
        'ignore_underscored': project_settings.get(SETTING_IGNOREPREFIXEDFILES, settings.get(SETTING_IGNOREPREFIXEDFILES, False)),
        'lessc_command': project_settings.get(SETTING_LESSCCOMMAND, settings.get(SETTING_LESSCCOMMAND)),
        'main_file': project_settings.get(SETTING_MAINFILE, settings.get(SETTING_MAINFILE, False)),
        'minimised': project_settings.get(SETTING_MINIFY, settings.get(SETTING_MINIFY, True)),
        'min_name': project_settings.get(SETTING_MINNAME, settings.get(SETTING_MINNAME, True)),
        'output_dir': project_settings.get(SETTING_OUTPUTDIR, settings.get(SETTING_OUTPUTDIR)),
        'output_file': project_settings.get(SETTING_OUTPUTFILE, settings.get(SETTING_OUTPUTFILE))
    }

  # for command 'LessToCssCommand' and 'AutoLessToCssCommand'
  def convertOne(self, is_auto_save=False):
    # check if the filename ends on .less, if not, stop processing the file
    fn = self.view.file_name()
    # in Python 3 all string are Unicode by default, we only have to encode when running on something lower than 3
    # in addition Windows uses UTF-16 for its file names so we don't encode to UTF-8 on Windows
    # but in Windows set system locale to Chinese(RPC) defalut filesystem encoding is "mbcs"
    if sys.version_info < (3, 0, 0):
      if platform.system() is "Windows":
        fn = fn.encode(sys.getfilesystemencoding())
      else:
        fn = fn.encode("utf_8")

    # it the file isn't a less file we have no don't have to process it any further
    if not fn.endswith(".less"):
      return ''

    # get the user settings for the plugin
    settings = self.getSettings()

    # if this method is called on auto save but auto compile is not enabled, stop processing the file
    if (is_auto_save and not settings['auto_compile']):
      return ''

    # check if files starting with an underscore should be ignored and if the file name starts with an underscore
    if (settings['ignore_underscored'] and os.path.basename(fn).startswith('_') and is_auto_save and not settings['main_file']):
      # print a friendly message for the user
      print("[less2css] '" + fn + "' ignored, file name starts with an underscore and ignorePrefixedFiles is True")
      return ''

    dirs = self.parseBaseDirs(settings['base_dir'], settings['output_dir'])

    # if you've set the main_file (relative to current file), only that file gets compiled
    # this allows you to have one file with lots of @imports
    if settings['main_file']:
      fn = os.path.join(os.path.dirname(fn), settings['main_file'])

    # compile the LESS file
    return self.convertLess2Css(settings['lessc_command'], dirs=dirs, file=fn, minimised=settings['minimised'], outputFile=settings['output_file'])

  # for command 'AllLessToCssCommand'
  def convertAll(self):
    err_count = 0

    # get the plugin settings
    settings = self.getSettings()

    dirs = self.parseBaseDirs(settings['base_dir'], settings['output_dir'])

    for r, d, f in os.walk(dirs['less']):
      # loop through all the files in the folder
      for files in f:
        # only process files ending on .less
        if files.endswith(".less"):
          # check if files starting with an underscore should be ignored and if the file name starts with an underscore
          if (settings['ignore_underscored'] and files.startswith('_')):
            # print a friendly message for the user
            print("[less2css] '" + os.path.join(r, files) + "' ignored, file name starts with an underscore and ignorePrefixedFiles is True")
          else:
            # add path to file name
            fn = os.path.join(r, files)
            # call compiler
            resp = self.convertLess2Css(settings['lessc_command'], dirs, file=fn, minimised=settings['minimised'], outputFile=settings['output_file'])
            # check the result of the compiler, if it isn't empty an error has occured
            if resp != "":
              # keep count of the number of files that failed to compile
              err_count += 1

    # if err_count is more than 0 it means at least 1 error occured while compiling all LESS files
    if err_count > 0:
      return "There were errors compiling all LESS files"
    else:
      return ''

  # do convert
  def convertLess2Css(self, lessc_command, dirs, file='', minimised=True, outputFile=''):
    out = ''

    # get the plugin settings
    settings = self.getSettings()

    # get the current file & its css variant
    # if no file was specified take the file name if the current view
    if file == "":
      less = self.view.file_name().encode("utf_8")
    else:
      less = file
    # if the file name doesn't end on .less, stop processing it
    if not less.endswith(".less"):
      return ''

    # check if an output file has been specified
    if outputFile != "" and outputFile != None:
      # if the outputfile doesn't end on .css make sure that it does by appending .css
      if not outputFile.endswith(".css"):
        css = outputFile + ".css"
      else:
        css = outputFile
    else:
      # when no output file is specified we take the name of the less file and substitute .less with .css
      if settings['min_name']:
        css = re.sub('\.less$', '.min.css', less)
      else:
        css = re.sub('\.less$', '.css', less)

    # Check if the CSS file should be written to the same folder as where the LESS file is
    if (dirs['same_dir']):
      # set the folder for the CSS file to the same folder as the LESS file
      dirs['css'] = os.path.dirname(less)
    elif (dirs['shadow_folders']):
      # replace less in the path with css, this will shadow the less folder structure
      dirs['css'] = re.sub('less', 'css', os.path.dirname(less))
    # get the file name of the CSS file, including the extension
    sub_path = os.path.basename(css)  # css file name
    # combine the folder for the CSS file with the file name, this will be our target
    css = os.path.join(dirs['css'], sub_path)

    # create directories
    # get the name of the folder where we need to save the CSS file
    output_dir = os.path.dirname(css)
    # if the folder doesn't exist, create it
    if not os.path.isdir(output_dir):
      os.makedirs(output_dir)

    # if no alternate compiler has been specified, pick the default one
    if not lessc_command:
      lessc_command = "lessc"

    # get the name of the platform (ie are we running on windows)
    platform_name = platform.system()
    # check if the compiler should create a minified CSS file
    if minimised:
      # create the command for calling the compiler
      cmd = [lessc_command, less, css, "--clean-css", "--verbose"]
      # when running on Windows we need to add an additional parameter to the call
      if platform_name == 'Windows':
        cmd[3] = '-compress'
    else:
      # the call for non minified CSS is the same on all platforms
      cmd = [lessc_command, less, css, "--verbose"]

    print("[less2css] Converting " + less + " to " + css)

    # check if we're compiling with the default compiler
    if lessc_command == "lessc":
      # check if we're on Windows
      if platform.system() == 'Windows':
        # change command from lessc to lessc.cmd on Windows,
        # only lessc.cmd works but lessc doesn't
        cmd[0] = 'lessc.cmd'
      else:
        # if is not Windows, modify the PATH
        env = os.getenv('PATH')
        env = env + ':/usr/bin:/usr/local/bin:/usr/local/sbin'
        os.environ['PATH'] = env
        # check for the existance of the less compiler, exit if it can't be located
        if subprocess.call(['which', lessc_command]) == 1:
          return sublime.error_message('less2css error: `lessc` is not available')

    #run compiler, catch an errors that might come up
    try:
      # not sure if node outputs on stderr or stdout so capture both
      p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as err:
      # an error has occured, stop processing the file any further
      return sublime.error_message('less2css error: ' + str(err))
    stdout, stderr = p.communicate()

    # create a regex to match all blank lines and control characters
    blank_line_re = re.compile('(^\s+$)|(\033\[[^m]*m)', re.M)

    # take the result text returned from node and convert it to UTF-8
    out = stderr.decode("utf_8")
    # use the regex to replace all blank lines and control characters with an empty string
    out = blank_line_re.sub('', out)

    # if out is empty it means the LESS file was succesfuly compiled to CSS, else we will print the error
    if out == '':
      print('[less2css] Convert completed!')
    else:
      print('----[less2cc] Compile Error----')
      print(out)

    return out

  # tries to find the project folder and normalize relative paths
  # such as /a/b/c/../d to /a/b/d
  # the resulting object will have the following members:
  #   - project_dir (string) = the top level folder of the project which houses the current file
  #   - less (string)        = the normalised folder specified in the base_dir parameter
  #   - css (string)         = the normalised folder where the CSS file should be stored
  #   - sameDir (bool)       = True if the CSS file should be written to the same folder as where the
  #                            LESS file is located; otherwise False
  #   - shadowFolders (bool) = True if the CSS files should follow the same folder structure as the LESS
  #                            files.
  def parseBaseDirs(self, base_dir='./', output_dir=''):
    shadow_folders = False
    # make sure we have a base and output dir before we continue. if none were provided
    # we will assign a default
    base_dir = './' if base_dir is None else base_dir
    output_dir = '' if output_dir is None else output_dir
    fn = self.view.file_name()
    # in Python 3 all string are Unicode by default, we only have to encode when running on something lower than 3
    # in addition Windows uses UTF-16 for its file names so we don't encode to UTF-8 on Windows
    if sys.version_info < (3, 0, 0) and not platform.system() is "Windows":
      fn = fn.encode("utf_8")

    # get the folder of the current file
    file_dir = os.path.dirname(fn)

    # if output_dir is set to auto, try to find appropriate destination
    if output_dir == 'auto':
      # current[0] here will be the parent folder, while current[1] is the current folder name
      current = os.path.split(file_dir)
      # parent[1] will be the parent folder name, while parent[0] is the parent's parent path
      parent = os.path.split(current[0])
      # check if the file is located in a folder called less
      if current[1] == 'less':
        # check if the less folder is located in a folder called css
        if parent[1] == 'css':
          # the current folder is less and the parent folder is css, set the css folder as the output dir
          output_dir = current[0]
        elif os.path.isdir(os.path.join(current[0], 'css')):
          # the parent folder of less has a folder named css, make this the output dir
          output_dir = os.path.join(current[0], 'css')
        else:
          # no conditions have been met, compile the file to the same folder as the less file is in
          output_dir = ''
      else:
        # we tried to automate it but failed
        output_dir = ''
    elif output_dir == 'shadow':
      shadow_folders = True
      output_dir = re.sub('less', 'css', file_dir)

    # find project path
    # you can have multiple folders at the top level in a project but there is no way
    # to get the project folder for the current file. we have to do some work to determine
    # the current project folder
    proj_dir = ''
    window = sublime.active_window()
    # this will get us all the top level folders in the project
    proj_folders = window.folders()
    # loop through all the top level folders in the project
    for folder in proj_folders:
      # we will have found the project folder when it matches with the start of the current file name
      if fn.startswith(folder):
        # keep the current folder as the project folder
        proj_dir = folder
        break

    # normalize less base path
    if not base_dir.startswith('/'):
      base_dir = os.path.normpath(os.path.join(proj_dir, base_dir))

    # if the output_dir is empty or set to ./ it means the CSS file should be placed in the same folder as the LESS file
    if output_dir == '' or output_dir == './':
      same_dir = True
    else:
      same_dir = False

    # normalize css output base path
    if not output_dir.startswith('/'):
      output_dir = os.path.normpath(os.path.join(proj_dir, output_dir))

    # return the object with all the information that is needed to be determine where to leave the CSS file when compiling
    return {'project': proj_dir, 'less': base_dir, 'css': output_dir, 'same_dir': same_dir, 'shadow_folders': shadow_folders}
