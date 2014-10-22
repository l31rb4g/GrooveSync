import os


class Environment():

    def __init__(self, barbacoa):
        self.barbacoa = barbacoa

    def get_user_home(self):
        path = os.path.expanduser('~')
        self.barbacoa.respond(path)