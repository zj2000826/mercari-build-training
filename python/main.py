import os
import logging
import pathlib
from fastapi import FastAPI, Form, HTTPException, File, UploadFile, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import hashlib
import json
import sqlite3

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

    conn = sqlite3.connect('mercari.sqlite3')
    cur = conn.cursor()

    cur.execute("SELECT id FROM categories WHERE name = ?", (category,))
    category_content = cur.fetchone()

    if not category_content:
        cur.execute("INSERT INTO categories (name) VALUES (?)", (category,))
        conn.commit()  
        category_id = cur.lastrowid  
    else:
        category_id = category[0]

    cur.execute("INSERT INTO items (name, category_id, image) VALUES (?, ?, ?)",
                (name, category_id, image_filename))
    conn.commit()
    conn.close()

    return {"name": name, "category": category, "image_name": image_filename}


@app.get("/items")
def get_items():
    conn = sqlite3.connect('mercari.sqlite3')
    cur = conn.cursor()

    cur.execute("""SELECT items.id, items.name, categories.name AS category_name, items.image
                   FROM items
                   JOIN categories ON items.category_id = categories.id""")
    items = cur.fetchall()
    conn.close()

    items_list = [{"id": item[0], "name": item[1], "category": item[2], "image_name": item[3]} for item in items]

    return {"items": items_list}


@app.get("/items/{item_id}")
def get_item(item_id: int):
    conn = sqlite3.connect('mercari.sqlite3')
    cur = conn.cursor()

    cur.execute("""SELECT items.id, items.name, categories.name, items.image
                   FROM items
                   INNER JOIN categories ON items.category_id = categories.id
                   WHERE items.id = ?""", (item_id,))
    item = cur.fetchone()

    conn.close()
    
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"id": item[0], "name": item[1], "category": item[2], "image_name": item[3]}


@app.get("/search")
def search_items(keyword: str = Query(None)):
    conn = sqlite3.connect('mercari.sqlite3')
    cur = conn.cursor()

    cur.execute("""SELECT items.id, items.name, categories.name, items.image
                   FROM items
                   JOIN categories ON items.category_id = categories.id
                   WHERE items.name LIKE ?""", (f"%{keyword}%",))

    items = cur.fetchall()
    conn.close()

    if items:
        items_list = [{"id": item[0], "name": item[1], "category": item[2], "image_name": item[3]} for item in items]
        return {"items": items_list}
    else:
        raise HTTPException(status_code=404, detail="No items found with that keyword")


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
