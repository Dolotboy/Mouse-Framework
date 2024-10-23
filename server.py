import http.server
import socketserver
import threading
import ctypes, sys
from dotenv import load_dotenv
import os
import platform

from framework.nest.routing.router import Router
from web.routes.route import define_routes
from framework.nest.htmlScanner import HtmlScanner

# Add the root directory to PYTHONPATH
load_dotenv()
root_directory = os.getenv('ROOT_DIRECTORY')
sys.path.append(root_directory)

def is_admin():
    if platform.system() == 'Windows':
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    else:
        return False
    
def is_running_in_docker():
    #Vérifie si le script s'exécute dans un environnement Docker.
    path = '/proc/1/cgroup'
    return os.path.exists('/.dockerenv') or (os.path.isfile(path) and any('docker' in line for line in open(path)))
    
def grant_admin_access():
    """Vérifie et accorde les privilèges administrateur si nécessaire."""
    # Si on est dans Docker, on ignore la vérification des privilèges
    if is_running_in_docker():
        print("Running in Docker, skipping admin privilege check.")
        return

    system = platform.system()

    # Sous Windows, vérifier et tenter d'élever les privilèges si nécessaire
    if system == 'Windows':
        if not is_admin():
            print("User is not admin, relaunching with admin privileges...")
            try:
                # Relancer le script avec des privilèges admin
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, " ".join(sys.argv), None, 1
                )
                sys.exit(0)  # Quitter le script original après la relance
            except Exception as e:
                print(f"Failed to elevate privileges: {e}")
                sys.exit(1)  # Quitter si l'élévation échoue

    # Sous Linux, vérifier si l'utilisateur est root (UID == 0)
    elif system in ['Linux', 'Darwin']:  # Darwin = macOS
        if not is_admin():
            print("This operation requires root privileges. Please run as root or with sudo.")
            sys.exit(1)


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        print(f"GET request received. URI: {self.path}, Headers: {self.headers}")

        # Initialise le routeur
        router = Router()
        define_routes(router, root_directory)  # Définit les routes spécifiques à l'application

        # Appelle la fonction handle_request qui utilise le Router
        response = router.handle_request(self.path)
        if response == '404 Not Found':
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'404 Not Found')
            return

        # Scanner pour remplacer la syntaxe personnalisée dans le contenu HTML
        scanner = HtmlScanner(root_directory)
        replaced_response = scanner.scan_and_replace(response)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(replaced_response.encode())

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        print(f"POST request received. URI: {self.path}, Headers: {self.headers}, Form Data: {post_data.decode()}")

        # Initialise le routeur
        router = Router()
        define_routes(router, root_directory)

        # Appelle la fonction handle_request qui utilise le Router
        response = router.handle_request(self.path)
        if response == '404 Not Found':
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'404 Not Found')
            return

        # Scanner pour remplacer la syntaxe personnalisée dans le contenu HTML
        scanner = HtmlScanner(root_directory)
        replaced_response = scanner.scan_and_replace(response)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(replaced_response.encode())

if __name__ == "__main__":
    try:
        # Vérifier et accorder les privilèges administrateur si nécessaire
        grant_admin_access()

        PORT = int(os.getenv('PORT', 8080))  # Port par défaut 8080 si non défini

        # Changer le répertoire de travail pour le répertoire racine
        os.chdir(root_directory)

        Handler = MyHttpRequestHandler

        with ThreadedTCPServer(("", PORT), Handler) as httpd:
            print("Serving at port", PORT)
            httpd.serve_forever()

    except Exception as e:
        print(f"Error: {e}")
    finally:
        input("Press enter to continue...")
