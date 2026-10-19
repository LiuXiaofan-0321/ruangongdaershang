#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
操作系统学习指南 · 本地服务 + AI 代理
作用：
  1. 以 http://127.0.0.1:8321/ 提供本目录下的学习指南页面
  2. 把页面发往 /v1/* 的请求转发到真实的 AI 端点，并自动补上 CORS 头，
     解决浏览器直连 http://154.9.227.59:6181 时的跨域拦截问题
用法：直接运行本脚本（或双击"启动指南.bat"），浏览器会自动打开指南。
"""
import http.server
import urllib.request
import urllib.error
import webbrowser
import sys

LISTEN_HOST = "127.0.0.1"
LISTEN_PORT = 8321
UPSTREAM = "http://154.9.227.59:6181"   # 真实 AI 端点（不含 /v1 前缀，转发时保留路径）
PAGE = "操作系统学习指南.html"

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Authorization, Content-Type",
}

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):  # 保持控制台干净，仅打印错误
        pass

    # ---- 预检请求：直接放行 ----
    def do_OPTIONS(self):
        self.send_response(204)
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)
        self.end_headers()

    # ---- 静态文件 ----
    def do_GET(self):
        if self.path.startswith("/v1/"):
            return self._proxy("GET")
        return super().do_GET()

    # ---- API 代理 ----
    def do_POST(self):
        if self.path.startswith("/v1/"):
            return self._proxy("POST")
        self.send_error(404)

    def _proxy(self, method):
        length = int(self.headers.get("Content-Length", 0))
        payload = self.rfile.read(length) if length else None
        req = urllib.request.Request(
            UPSTREAM + self.path, data=payload, method=method,
            headers={
                "Content-Type": self.headers.get("Content-Type", "application/json"),
                "Authorization": self.headers.get("Authorization", ""),
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = resp.read()
                self._send(resp.status, body, resp.headers.get("Content-Type", "application/json"))
        except urllib.error.HTTPError as e:   # 上游 4xx/5xx 原样透传，方便前端展示真实错误
            self._send(e.code, e.read(), "application/json")
        except Exception as e:
            self._send(502, ('{"error":"proxy: %s"}' % e).encode("utf-8"), "application/json")

    def _send(self, status, body, ctype):
        self.send_response(status)
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

if __name__ == "__main__":
    url = f"http://{LISTEN_HOST}:{LISTEN_PORT}/{PAGE}"
    print(f"✅ 学习指南服务已启动: {url}")
    print(f"🔀 AI 代理: /v1/* -> {UPSTREAM}/v1/*  （按 Ctrl+C 停止）")
    if "--no-browser" not in sys.argv:
        webbrowser.open(url)
    http.server.ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), Handler).serve_forever()
