import sublime, sublime_plugin
import subprocess
import re

#define methods to convert css, either the current file or all
class LessToCss:
  def __init__(self, view):
    self.view = view

  def convertOne(self):
    #get the current file & its css variant
    fn = self.view.file_name().encode("utf_8")
    fn_css = re.sub('\.less', '.css', fn)
    cmd = ["lessc", fn, fn_css, "-x", "--verbose"]

    p = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr=subprocess.PIPE)

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
    #call generic *.less > *.css command
    p = subprocess.Popen('ae-less2css', stdout = subprocess.PIPE, stderr=subprocess.PIPE)

    while True:
      try:
        stdout, stderr = p.communicate()
      except ValueError:
        break
      #remove control characters  
      out = stderr.decode("ascii")
      out = re.sub('\033\[[^m]*m', '', out)

    return out  




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
      resp = l2c.convertOne()

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
      sublime.message_box("All .less files compiled successfully")

#listener to current less file
class LessToCssSave(sublime_plugin.EventListener):
  def on_post_save(self, view):
    view.run_command("less_to_css")