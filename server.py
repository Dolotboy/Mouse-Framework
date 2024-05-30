import http.server
import socketserver
import threading
import ctypes, sys
from dotenv import load_dotenv
from route import handle_request
import os

load_dotenv()
root_directory = os.getenv('ROOT_DIRECTORY')
PORT = int(os.getenv('PORT'))

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        #print(f"GET request received. URI: {self.path}, Headers: {self.headers}")
        response = handle_request(self, root_directory)
        if isinstance(response, str):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(response.encode())
        elif callable(response):
            # Si 'response' est une fonction, appelez-la pour obtenir la chaîne de caractères
            response_content = response()
            if isinstance(response_content, str):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(response_content.encode())
        else:
            # Gérez les autres types de réponses ou erreurs ici
            pass

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        print(f"POST request received. URI: {self.path}, Headers: {self.headers}, Forms Data: {post_data.decode()}")

        response = handle_request(self, root_directory)
        if response == '404 Not Found':
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'404 Not Found')
            return

        self.send_response(200)
        self.end_headers()
        self.wfile.write(response.encode())

if __name__ == "__main__":
    try:
        if is_admin():

            # Change working directory to 'web'
            os.chdir(root_directory)

            Handler = MyHttpRequestHandler

            with ThreadedTCPServer(("", PORT), Handler) as httpd:
                print("Serving at port", PORT)
                httpd.serve_forever()
        else:
            print("User is not admin, relaunch in admin mode")
            # Re-run the program with admin rights
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    except Exception as e:
        print(f"Error : {e}")
    finally:
        input("Press enter to continue...")
