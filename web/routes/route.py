from framework.nest.routing.router import Router
from framework.nest.utils import display_view
from web.controllers.Controller import Controller

def define_routes(router, root_directory):
    router.add_route('/', lambda: display_view("index.html", root_directory))
    router.add_route('/about', lambda: display_view("about.html", root_directory))
    router.add_route('/contact', lambda: display_view("contact.html", root_directory))
    router.add_route('/index', lambda: Controller().displayIndex(root_directory))