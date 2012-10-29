import sublime, sublime_plugin
import subprocess, platform, re, os

#define methods to convert css, either the current file or all
class Compiler:
  def __init__(self, view):
    self.view = view

  def convertOne(self, file="", is_auto_save = False):
    #get the current file & its css variant
    if file == "":
      fn = self.view.file_name().encode("utf_8")
    else:
      fn = file

    if fn.find(".less") < 0:
      return ''

    default_output_dir = fn[0:fn.rfind(os.path.sep)]

    fn_css = re.sub('\.less', '.css', fn)

    settings = sublime.load_settings('less2css.sublime-settings')
    output_dir = settings.get("outputDir", default_output_dir)
    minimised = settings.get("minify", True)
    auto_compile = settings.get("autoCompile", True)

    if auto_compile == False and is_auto_save == True:
      return ''

    #".split(x)[1]" returns the file.css part of the /whole/path/
    css_output = os.path.join(output_dir, os.path.split(fn_css)[1])

    if minimised == True:
      cmd = ["lessc", fn, css_output, "-x", "--verbose"]
    else:
      cmd = ["lessc", fn, css_output, "--verbose"]

    print "[less2css] Converting "+fn+" to "+css_output

    # set environment
    env = os.getenv('PATH')
    #if is not windows, modify system path
    if platform.system != 'Windows':
      env = env + ':/usr/local/bin:/usr/local/sbin'
    os.environ['PATH'] = env

    #run compiler
    p = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr=subprocess.PIPE) #not sure if node outputs on stderr or stdout so capture both

    out = ''

    #blank lines and control characters
    blank_line = re.compile('(^\s+$)|(\033\[[^m]*m)', re.M)

    while True:
      try:
        stdout, stderr = p.communicate()
      except ValueError:
        break
      #decode and replace blank lines
      out = stderr.decode("ascii")
      out = blank_line.sub('', out)

    if out != '':
      print '----Error----'
      print out

    return out

  def convertAll(self):
    err_count = 0;

    settings = sublime.load_settings('less2css.sublime-settings')
    base = settings.get("lessBaseDir")

    out = []

    for r,d,f in os.walk(base):
      for files in f:
        if files.endswith(".less"):
          #add path to file name
          fn = os.path.join(r, files)
          #call compiler
          resp = self.convertOne(fn)

          if resp != "":
            err_count = err_count + 1
            out.append({"file": fn, "message": out})

    if err_count > 0:
      return "There were errors compiling all LESS files"
    else:
      return ''
