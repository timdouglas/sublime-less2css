# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import re
import sys
import sublime
import itertools
import subprocess

IS_WINDOWS = True if sys.platform == 'win32' else False

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
SETTING_CREATECSSSOURCEMAPS = "createCssSourceMaps"
SETTING_AUTOPREFIX = "autoprefix"
SETTING_DISABLEVERBOSE = 'disableVerbose'


class Compiler:
    def __init__(self, view):
        self.view = view

        # get global settings and project settings
        settings = sublime.load_settings('less2css.sublime-settings')
        project_settings = sublime.active_window().active_view().settings().get(
        'less2css') or {}

        # Build a dictionary of settings using both system and
        # project setting files
        self.settings = {
            'auto_compile': project_settings.get(
                SETTING_AUTOCOMPILE, settings.get(SETTING_AUTOCOMPILE, True)
            ),
            'base_dir': project_settings.get(
                SETTING_LESSBASEDIR, settings.get(SETTING_LESSBASEDIR)
            ),
            'ignore_underscored': project_settings.get(
                SETTING_IGNOREPREFIXEDFILES,
                settings.get(SETTING_IGNOREPREFIXEDFILES, False)
            ),
            'lessc_command': project_settings.get(
                SETTING_LESSCCOMMAND,
                settings.get(SETTING_LESSCCOMMAND)
            ),
            'main_file': project_settings.get(
                SETTING_MAINFILE,
                settings.get(SETTING_MAINFILE, False)
            ),
            'minimised': project_settings.get(
                SETTING_MINIFY,
                settings.get(SETTING_MINIFY, True)
            ),
            'min_name': project_settings.get(
                SETTING_MINNAME,
                settings.get(SETTING_MINNAME, True)
            ),
            'output_dir': project_settings.get(
                SETTING_OUTPUTDIR,
                settings.get(SETTING_OUTPUTDIR)
            ),
            'output_file': project_settings.get(
                SETTING_OUTPUTFILE,
                settings.get(SETTING_OUTPUTFILE)
            ),
            'create_css_source_maps': project_settings.get(
                SETTING_CREATECSSSOURCEMAPS,
                settings.get(SETTING_CREATECSSSOURCEMAPS)
            ),
            'autoprefix': project_settings.get(
                SETTING_AUTOPREFIX,
                settings.get(SETTING_AUTOPREFIX)
            ),
            'disable_verbose': project_settings.get(
                SETTING_DISABLEVERBOSE,
                settings.get(SETTING_DISABLEVERBOSE)
            ),

        }

        # Get the filename and encode accordingly.
        self.file_name = self.view.file_name()
        if sys.version_info < (3, 0, 0):
            if IS_WINDOWS:
                self.file_name = self.file_name.encode(
                    sys.getfilesystemencoding()
                )
            else:
                self.file_name = self.file_name.encode("utf_8")

    def output_file_name(self, file_name):
        # check if an output file has been specified
        output_file = self.settings.get('output_file', '')
        if output_file:
            return output_file if output_file.endswith('.css') else \
                '{}.css'.format(output_file)
        else:
            # when no output file is specified we take the name of the less
            # file and substitute .less with .css
            if self.settings['min_name']:
                return re.sub('\.less$', '.min.css', file_name)
            else:
                return re.sub('\.less$', '.css', file_name)

    def convert_one(self, is_auto_save=False):
        """
        Used in the commands 'LessToCssCommand' and 'AutoLessToCssCommand'
        :param is_auto_save:
        :return:
        """

        # if this method is called on auto save but auto compile is not enabled,
        # stop processing the file
        if is_auto_save and not self.settings['auto_compile']:
            return ''

        # check if files starting with an underscore should be ignored and
        # if the file name starts with an underscore
        if (self.settings['ignore_underscored'] and \
            os.path.basename(self.file_name).startswith('_') and \
            is_auto_save and not self.settings['main_file']):
            print(
                "[less2css] {} ignored, file name starts with an underscore "
                "and ignorePrefixedFiles is True".format(self.file_name)
            )
            return ''

        dirs = self.parseBaseDirs(
            self.settings['base_dir'],
            self.settings['output_dir']
        )

        # if you've set the main_file (relative to current file), only that file
        # gets compiled this allows you to have one file with lots of @imports
        if self.settings['main_file']:
            self.file_name = os.path.join(
                os.path.dirname(self.file_name),
                self.settings['main_file']
            )

        # compile the LESS file
        return self.convertLess2Css(
            self.settings['lessc_command'],
            dirs=dirs,
            less_file=self.file_name,
        )

    # for command 'AllLessToCssCommand'
    def convertAll(self):
        err_count = 0

        dirs = self.parseBaseDirs(
            self.settings['base_dir'], self.settings['output_dir']
        )

        for r, d, f in os.walk(dirs['less']):
            # loop through all the files in the folder
            for files in f:
              # only process files ending on .less
                if files.endswith(".less"):
                    # check if files starting with an underscore should be
                    # ignored and if the file name starts with an underscore
                    if (self.settings['ignore_underscored'] and \
                                files.startswith('_')):
                        # print a friendly message for the user
                        print(
                            "[less2css] {} ignored, file name starts with an "
                            "underscore "
                            "and ignorePrefixedFiles is True".format(
                                os.path.join(r, files)
                            )
                        )
                    else:
                        # add path to file name
                        fn = os.path.join(r, files)
                        # call compiler
                        resp = self.convertLess2Css(
                            self.settings['lessc_command'],
                            dirs,
                            less_file=fn,
                        )
                        # check the result of the compiler,
                        # if it isn't empty an error has occured
                        if resp:
                            # keep count of the number of files that
                            # failed to compile
                            err_count += 1

        # if err_count is more than 0 it means at least 1 error occurred while
        # compiling all LESS files
        if err_count > 0:
            return "There were errors compiling all LESS files"
        return ''

    # old function name keep for legacy
    convertOne = convert_one

    # do convert
    def convertLess2Css(self, lessc_command, dirs, less_file=''):
        args = []

        # get the current file & its css variant
        # if no file was specified take the file name if the current view

        if not less_file:
            less_file = self.file_name

        # if the current file name doesn't end on .less, stop processing it
        if not self.view.file_name().endswith(".less"):
            return ''

        css_file_name = self.output_file_name(less_file)

        # Check if the CSS file should be written to the same folder as
        # where the LESS file is
        css_dir = dirs['css']
        if dirs['same_dir']:
            # set the folder for the CSS file to the same
            # folder as the LESS file
            css_dir = os.path.dirname(less_file)
        elif dirs['shadow_folders']:
            print(
                '[less2css] Using shadowed folders: outputting to {}'.format(
                    dirs['css']
                )
            )
            replacement = css_file_name.replace(
                dirs['less'],
                ''
            )
            # Strip off the slash this can cause issue within windows file paths
            css_dir = os.path.join(
                dirs['css'],
                os.path.dirname(replacement.strip('/').strip('\\'))
            )
        # get the file name of the CSS file, including the extension
        sub_path = os.path.basename(css_file_name)  # css file name
        # combine the folder for the CSS file with the file name, this
        # will be our target
        css_file_name = os.path.join(css_dir, sub_path)

        # create directories
        # get the name of the folder where we need to save the CSS file
        output_dir = os.path.dirname(css_file_name)
        # if the folder doesn't exist, create it
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        # if no alternate compiler has been specified, pick the default one
        if (type(lessc_command) is not str) or (not lessc_command):
            lessc_command = 'lessc'
        else:
            print('[less2css] Using less compiler :: {}'.format(lessc_command))
        # check if we're compiling with the default compiler
        if lessc_command == "lessc":
            if IS_WINDOWS:
                # change command from lessc to lessc.cmd on Windows,
                # only lessc.cmd works but lessc doesn't
                lessc_command = 'lessc.cmd'
            else:
                # if is not Windows, modify the PATH
                env = os.getenv('PATH')
                env = env + ':/usr/bin:/usr/local/bin:/usr/local/sbin'
                os.environ['PATH'] = env
                # check for the existance of the less compiler,
                # exit if it can't be located
                if subprocess.call(['which', lessc_command]) == 1:
                    return sublime.error_message(
                    'less2css error: `lessc` is not available'
                    )

        # check if the compiler should create a minified CSS file
        _minifier = None
        if self.settings['minimised'] is True:
            _minifier = '--clean-css'
        elif type(self.settings.get('minimised')) is str:
            _minifier = self.settings.get('minimised', '')

        if _minifier:
            print('[less2css] Using minifier : '+_minifier)
            args.append(_minifier)

        if self.settings['create_css_source_maps']:
            args.append('--source-map')
            print('[less2css] Using css source maps')

        if self.settings['autoprefix']:
            args.append('--autoprefix')
            print('[less2css] add prefixes to {}'.format(css_file_name))

        # you must opt in to disable this option
        if not self.settings['disable_verbose']:
            args.append('--verbose')
            print('[less2css] Using verbose mode')

        print("[less2css] Converting " + less_file + " to " + css_file_name)

        command = list(
            itertools.chain.from_iterable(
                [[lessc_command], args, [less_file, css_file_name]]
            )
        )

        #run compiler, catch an errors that might come up
        try:
            # not sure if node outputs on stderr or stdout so capture both
            p = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        except OSError as err:
            # an error has occured, stop processing the file any further
            return sublime.error_message('less2css error: ' + str(err))
        stdout, stderr = p.communicate()

        # create a regex to match all blank lines and control characters
        blank_line_re = re.compile('(^\s+$)|(\033\[[^m]*m)', re.M)

        # take the result text returned from node and convert it to UTF-8
        out = stderr.decode("utf_8")
        # use the regex to replace all blank lines and control characters
        # with an empty string
        out = blank_line_re.sub('', out)

        # if out is empty it means the LESS file was succesfuly compiled to CSS,
        # else we will print the error
        if not out:
            print('[less2css] Convert completed!')
        else:
            print('----[less2cc] Compile Error----')
            print(out)

        return out

    def parseBaseDirs(self, base_dir='./', output_dir=''):
        """
         tries to find the project folder and normalize relative paths
         such as /a/b/c/../d to /a/b/d
         the resulting object will have the following members:
           - project_dir (string) = the top level folder of the project which
                                    houses the current file
           - less (string)        = the normalised folder specified in the
                                    base_dir parameter
           - css (string)         = the normalised folder where the CSS file
                                    should be stored
           - sameDir (bool)       = True if the CSS file should be written to
                                    the same folder as where the
                                    LESS file is located; otherwise False
           - shadowFolders (bool) = True if the CSS files should follow the same
                                    folder structure as the LESS files.
        """
        shadow_folders = False
        # make sure we have a base and output dir before we continue.
        # if none were provided we will assign a default
        base_dir = base_dir or './'
        output_dir = output_dir or ''


        # get the folder of the current file
        file_dir = os.path.dirname(self.file_name)

        # current[0] here will be the parent folder, while current[1]
        # is the current folder name
        current = os.path.split(file_dir)

        # if output_dir is set to auto, try to find appropriate destination
        if output_dir == 'auto':
            # parent[1] will be the parent folder name, while parent[0]
            # is the parent's parent path
            parent = os.path.split(current[0])
            # check if the file is located in a folder called less
            if current[1] == 'less':
                # check if the less folder is located in a folder called css
                if parent[1] == 'css':
                    # the current folder is less and the parent folder is css,
                    # set the css folder as the output dir
                    output_dir = current[0]
                elif os.path.isdir(os.path.join(current[0], 'css')):
                    # the parent folder of less has a folder named css,
                    # make this the output dir
                    output_dir = os.path.join(current[0], 'css')
                else:
                    # no conditions have been met, compile the file to the same
                    # folder as the less file is in
                    output_dir = ''
            else:
                # we tried to automate it but failed
                output_dir = ''
        elif output_dir == 'shadow':
            shadow_folders = True
            # replace last occurrence of less with css
            parts = base_dir.rsplit('less', 1)
            output_dir = 'css'.join(parts)

        # find project path
        # you can have multiple folders at the top level in a project but
        # there is no way to get the project folder for the current file.
        # we have to do some work to determine the current project folder
        proj_dir = ''
        window = sublime.active_window()
        # this will get us all the top level folders in the project
        proj_folders = window.folders()
        # loop through all the top level folders in the project
        for folder in proj_folders:
            # we will have found the project folder when it matches
            # with the start of the current file name
            if self.file_name.startswith(folder):
                # keep the current folder as the project folder
                proj_dir = folder
                break

        # normalize less base path
        if not base_dir.startswith('/'):
            base_dir = os.path.normpath(os.path.join(proj_dir, base_dir))

        # if the output_dir is empty or set to ./ it means the CSS file should
        # be placed in the same folder as the LESS file
        if output_dir in ['', './']:
            same_dir = True
        else:
            same_dir = False

        # normalize css output base path
        if not output_dir.startswith('/'):
            output_dir = os.path.normpath(os.path.join(proj_dir, output_dir))

        # return the object with all the information that is needed to be
        # determine where to leave the CSS file when compiling
        return {
            'project': proj_dir,
            'less': base_dir,
            'css': output_dir,
            'same_dir': same_dir,
            'shadow_folders': shadow_folders
        }
