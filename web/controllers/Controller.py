from framework.nest.utils import display_view

class Controller:
    def __init__(self):
        self.routes = {}

    def route(self, path):
        def wrapper(func):
            self.routes[path] = func
            return func
        return wrapper
    
    def displayIndex(self, root_directory):
        print('Displaying Index Page')
        return display_view("index.html", root_directory)