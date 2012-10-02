import sublime, sublime_plugin
import subprocess
import re
import os

#define methods to convert css, either the current file or all
class LessToCss:
  def __init__(self, view):
    self.view = view

  def convertOne(self, file=""):

    #get the current file & its css variant
    if file == "":
      fn = self.view.file_name().encode("utf_8")
    else:
      fn = file

    fn_css = re.sub('\.less', '.css', fn)

    window = sublime.active_window()
    proj_folders = window.folders()

    settings = sublime.load_settings('less2css.sublime-settings')
    output_dir = settings.get("outputDir", proj_folders[0])
    minimised = settings.get("minify", True)

    #".split(x)[1]" returns the file.css part of the /whole/path/
    css_output = os.path.join(output_dir, os.path.split(fn_css)[1])

    if minimised == True:
      cmd = ["lessc", fn, css_output, "-x", "--verbose"]
    else:
      cmd = ["lessc", fn, css_output, "--verbose"]

    print "[less2css] Converting "+fn+" to "+css_output

    #run compiler
    p = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr=subprocess.PIPE) #not sure if node outputs on stderr or stdout so capture both

    while True:
      try:
        stdout, stderr = p.communicate()
      except ValueError:
        break
      #remove control characters  
      out = stderr.decode("ascii")
      out = re.sub('\033\[[^m]*m', '', out)

    return out

  def convertAll(self):
    err_count = 0;

    settings = sublime.load_settings('less2css.sublime-settings')
    base = settings.get("lessBaseDir")

    for r,d,f in os.walk(base):
      for files in f:
        if files.endswith(".less"):
          #add path to file name
          fn = os.path.join(r, files)
          #call compiler
          resp = self.convertOne(fn)

          if resp != "":
            err_count = err_count + 1

    if err_count > 0:
      return "There were errors compiling all LESS files"
    else:
      return ""


############################
##### SUBLIME COMMANDS #####
############################

#single less file
class LessToCssCommand(sublime_plugin.TextCommand):
  def run(self, text):
    l2c = LessToCss(self.view)
    fn = self.view.file_name().encode("utf_8")
    
    if fn.find(".less") > -1:
      sublime.status_message("Compiling .less files...")
      resp = l2c.convertOne("")

      if resp != "":
        sublime.error_message(resp)
      else:
        sublime.status_message(".less file compiled successfully")

#all less files
class AllLessToCssCommand(sublime_plugin.TextCommand):
  def run(self, text):
    l2c = LessToCss(self.view)
    sublime.status_message("Compiling .less files...")
    resp = l2c.convertAll()

    if resp != "":
      sublime.error_message(resp)
    else:
      sublime.message_dialog("All .less files compiled successfully")

#listener to current less file
class LessToCssSave(sublime_plugin.EventListener):
  def on_post_save(self, view):
    view.run_command("less_to_css")

#change css base setting
class SetLessBaseCommand(sublime_plugin.WindowCommand):
  def run(self):
    self.window.show_input_panel("Enter Your Less Base Directory: ", '', lambda s: self.set_less_setting(s), None, None)

  def set_less_setting(self, text):
    settings_base = 'less2css.sublime-settings'

    settings = sublime.load_settings(settings_base)
    
    if os.path.isdir(text):
      settings.set("lessBaseDir", text)
      sublime.save_settings(settings_base) #have to assume this is successful...

      sublime.status_message("Less Base Directory updated")
    else:
      sublime.error_message("Entered directory does not exist")

class SetOutputDirCommand(sublime_plugin.WindowCommand):
  def run(self):
    self.window.show_input_panel("Enter CSS Output Directory: ", "", lambda s: self.set_output_dir(s), None, None)

  def set_output_dir(self, text):
    settings_base = 'less2css.sublime-settings'

    settings = sublime.load_settings(settings_base)
    
    if os.path.isdir(text):
      settings.set("outputDir", text)
      sublime.save_settings(settings_base)

      sublime.status_message("Output directory updated")
    else:
      sublime.error_message("Entered directory does not exist")

#toggle minification
class toggleCssMinificationCommand(sublime_plugin.WindowCommand):
  def run(self):
    #show yes/no input
    self.window.show_quick_panel(["Minify css", "Don't minify css"], lambda s: self.set_minify_flag(s))

  def set_minify_flag(self, minify):
    minify_flag = False

    if minify == 0:
      minify_flag = True

    settings_base = 'less2css.sublime-settings'
    settings = sublime.load_settings(settings_base)

    if minify == -1:
      #input was cancelled, don't change
      minify_flag = settings.get("minify", True) #existing or default

    settings.set("minify", minify_flag)
    sublime.save_settings(settings_base)

    sublime.status_message("Updated minify flag")
