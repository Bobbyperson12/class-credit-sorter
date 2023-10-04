from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import json

data_folder = Path("backend/data/") # TODO: Will cause errors if not run from main folder, needs a fix.

hostName = "localhost"
serverPort = 8080

class MainServer(BaseHTTPRequestHandler):
    # Setup basic json request
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header("Access-Control-Allow-Origin", "*") # needs to be changed off of * in a prod environment
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")  # Allow these methods
        self.send_header("Access-Control-Allow-Headers", "Content-Type")  # Allow Content-Type header
        self.end_headers()

    def do_OPTIONS(self): # inform browser of what methods are allowed
        self._set_headers()

        
    # GET sends back the required classes for the degree
    def do_GET(self):
        self._set_headers()
        degree = self.path[1:] # Remove the beginning slash
        file_lines = self.get_required_classes(degree)

        if file_lines == []:
            degree_message = None,
            required_classes = None,
            error = True, 
            error_message = "Degree not found."
        else:
            degree_message = self.get_full_degree_name(degree)
            required_classes = file_lines
            error = False
            error_message = None
        response = {
            "degree": degree_message,
            "required_classes": required_classes,
            "error": error,
            "error_message": error_message
        }

        self.wfile.write(bytes(json.dumps(response), "utf-8"))
        
    def do_POST(self):
        self._set_headers()

        # Extract and parse POST data
        content_length = int(self.headers['Content-Length'])  # Get the size of data
        post_data = self.rfile.read(content_length)  # Get the data
        parsed_data = json.loads(post_data)  # Parse the JSON data

        # Extract the required data
        degree = parsed_data.get("degree", "")
        # other_info = parsed_data.get("other_info")  # If you need other info

        file_lines = self.get_required_classes(degree)

        if file_lines == []:
            degree_message = None
            required_classes = None
            error = True
            error_message = "Degree not found."
        else:
            degree_message = self.get_full_degree_name(degree)
            required_classes = file_lines
            error = False
            error_message = None

        response = {
            "degree": degree_message,
            "required_classes": required_classes,
            "error": error,
            "error_message": error_message
        }

        self.wfile.write(bytes(json.dumps(response), "utf-8"))

        
    def get_required_classes(self, degree) -> list:
        """
        Takes a degree as input and returns the required classes for that
        degree.
        
        Args:
            degree (str): Shortened version of the degree name. Ex: "CS-Major"

        Returns:
            str: Required classes for the degree
        """
        try:
            with open(str(data_folder.absolute()) + "/" + degree + ".csv", "r") as f:
                file_lines = [line.rstrip() for line in f.readlines()] # Get each class and strip the newline character
                return file_lines[1:] # First line is the degree name, so we skip it
        except FileNotFoundError:
            return []
        
    def get_full_degree_name(self, degree: str) -> str:
        """
        Takes a degree as input and returns the full name of the degree.

        Args:
            degree (str): Shortened version of the degree name. Ex: "CS-Major"

        Returns:
            str: Full degree name
        """
        try:
            with open(str(data_folder.absolute()) + "/" + degree + ".csv", "r") as f:
                file_lines = [line.rstrip() for line in f.readlines()] # Get each class and strip the newline character
                return file_lines[0] # type: ignore # First line is the degree name, so we only return that
        except FileNotFoundError:
            return ""
        
    
    
if __name__ == "__main__":        
    webServer = HTTPServer((hostName, serverPort), MainServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")