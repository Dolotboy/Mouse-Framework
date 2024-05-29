import os
from web.controllers.Controller import Controller

def display_view(name):
    with open(name, 'r') as f:
        return f.read()

def get_routes(root_directory):
    return {
        '/': display_view("index.html"),
        '/about': display_view("about.html"),
        '/contact': display_view("contact.html"),
        '/index': Controller().displayIndex(),
    }

def handle_request(request, root_directory):
    path = request.path
    routes = get_routes(root_directory)
    if path in routes:
        response = routes[path]
        return response
    else:
        return '404 Not Found'
