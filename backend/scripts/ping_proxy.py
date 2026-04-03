"""
Ping 代理服务 — 运行在宿主机上，供 Docker 容器调用。
用法: python ping_proxy.py
监听: 0.0.0.0:8001
使用多线程处理并发请求。
"""
import platform
import subprocess
import json
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn


def ping_ip(ip_address, timeout=2, count=1):
    try:
        system = platform.system().lower()
        if system == "windows":
            cmd = ["ping", "-n", str(count), "-w", str(timeout * 1000), ip_address]
        else:
            cmd = ["ping", "-c", str(count), "-W", str(timeout), ip_address]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 3)
        is_online = result.returncode == 0

        response_time = None
        if is_online:
            output = result.stdout
            if system == "windows":
                m = re.search(r'[=<](\d+)ms', output)
            else:
                m = re.search(r'time[=<](\d+\.?\d*)\s*ms', output)
            if m:
                response_time = float(m.group(1))

        return {"is_online": is_online, "response_time": response_time, "error": None}
    except subprocess.TimeoutExpired:
        return {"is_online": False, "response_time": None, "error": "timeout"}
    except Exception as e:
        return {"is_online": False, "response_time": None, "error": str(e)}


class PingHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/ping":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            ip = body.get("ip_address", "")
            timeout = body.get("timeout", 2)
            count = body.get("count", 1)

            if not ip:
                self._respond(400, {"error": "ip_address required"})
                return

            result = ping_ip(ip, timeout, count)
            self._respond(200, result)
        else:
            self._respond(404, {"error": "not found"})

    def do_GET(self):
        if self.path == "/health":
            self._respond(200, {"status": "ok"})
        else:
            self._respond(404, {"error": "not found"})

    def _respond(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        pass  # 静默日志，避免刷屏


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """多线程 HTTP 服务器，支持并发请求"""
    daemon_threads = True


if __name__ == "__main__":
    port = 8001
    server = ThreadedHTTPServer(("0.0.0.0", port), PingHandler)
    print(f"Ping proxy started on 0.0.0.0:{port} (threaded)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped")
        server.server_close()
