import os
import logging
import pathlib
from fastapi import FastAPI, HTTPException, Form, File, UploadFile, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import hashlib
import sqlite3

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

def get_db():
    conn = sqlite3.connect('mercari.sqlite3')
    try:
        yield conn
    finally:
        conn.close()

def initialize_database():
    try:
        conn = sqlite3.connect('mercari.sqlite3')
        cursor = conn.cursor()
        with open('items.json', 'r') as file:
            data = json.load(file)
            items = data['items']
        
        for item in items:
            cursor.execute("INSERT INTO items (name, category, image_name) VALUES (?, ?, ?)", 
                           (item['name'], item['category'], item.get('image_name', 'default.jpg')))

        conn.commit()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        conn.close()

@app.on_event("startup")
def on_startup():
    initialize_database()

@app.get("/search")
def search_items(keyword: str, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    query = "SELECT * FROM items WHERE name LIKE ?"
    cursor.execute(query, ('%' + keyword + '%',))
    items = cursor.fetchall()
    items_list = [{"name": item[1], "category": item[2]} for item in items]

    return {"items": items_list}

@app.get("/items")
def read_items(db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        SELECT i.id, i.name, c.name AS category_name, i.image_name
        FROM items AS i
        JOIN categories AS c ON i.category_id = c.id
    """)
    items = cursor.fetchall()
    result = [
        {"id": item[0], "name": item[1], "category": item[2], "image_name": item[3]}
        for item in items
    ]
    return {"items": result}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
