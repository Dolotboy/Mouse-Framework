class Controller:
    def __init__(self):
        self.routes = {}

    def route(self, path):
        def wrapper(func):
            self.routes[path] = func
            return func
        return wrapper
    
    def displayIndex(self):
        print('Hey')
        with open("index.html", 'r') as f:
            return f.read()