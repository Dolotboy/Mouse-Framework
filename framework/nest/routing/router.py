import os

class Router:
    def __init__(self):
        self.routes = {}

    def add_route(self, path, handler):
        self.routes[path] = handler

    def handle_request(self, path):
        if path in self.routes:
            return self.routes[path]()
        return '404 Not Found'
