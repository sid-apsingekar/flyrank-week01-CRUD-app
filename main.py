import os
import psycopg
from dotenv import load_dotenv
import sqlite3
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

load_dotenv()
DATABASE_URL = os.environ["DATABASE_URL"]

def get_connection():
    return psycopg.connect(DATABASE_URL)

def init_db():
    conn = get_connection()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT FALSE
        )
    """)
    count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    if count == 0:
        conn.execute("INSERT INTO tasks (title, done) VALUES (%s,%s)", ("Buy milk",False))
        conn.execute("INSERT INTO tasks (title, done) VALUES (%s,%s)", ("Walk the dog",False))
        conn.execute("INSERT INTO tasks (title, done) VALUES (%s,%s)", ("Finish assignment",False))
    conn.commit()
    conn.close()

app = FastAPI()
init_db()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid request body"}
    )




class TaskCreate(BaseModel):
    title: str


class TaskUpdate(BaseModel):
    title: str
    done: bool


tasks = [
    {
        "id": 1,
        "title": "Buy milk",
        "done": False
    },
    {
        "id": 2,
        "title": "Walk the dog",
        "done": False
    },
    {
        "id": 3,
        "title": "Finish assignment",
        "done": True
    }
]


@app.get("/",summary="API Information",description="Returns basic information about the Task API, including its version and available endpoints.")
def home():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }


@app.get("/health",summary="Health Check",description="Checks whether the API server is running and responding correctly.")
def health():
    return {
        "status": "ok"
    }


@app.get("/tasks",summary="List All Tasks",description="Returns the complete list of tasks currently stored in database .")
def list_tasks():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM tasks").fetchall()
    conn.close()
    return [{"id":r[0],"title":r[1],"done": r[2]} for r in rows]


@app.get("/tasks/{task_id}",summary="Get Task by ID",description="Retrieves a single task using its unique ID. Returns 404 if task does not exist.")
def get_task(task_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM tasks WHERE id = %s ",(task_id,)).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return {"id":row[0],"title":row[1],"done":row[2]}

    raise HTTPException(
        status_code=404,
        detail=f"Task {task_id} not found"
    )


@app.post("/tasks", status_code=201,summary="Create a New Task",description="Create a new task with the provided title. The task is assigned a unique ID and is marked as incomplete by default.")
def create_task(task: TaskCreate):

    if not task.title.strip():
        raise HTTPException(
            status_code=400,
            detail="Title is required"
        )

    conn = get_connection()
    row = conn.execute("INSERT INTO tasks (title,done) VALUES (%s,%s) RETURNING id, title,done",(task.title,False)).fetchone()
    conn.commit()
    conn.close()

    return {"id":row[0],"title":row[1],"done":row[2]}

@app.put("/tasks/{task_id}",summary="Update a Task",description="Updates an existing task's title and completion status. Returns 404 if the task does not exist.")
def update_task(task_id: int, task: TaskUpdate):

    if not task.title.strip():
        raise HTTPException(
            status_code=400,
            detail="Title is required"
        )

    conn = get_connection()
    row = conn.execute(
    "UPDATE tasks SET title=%s, done=%s WHERE id = %s RETURNING id, title, done",
    (task.title, task.done, task_id)
        ).fetchone()
    conn.commit()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return {"id": row[0], "title": row[1], "done": row[2]}


@app.delete("/tasks/{task_id}", status_code=204,summary="Delete a Task",description="Deletes a task by its ID. Returns 204 on successful deletion or 404 if the task is not found.")
def delete_task(task_id: int):

    conn = get_connection()
    row = conn.execute("DELETE FROM tasks WHERE id = %s RETURNING id",(task_id,)).fetchone()
    conn.commit()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail=f'Task {task_id} not found')

    return