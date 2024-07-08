import http.server
import socketserver
import threading
import ctypes, sys
from dotenv import load_dotenv
import os

# Add the root directory to PYTHONPATH
load_dotenv()
root_directory = os.getenv('ROOT_DIRECTORY')
sys.path.append(root_directory)

from web.routes.route import handle_request

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        print(f"GET request received. URI: {self.path}, Headers: {self.headers}")
        response = handle_request(self, root_directory)
        print(f"Response from handle_request: {response}")
        if response == '404 Not Found':
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'404 Not Found')
            return

        self.send_response(200)
        self.end_headers()
        self.wfile.write(response.encode())

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        print(f"POST request received. URI: {self.path}, Headers: {self.headers}, Form Data: {post_data.decode()}")

        response = handle_request(self, root_directory)
        print(f"Response from handle_request: {response}")
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
            PORT = int(os.getenv('PORT'))

            # Change working directory to the root directory
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
        print(f"Error: {e}")
    finally:
        input("Press enter to continue...")
