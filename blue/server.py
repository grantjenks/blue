import http.server
import io
import json
import os
import pathlib
import subprocess
import tempfile

from . import __version__

INDEX_HTML = (pathlib.Path(__file__).parent / 'index.html').read_bytes()


class BlueHandler(http.server.SimpleHTTPRequestHandler):

    server_version = f'Blue/{__version__}'
    sys_version = 'Python/3'

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Length', len(INDEX_HTML))
        self.send_header('Content-Type', 'text/html; charset=UTF-8')
        self.end_headers()
        self.wfile.write(INDEX_HTML)

    def _format(self, content):
        handle, name = tempfile.mkstemp(prefix='blue-', suffix='.py')
        try:
            with os.fdopen(handle, 'w') as writer:
                writer.write(content)
            subprocess.run(['blue', name])
            with open(name) as reader:
                formatted = reader.read()
        except Exception:
            os.remove(name)
            raise
        return formatted

    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            formatted = self._format(data['content'])
            response = {'result': formatted}
            output = json.dumps(response).encode('utf-8')
        except Exception:
            self.send_response(500)
            return
        self.send_response(200)
        self.send_header('Content-Length', len(output))
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(output)


def main():
    server_address = ('', 8000)
    httpd = http.server.ThreadingHTTPServer(server_address, BlueHandler)
    httpd.serve_forever()


if __name__ == '__main__':
    main()
