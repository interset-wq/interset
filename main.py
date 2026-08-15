from fastapi import FastAPI

# 创建app实例
app = FastAPI(title="最简FastAPI Demo")

# 根路径GET接口
@app.get("/")
def root():
    return {"msg": "hello fastapi", "code": 200}

# 带路径参数接口
@app.get("/hello/{name}")
def say_hello(name: str):
    return {"message": f"你好，{name}"}

# post请求示例，接收json
from pydantic import BaseModel

class User(BaseModel):
    username: str
    age: int

@app.post("/user")
def create_user(user: User):
    return {"username": user.username, "age": user.age, "status": "created"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
