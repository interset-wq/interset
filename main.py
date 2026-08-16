"""入口文件：本地启动开发服务器（uv run python main.py，监听 0.0.0.0:8000）。"""

import uvicorn

from app.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
