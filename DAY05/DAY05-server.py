#server.py
import socketserver

class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        self.wfile.write(b"Welcome!\n")
        self.wfile.write(b"Number: ")
        self.wfile.flush()

        data = self.rfile.readline()
        if not data:
            return

        try:
            number = int(data.strip())
        except ValueError:
            self.wfile.write(b"Invalid number\n")
            return

        self.wfile.write(
            f"Result: {number * 2}\n".encode()
        )
        self.wfile.flush()

class Server(socketserver.TCPServer):
    allow_reuse_address = True

with Server(("127.0.0.1", 9001), Handler) as server:
    print("Listening on 127.0.0.1:9001", flush=True)
    server.serve_forever()