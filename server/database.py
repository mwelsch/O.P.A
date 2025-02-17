class PseudoDatabase:
    def __init__(self):
        #self.last_screenshot = None
        self.database = {}

    def update_last_screenshot(self, id, file):
        self.database[id] = file

    def get_last_screenshot(self, id):
        return self.database[id]