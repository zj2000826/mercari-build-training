import os
import logging
import pathlib
from fastapi import FastAPI, Form, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import hashlib
import json

app = FastAPI()
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("uvicorn")

images = pathlib.Path(__file__).parent.resolve() / "images"
origins = [os.environ.get("FRONT_URL", "http://localhost:3000")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Hello, world!"}


@app.post("/items")
def add_item(name: str = Form(...), category: str = Form(...), image: UploadFile = File(...)):
    logger.info(f"Receive item: {name}, Category: {category}, Image: {image}")

    image_content = image.file.read()
    image_hash = hashlib.sha256(image_content).hexdigest()
    image_filename = f"{image_hash}.jpg"
    image_path = os.path.join('images', image_filename)
    with open(image_path, 'wb') as f:
        f.write(image_content)

    with open('items.json', 'r') as f:
        items_data = json.load(f)

    items_data['items'].append({'name': name, 'category': category, 'image': image_filename})

    with open('items.json', 'w') as f:
        json.dump(items_data, f, indent=4)

    return {"name": name, "category": category, "image_name": image_filename}

@app.get("/items/{item_id}")
def get_item(item_id: int):
    with open('items.json', 'r') as f:
        items = json.load(f)
    items = items.get("items", [])
    return items[item_id]


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
