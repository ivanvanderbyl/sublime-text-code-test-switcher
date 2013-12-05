import os
import re
import functools
import sublime
import string
import sublime_plugin

class SwitchBetweenCodeAndTest(sublime_plugin.TextCommand):
  def run(self, args):
    opposite_file_name = self.opposite_file_name()
    alternates = self.project_files(opposite_file_name)

    if alternates:
      if len(alternates) == 1:
        self.view.window().open_file(alternates.pop())
      else:
        callback = functools.partial(self.on_selected, alternates)
        self.view.window().show_quick_panel(alternates, callback)
    else:
      sublime.error_message("No file found")

  def opposite_file_name(self):
    file_name = self.view.file_name().split(os.sep)[-1]
    if re.search('\w+\_test\.\w+', file_name):
      return file_name.replace("_test", "")
    else:
      return file_name.replace(".py", "_test.py")

  def on_selected(self, alternates, index):
    if index == -1:
      return

    self.view.window().open_file(alternates[index])

  def walk(self, directory):
    for dir, dirnames, files in os.walk(directory):
      # Skip hidden directories
      if re.search('(^|\/)\.', dir):
        continue
      dirnames[:] = [dirname for dirname in dirnames]
      yield dir, dirnames, files

  def project_files(self, file_matcher):
    directories = self.view.window().folders()
    candidates = []
    for directory in directories:
      for dirname, _, files in self.walk(directory):
        for file in files:
          if file == file_matcher:
            candidates += [os.path.join(dirname, file)]
    return candidates

# Copy to clipboard test path in a form:
# testify [test_path] [test_class].[test_name]
class PrepareTestCommander(sublime_plugin.TextCommand):
  def run(self, args):
    test_name, test_class = self.extract_class_and_name()
    if not self.is_present(test_name, "No test function!"):
      return
    if not self.is_present(test_class, "No test class!"):
      return

    test_path = self.extract_path()
    if not self.is_present(test_path, "Wrong project/file path!"):
      return

    test_command = "testify %s %s.%s" % (test_path, test_class, test_name)
    sublime.set_clipboard(test_command)
    sublime.status_message(test_command)

  def extract_class_and_name(self):
    region = self.view.sel()[0]
    line_region = self.view.line(region)
    text_string = self.view.substr(sublime.Region(region.begin() - 65536, line_region.end()))
    text_string = text_string.replace("\n", "\\N")
    text_string = text_string[::-1]

    test_name, test_class = ['', '']
    match_obj = re.search(':\)fles\(([a-zA-Z_\d]+_tset) fed', text_string) # 1st search for 'def test_[name](self):'
    if match_obj:
      test_name = match_obj.group(1)[::-1]

    match_obj = re.search('\:\)[a-zA-Z_.\d]+\(([a-zA-Z_\d]+) ssalc', text_string) # 2nd search for 'class [Name]Test([inherit_from]):'
    if match_obj:
      test_class = match_obj.group(1)[::-1]

    return [test_name, test_class]

  def extract_path(self):
    directories = self.view.window().folders()
    file_path = self.view.file_name()
    test_path = ''

    for directory in directories:
      if re.search(directory, file_path):
        test_path = file_path.replace(directory + '/', '')
        break

    test_path = re.sub('.py$', '', test_path)
    test_path = re.sub('\/', '.', test_path)

    return test_path

  def is_present(self, content, message):
    if len(content) == 0:
      sublime.error_message(message)
      return False
    else:
      return True
