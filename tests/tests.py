import unittest
import tempfile
import sys
import os

# append the plugin dir to system path so we can import stuff
sys.path.append(
    os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
)


# fake some modules
class sublime:
    class Dummy:
        @staticmethod
        def folders():
            return [os.environ.get("test_project_dir")]

    @staticmethod
    def active_window():
        return sublime.Dummy()


class sublime_plugin:
    pass

sys.modules['sublime'] = sublime
sys.modules['sublime_plugin'] = sublime_plugin

from lesscompiler import Compiler

# allways ./ ??
BASE_DIR = './'
LESS_FILE = "foo.less"
CSS_FILE = "bar.css"


###
### Dummy view so we can instantiate the Compiler
###
class DummyView:
    def __init__(self, project_dir):
        self.project_dir = project_dir

    def file_name(self):
        # less file to compile
        return os.path.join(self.project_dir, LESS_FILE)


class TestOuputDir(unittest.TestCase):
    def setUp(self):
        # create the project dir
        self.project_dir = tempfile.mkdtemp()
        os.environ['test_project_dir'] = self.project_dir
        # the less file to compile
        self.dummy_view = DummyView(self.project_dir)
        # create the dummy less file
        open(self.dummy_view.file_name(), 'w').close()
        # the compiler
        self.compiler = Compiler(self.dummy_view)

    def test_absolute_path_same_name(self):
        print "Running %s" % self._testMethodName
        # Providing an absolute path inside the project dir
        # because that's in tmp and we have write access
        # but should work with any path
        self.output = os.path.join(self.project_dir, 'absolute')  # something like /tmp/tmpJshx/absolute
        self.compiler.convertLess2Css(self.compiler.parseBaseDirs(BASE_DIR, self.output))

        # open the created file
        with open(os.path.join(self.output, LESS_FILE.replace(".less", ".css")), "r") as f:
            self.assertIsInstance(f, file)

    def test_absolute_path_provided_name(self):
        print "Running %s" % self._testMethodName
        # Providing an absolute path inside the project dir
        # because that's in tmp and we have write access
        # but should work with any path
        self.output = os.path.join(self.project_dir, 'absolute')  # something like /tmp/tmpJshx/absolute
        self.compiler.convertLess2Css(self.compiler.parseBaseDirs(BASE_DIR, self.output), outputFile=CSS_FILE)

        # open the created file
        with open(os.path.join(self.output, CSS_FILE), "r") as f:
            self.assertIsInstance(f, file)

    def test_relative_path_same_name(self):
        print "Running %s" % self._testMethodName
        self.output = 'relative/path'  # something like /tmp/tmpJshx/relative/path
        self.compiler.convertLess2Css(self.compiler.parseBaseDirs(BASE_DIR, self.output))

        # open the created file
        with open(os.path.join(self.project_dir, self.output, LESS_FILE.replace(".less", ".css")), "r") as f:
            self.assertIsInstance(f, file)

    def test_relative_path_provided_name(self):
        print "Running %s" % self._testMethodName
        self.output = 'relative/path'  # something like /tmp/tmpJshx/relative/path
        self.compiler.convertLess2Css(self.compiler.parseBaseDirs(BASE_DIR, self.output), outputFile=CSS_FILE)

        # open the created file
        with open(os.path.join(self.project_dir, self.output, CSS_FILE), "r") as f:
            self.assertIsInstance(f, file)

    def test_dot_path_same_name(self):
        print "Running %s" % self._testMethodName
        self.output = './'
        self.compiler.convertLess2Css(self.compiler.parseBaseDirs(BASE_DIR, self.output))

        # open the created file
        with open(os.path.join(self.project_dir, self.output, LESS_FILE.replace(".less", ".css")), "r") as f:
            self.assertIsInstance(f, file)

    def test_dot_path_provided_name(self):
        print "Running %s" % self._testMethodName
        self.output = './'
        self.compiler.convertLess2Css(self.compiler.parseBaseDirs(BASE_DIR, self.output), outputFile=CSS_FILE)

        # open the created file
        with open(os.path.join(self.project_dir, self.output, CSS_FILE), "r") as f:
            self.assertIsInstance(f, file)

    def test_empty_path_same_name(self):
        print "Running %s" % self._testMethodName
        self.output = ''
        self.compiler.convertLess2Css(self.compiler.parseBaseDirs(BASE_DIR, self.output))

        # open the created file
        with open(os.path.join(self.project_dir, self.output, LESS_FILE.replace(".less", ".css")), "r") as f:
            self.assertIsInstance(f, file)

    def test_empty_path_provided_name(self):
        print "Running %s" % self._testMethodName
        self.output = ''
        self.compiler.convertLess2Css(self.compiler.parseBaseDirs(BASE_DIR, self.output), outputFile=CSS_FILE)

        # open the created file
        with open(os.path.join(self.project_dir, self.output, CSS_FILE), "r") as f:
            self.assertIsInstance(f, file)

if __name__ == "__main__":
    unittest.main()
