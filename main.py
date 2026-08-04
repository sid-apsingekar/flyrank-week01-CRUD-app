import sqlite3
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel


def get_connection():
    return sqlite3.connect("tasks.db")

def init_db():
    conn = get_connection()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS tasks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0)
    """)
    count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    if count == 0:
        conn.execute("INSERT INTO tasks (title, done) VALUES (?,?)", ("Buy milk",0))
        conn.execute("INSERT INTO tasks (title, done) VALUES (?,?)", ("Walk the dog",0))
        conn.execute("INSERT INTO tasks (title, done) VALUES (?,?)", ("Finish assignment",1))
    conn.commit()
    conn.commit()

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
    return [{"id":r[0],"title":r[1],"done": bool(r[2])} for r in rows]


@app.get("/tasks/{task_id}",summary="Get Task by ID",description="Retrieves a single task using its unique ID. Returns 404 if task does not exist.")
def get_task(task_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM tasks WHERE id = ? ",(task_id,)).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return {"id":row[0],"title":row[1],"done":bool(row[2])}

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
    cursor = conn.execute("INSERT INTO tasks (title,done) VALUES (?,?)",(task.title,0))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return {"id":new_id,"title":task.title,"done":False}

@app.put("/tasks/{task_id}",summary="Update a Task",description="Updates an existing task's title and completion status. Returns 404 if the task does not exist.")
def update_task(task_id: int, task: TaskUpdate):

    if not task.title.strip():
        raise HTTPException(
            status_code=400,
            detail="Title is required"
        )

    conn = get_connection()
    cursor = conn.execute(
        "UPDATE tasks SET title=?, done=? WHERE id = ?",(task.title,int(task.done),task_id)
    )
    conn.commit()
    if cursor.rowcount==0:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Task{task_id} not found")
    conn.close()
    return{"id":task_id,"title":task.title,"done":task.done}


@app.delete("/tasks/{task_id}", status_code=204,summary="Delete a Task",description="Deletes a task by its ID. Returns 204 on successful deletion or 404 if the task is not found.")
def delete_task(task_id: int):

    conn = get_connection()
    cursor = conn.execute("DELETE FROM tasks WHERE id = ?",(task_id,))
    conn.commit()
    conn.close()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail=f'Task {task_id} not found')

    return