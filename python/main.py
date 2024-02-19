import os
import logging
import pathlib
from fastapi import FastAPI, Form, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import hashlib


app = FastAPI()
logger = logging.getLogger("uvicorn")
logger.level = logging.INFO
images = pathlib.Path(__file__).parent.resolve() / "images"
origins = [os.environ.get("FRONT_URL", "http://localhost:3000")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


def read_items_from_json():
    with open('items.json', 'r') as file:
        data = json.load(file)
    return data['items']

@app.get("/items")
def read_items():
    items = read_items_from_json()
    return {"items": items}

@app.get("/items/{item_id}")
def read_item(item_id: int):
    items = read_items_from_json()  # 这个函数应该从你之前的步骤中已经实现
    if item_id < 0 or item_id >= len(items):
        raise HTTPException(status_code=404, detail="Item not found")
    return items[item_id]


@app.get("/")
def root():
    return {"message": "Hello, world!"}

@app.post("/items")
async def add_item(name: str = Form(...), category: str = Form(...), image: UploadFile = File(...)):
    # 读取图片内容
    image_data = await image.read()
    # 生成图片哈希值
    image_hash = hashlib.sha256(image_data).hexdigest()
    # 保存图片到硬盘
    file_path = images / f"{image_hash}.jpg"
    with open(file_path, 'wb') as f:
        f.write(image_data)
    # 读取现有的项目
    items = read_items_from_json()
    # 添加新项目到列表
    items.append({"name": name, "category": category, "image_name": f"{image_hash}.jpg"})
    # 写回到items.json文件
    with open('items.json', 'w') as file:
        json.dump({"items": items}, file)
    # 返回新添加的项目信息
    return {"name": name, "category": category, "image_name": f"{image_hash}.jpg"}

@app.post("/items")
def add_item(name: str = Form(...)):
    logger.info(f"Receive item: {name}")
    return {"message": f"item received: {name}"}



@app.get("/image/{image_name}")
async def get_image(image_name):
    # Create image path
    image = images / image_name

    if not image_name.endswith(".jpg"):
        raise HTTPException(status_code=400, detail="Image path does not end with .jpg")

    if not image.exists():
        logger.debug(f"Image not found: {image}")
        image = images / "default.jpg"

    return FileResponse(image)
