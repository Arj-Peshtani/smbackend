import os
from django.conf import settings
from .scripts import accessibility_rules

class AccessibilityRules(object):
    def __init__(self, data_paths, filename):
        self.data_paths = data_paths
        self.filename = filename
        self.modified_time = None
        self.tree = None
        self._messages = None
    def values(self):
        if self.is_data_file_modified():
            self._parse()
        return self.tree
    def messages(self):
        if self.is_data_file_modified():
            self._parse()
        return self._messages
    def is_data_file_modified(self):
        datafile = self.find_data_file(self.filename)
        new_time = os.path.getmtime(datafile)
        if self.modified_time == None or new_time > self.modified_time:
            self.modified_time = new_time
            return True
        return False
    def find_data_file(self, data_file):
        for path in self.data_paths:
            full_path = os.path.join(path, data_file)
            if os.path.exists(full_path):
                return full_path
        raise FileNotFoundError("Data file '%s' not found" % data_file)
    def _parse(self):
        tree, self._messages = (
            accessibility_rules.parse_accessibility_rules(
                self.find_data_file(self.filename)))
        self.tree = dict([(case, val.val()) for case, val in tree.items()])
 
if hasattr(settings, 'PROJECT_ROOT'):
    root_dir = settings.PROJECT_ROOT
else:
    root_dir = settings.BASE_DIR
DATA_PATHS = [os.path.join(root_dir, 'data')]
RULES = AccessibilityRules(DATA_PATHS, 'accessibility_rules.csv')
