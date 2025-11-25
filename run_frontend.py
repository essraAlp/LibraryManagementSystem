"""
Script to run the frontend web server
"""
import os
import http.server
import socketserver
import webbrowser

PORT = 8080

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

if __name__ == "__main__":
    # Change to the web directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    web_dir = os.path.join(project_dir, "web")
    os.chdir(web_dir)
    
    print("=" * 60)
    print("Starting Frontend Web Server")
    print("=" * 60)
    print(f"Serving files from: {web_dir}")
    print(f"Frontend will be available at: http://localhost:{PORT}")
    print(f"Open this URL in your browser: http://localhost:{PORT}/index.html")
    print("Press CTRL+C to stop the server")
    print("=" * 60)
    print()
    
    Handler = MyHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"Server is running on port {PORT}...")
            print("\nOpening browser...")
            webbrowser.open(f'http://localhost:{PORT}/index.html')
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nFrontend server stopped.")
    except OSError as e:
        if "address already in use" in str(e).lower():
            print(f"\nError: Port {PORT} is already in use.")
            print("Either stop the other server or change the PORT variable in this script.")
        else:
            print(f"\nError: {e}")
