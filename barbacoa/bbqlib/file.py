import os
from PyQt4 import QtGui


class File():

    def __init__(self, barbacoa):
        self.barbacoa = barbacoa

    def read(self, filename):
        with open(filename, 'r') as f:
            content = f.read()
        self.barbacoa.respond(content)

    def write(self, filename, content):
        with open(filename, 'w') as f:
            f.write(content)

    def choose_directory(self, selected_dir):
        if not selected_dir:
            selected_dir = os.path.expanduser('~')
        path = str(QtGui.QFileDialog().getExistingDirectory(None, "Choose directory", selected_dir))
        self.barbacoa.respond(path)