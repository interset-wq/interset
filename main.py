from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

# 页面路由：仅h1 Hello World，纯HTML无CSS
@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <html>
        <body>
            <h1>Hello World</h1>
        </body>
    </html>
    """

# API接口，返回JSON
@app.get("/info")
async def api_info():
    return {"msg": "this is api response", "code": 200}

@app.post("/data")
async def api_data(name: str):
    return {"receive_name": name, "status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)