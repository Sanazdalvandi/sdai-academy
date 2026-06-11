from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import sqlite3, hashlib, jwt, datetime

app = FastAPI(title="SDAI Academy API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = "sdai-secret-2024"
ADMIN_USER = "sanaz"
ADMIN_PASS = hashlib.sha256("admin1234".encode()).hexdigest()
DB = "portfolio.db"
security = HTTPBearer()

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        type TEXT,
        tags TEXT,
        link TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT,
        category TEXT,
        date TEXT,
        link TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        message TEXT,
        read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("SELECT COUNT(*) FROM projects")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO projects (title,description,type,tags) VALUES (?,?,?,?)", [
            ("Dental Caries Detection with YOLOv8", "Bitewing X-ray analysis system", "Medical AI", "YOLOv8,PyTorch,CLAHE,X-ray"),
            ("SDAI Course Advisor Widget", "Bilingual React+Vite widget", "Education AI", "React,Vite,Persian,Offline"),
            ("Medical Image Processing", "CLAHE and augmentation pipeline", "Computer Vision", "OpenCV,Augmentation,Pipeline"),
            ("Industrial AI Projects", "Machine vision detection systems", "Industrial AI", "Detection,FastAPI,Gradio"),
        ])
    c.execute("SELECT COUNT(*) FROM articles")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO articles (title,category,date) VALUES (?,?,?)", [
            ("YOLOv8 for Dental Lesion Detection", "Medical AI", "1403"),
            ("CLAHE Guide for Medical Images", "Computer Vision", "1403"),
            ("Building AI Widgets with React+Vite", "Development", "1402"),
        ])
    conn.commit()
    conn.close()

init_db()

class LoginData(BaseModel):
    username: str
    password: str

def verify_token(creds: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(creds.credentials, SECRET_KEY, algorithms=["HS256"])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/api/login")
def login(data: LoginData):
    hashed = hashlib.sha256(data.password.encode()).hexdigest()
    if data.username != ADMIN_USER or hashed != ADMIN_PASS:
        raise HTTPException(status_code=401, detail="Wrong credentials")
    token = jwt.encode({
        "sub": data.username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }, SECRET_KEY, algorithm="HS256")
    return {"token": token}

class ProjectIn(BaseModel):
    title: str
    description: Optional[str] = ""
    type: Optional[str] = ""
    tags: Optional[str] = ""
    link: Optional[str] = ""

@app.get("/api/projects")
def get_projects():
    conn = get_db()
    rows = conn.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/projects")
def add_project(p: ProjectIn, _=Depends(verify_token)):
    conn = get_db()
    conn.execute("INSERT INTO projects (title,description,type,tags,link) VALUES (?,?,?,?,?)",
                 (p.title, p.description, p.type, p.tags, p.link))
    conn.commit(); conn.close()
    return {"ok": True}

@app.put("/api/projects/{pid}")
def update_project(pid: int, p: ProjectIn, _=Depends(verify_token)):
    conn = get_db()
    conn.execute("UPDATE projects SET title=?,description=?,type=?,tags=?,link=? WHERE id=?",
                 (p.title, p.description, p.type, p.tags, p.link, pid))
    conn.commit(); conn.close()
    return {"ok": True}

@app.delete("/api/projects/{pid}")
def delete_project(pid: int, _=Depends(verify_token)):
    conn = get_db()
    conn.execute("DELETE FROM projects WHERE id=?", (pid,))
    conn.commit(); conn.close()
    return {"ok": True}

class ArticleIn(BaseModel):
    title: str
    content: Optional[str] = ""
    category: Optional[str] = ""
    date: Optional[str] = ""
    link: Optional[str] = ""

@app.get("/api/articles")
def get_articles():
    conn = get_db()
    rows = conn.execute("SELECT * FROM articles ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/articles")
def add_article(a: ArticleIn, _=Depends(verify_token)):
    conn = get_db()
    conn.execute("INSERT INTO articles (title,content,category,date,link) VALUES (?,?,?,?,?)",
                 (a.title, a.content, a.category, a.date, a.link))
    conn.commit(); conn.close()
    return {"ok": True}

@app.put("/api/articles/{aid}")
def update_article(aid: int, a: ArticleIn, _=Depends(verify_token)):
    conn = get_db()
    conn.execute("UPDATE articles SET title=?,content=?,category=?,date=?,link=? WHERE id=?",
                 (a.title, a.content, a.category, a.date, a.link, aid))
    conn.commit(); conn.close()
    return {"ok": True}

@app.delete("/api/articles/{aid}")
def delete_article(aid: int, _=Depends(verify_token)):
    conn = get_db()
    conn.execute("DELETE FROM articles WHERE id=?", (aid,))
    conn.commit(); conn.close()
    return {"ok": True}

class MessageIn(BaseModel):
    name: str
    email: str
    message: str

@app.post("/api/contact")
def send_message(m: MessageIn):
    conn = get_db()
    conn.execute("INSERT INTO messages (name,email,message) VALUES (?,?,?)",
                 (m.name, m.email, m.message))
    conn.commit(); conn.close()
    return {"ok": True}

@app.get("/api/messages")
def get_messages(_=Depends(verify_token)):
    conn = get_db()
    rows = conn.execute("SELECT * FROM messages ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.put("/api/messages/{mid}/read")
def mark_read(mid: int, _=Depends(verify_token)):
    conn = get_db()
    conn.execute("UPDATE messages SET read=1 WHERE id=?", (mid,))
    conn.commit(); conn.close()
    return {"ok": True}