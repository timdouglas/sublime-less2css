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

    print file

    fn_css = re.sub('\.less', '.css', fn)

    cmd = ["lessc", fn, fn_css, "-x", "--verbose"]

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
    base = settings.get("cssBaseDir")

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
class SetCssBaseCommand(sublime_plugin.WindowCommand):
  def run(self):
    self.window.show_input_panel("Enter Your CSS Base Directory: ", '', lambda s: self.set_css_setting(s), None, None)

  def set_css_setting(self, text):
    settings_base = 'less2css.sublime-settings'

    settings = sublime.load_settings(settings_base)
    
    if os.path.isdir(text):
      settings.set("cssBaseDir", text)
      sublime.save_settings(settings_base) #have to assume this is successful...

      sublime.status_message("CSS Base Directory updated")
    else:
      sublime.error_message("Entered directory does not exist")