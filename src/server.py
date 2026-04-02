import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
import traceback
import json
import reccomend_devs

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Handle API requests
        if self.path.startswith('/api/'):
            try:
                self.handle_api()
            except Exception as e:
                print(traceback.format_exc())
                self.send_response(500)
                pass
        else:
            # Serve static files from ./public directory
            self.directory = './public'
            super().do_GET()

    def do_POST(self):
        if self.path.startswith('/api/'):
            try:
                self.handle_api()
            except Exception as e:
                print(traceback.format_exc())
                self.send_response(500)
                pass

    def handle_api(self):
        # Parse the path
        parsed_path = urlparse(self.path)
        api_path = parsed_path.path
        query = parse_qs(parsed_path.query)

        # Example: respond to /api/data
        if api_path == '/api/ping':
                self.send_response(200)
                self.wfile.write(b"Pong!")
        elif api_path == '/api/query.json':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                funcs = query["names"][0].split(" ")
                res = reccomend_devs.doStuff(
                    "expertise_map.json", funcs,
                    not query.get("simple", ["true"])[0] == "false", float(query.get("modWeight", ["2"])[0]),
                    float(query.get("callWeight", ["1"])[0]), float(query.get("decayWindow", ["720"])[0]),
                    float(query.get("diversityWeight", ["0.25"])[0]), float(query.get("consistencyWeight", ["10"])[0]),
                    False
                )
                devs = []
                for item in res:
                    dev_id = item[0]
                    score = item[1]
                    methods_dict = item[2]
                    
                    methods_list = []
                    for method_name, stats in methods_dict.items():
                        method_obj = {
                            "name": method_name,
                            "commits": stats["totalHits"],
                            "modifications": stats["modScore"],
                            "calls": stats["callScore"]
                        }
                        methods_list.append(method_obj)
                    
                    devs.append({
                        "id": dev_id,
                        "score": score,
                        "methods": methods_list,
                        "github": reccomend_devs.userMap['accounts'].get(dev_id, None)
                    })
                self.wfile.write(json.dumps({"devs": devs}).encode())

PORT = 3000
socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
    print(f"Server running at http://localhost:{PORT}/")
    httpd.serve_forever()

