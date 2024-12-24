import requests
import re
import argparse
import json
import logging
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(
    level=logging.INFO,  # 日志等级：INFO
    format="%(asctime)s [%(levelname)s] %(message)s",  # 日志格式
    handlers=[
        logging.FileHandler("server.log"),  # 将日志写入文件
        logging.StreamHandler()  # 输出到控制台
    ]
)

CACHE_FILE = "data.json"  # 缓存文件路径

# 工具函数：按块分割列表
def list_split(items, n):
    return [items[i:i + n] for i in range(0, len(items), n)]

# 获取 GitHub 数据的函数
def getdata(name, cache_expiration_days):
    logging.info(f"Fetching data for user: {name}")

    # 检查缓存文件是否存在且未过期
    if os.path.exists(CACHE_FILE):
        file_mod_time = datetime.fromtimestamp(os.path.getmtime(CACHE_FILE))
        if datetime.now() - file_mod_time < timedelta(days=cache_expiration_days):
            logging.info("Cache file is still valid, returning cached data")
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)

    logging.info("Cache expired or not found, fetching fresh data from GitHub")

    headers = {
        'Referer': f'https://github.com/{name}',
        'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Microsoft Edge";v="122"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0',
        'X-Requested-With': 'XMLHttpRequest'
    }

    try:
        logging.info(f"Sending request to GitHub for user {name}...")
        gitpage = requests.get(f"https://github.com/{name}?action=show&controller=profiles&tab=contributions&user_id={name}", headers=headers)
        logging.info(f"Received response for user {name}, status code: {gitpage.status_code}")

        if gitpage.status_code != 200:
            logging.error(f"Failed to fetch data for user {name}, status code: {gitpage.status_code}")
            return {"error": f"Failed to fetch data, status code: {gitpage.status_code}"}

        data = gitpage.text
        datadatereg = re.compile(r'data-date="(.*?)" id="contribution-day-component')
        datacountreg = re.compile(r'<tool-tip .*?class="sr-only position-absolute">(.*?) contribution')

        datadate = datadatereg.findall(data)
        datacount = datacountreg.findall(data)
        datacount = list(map(int, [0 if i == "No" else i for i in datacount]))

        if not datadate or not datacount:
            logging.warning(f"No contribution data found for user {name}")
            return {"total": 0, "contributions": []}

        sorted_data = sorted(zip(datadate, datacount))
        datadate, datacount = zip(*sorted_data)

        contributions = sum(datacount)
        datalist = [{"date": item, "count": datacount[index]} for index, item in enumerate(datadate)]
        datalistsplit = list_split(datalist, 7)

        result = {
            "total": contributions,
            "contributions": datalistsplit
        }

        # 缓存数据到文件
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)

        logging.info(f"Successfully fetched and cached contribution data for user {name}: {contributions} total contributions")
        return result

    except Exception as e:
        logging.error(f"Error fetching data for user {name}: {e}")
        return {"error": str(e)}

# HTTP 请求处理类
class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        logging.info(f"Received GET request: {self.path}")
        if self.path.startswith("/api"):
            try:
                query = self.path.split('?')[1]
                params = dict(param.split('=') for param in query.split('&'))
                user = params.get('user')

                if not user:
                    raise ValueError("Missing 'user' parameter")

                logging.info(f"Processing request for user: {user}")
                data = getdata(user, cache_expiration_days)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(data).encode('utf-8'))
                logging.info(f"Successfully processed request for user: {user}")
            except Exception as e:
                logging.error(f"Error processing request: {e}")
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        else:
            logging.warning(f"Received invalid request: {self.path}")
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"404 Not Found")

# 启动 HTTP 服务
if __name__ == "__main__":
    # 设置命令行参数解析
    parser = argparse.ArgumentParser(description='Start an HTTP server.')
    parser.add_argument('--port', type=int, default=8080, help='Port number to run the server on')
    parser.add_argument('--cache', type=int, default=3, help='Cache expiration time in days')
    args = parser.parse_args()

    # 设置日志
    logging.basicConfig(level=logging.INFO)

    # 使用命令行参数中提供的端口
    port = args.port
    cache_expiration_days = args.cache
    logging.info(f"Starting server on port {port}...")
    try:
        server = HTTPServer(("0.0.0.0", port), RequestHandler)
        logging.info(f"Server is running at http://0.0.0.0:{port}")
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info("Server is shutting down...")
        server.server_close()
        logging.info("Server stopped successfully")