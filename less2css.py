# -*- coding: utf-8 -*-
import sublime
import sublime_plugin
import os
try:
    import lesscompiler
except ImportError:
    from . import lesscompiler

SETTING_SHOW_ALERT = "showErrorWithWindow"


class MessageWindow:
    """
    Popup window messages
    """
    def __init__(self, message=''):
        settings = sublime.load_settings('less2css.sublime-settings')
        project_settings = sublime.active_window().active_view().settings().get(
            "less2css"
        )
        if project_settings is None:
            project_settings = {}
        self.show_alert = project_settings.get(
            SETTING_SHOW_ALERT,
            settings.get(SETTING_SHOW_ALERT, True)
        )
        self.show(message)

    def show(self, message):
        if not message:
            return

        if not self.show_alert:
            return

        sublime.error_message(message)


############################
##### SUBLIME COMMANDS #####
############################

class LessToCssCommand(sublime_plugin.TextCommand):
    """
    single less file to css
    """
    def run(self, text):
        l2c = lesscompiler.Compiler(self.view)
        resp = l2c.convert_one()
        MessageWindow(resp)


class AutoLessToCssCommand(sublime_plugin.TextCommand):
    def run(self, text):
        l2c = lesscompiler.Compiler(self.view)
        resp = l2c.convert_one(is_auto_save=True)
        MessageWindow(resp)


class AllLessToCssCommand(sublime_plugin.TextCommand):
    """
    all less files
    """
    def run(self, text):
        l2c = lesscompiler.Compiler(self.view)
        sublime.status_message("Compiling .less files...")
        resp = l2c.convertAll()

        if resp:
            MessageWindow(resp)
        else:
            sublime.message_dialog("All .less files compiled successfully")


class LessToCssSave(sublime_plugin.EventListener):
    """
    listener to current less file
    """
    def on_post_save(self, view):
        view.run_command("auto_less_to_css")


class SetLessBaseCommand(sublime_plugin.WindowCommand):
    """
    change css base setting
    """
    def run(self):
        self.window.show_input_panel(
          "Enter Your Less Base Directory: ",
          '',
          lambda s: self.set_less_setting(s),
          None,
          None
      )

    def set_less_setting(self, text):
        settings_base = 'less2css.sublime-settings'

        settings = sublime.load_settings("less2css.sublime-settings")

        if os.path.isdir(text):
            settings.set("lessBaseDir", text)
            sublime.save_settings(settings_base)

            sublime.status_message("Less Base Directory updated")
        else:
            sublime.error_message("Entered directory does not exist")


class ResetLessBaseAuto(sublime_plugin.WindowCommand):
    """
    set the css output folder to auto
    """
    def run(self):
        settings_base = 'less2css.sublime-settings'

        settings = sublime.load_settings("less2css.sublime-settings")

        settings.set("outputDir", "auto")
        sublime.save_settings(settings_base)

        sublime.status_message("Output directory reset to auto")


class SetOutputDirCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.window.show_input_panel(
            "Enter CSS Output Directory: ",
            "",
            self.set_output_dir,
            None,
            None
        )

    def set_output_dir(self, text):
        settings_base = 'less2css.sublime-settings'

        settings = sublime.load_settings("less2css.sublime-settings")

        if os.path.isdir(text):
            settings.set("outputDir", text)
            sublime.save_settings(settings_base)

            sublime.status_message("Output directory updated")
        else:
            sublime.error_message("Entered directory does not exist")


class toggleCssMinificationCommand(sublime_plugin.WindowCommand):
    """
    toggle minification
    """
    def run(self):
        #show yes/no input
        self.window.show_quick_panel(
            ["Minify css", "Don't minify css"],
            self.set_minify_flag
        )

        def set_minify_flag(self, minify):
            minify_flag = False
            settings = sublime.load_settings("less2css.sublime-settings")

            if minify == 0:
                minify_flag = True
            elif minify == -1:
                #input was cancelled, don't change
                minify_flag = settings.get("minify", True)

            settings.set("minify", minify_flag)
            sublime.save_settings("less2css.sublime-settings")

            sublime.status_message("Updated minify flag")
