from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()


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


@app.get("/health",summary="Health Check",description="Checks whether the API sever is running and respondign correctly.")
def health():
    return {
        "status": "ok"
    }


@app.get("/tasks",summary="List All Tasks",description="Returns the complete list of tasks currently stored in memory.")
def list_tasks():
    return tasks


@app.get("/tasks/{task_id}",summary="Get Task by ID",description="Retrieves a single task using its unique ID. Returns 404 if task does not exist.")
def get_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task

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

    new_id = max((t["id"] for t in tasks), default=0) + 1

    new_task = {
        "id": new_id,
        "title": task.title,
        "done": False
    }

    tasks.append(new_task)

    return new_task


@app.put("/tasks/{task_id}",summary="Update a Task",description="Updates an existing task's title and completion status. Returns 404 if the task does not exist.")
def update_task(task_id: int, task: TaskUpdate):

    if not task.title.strip():
        raise HTTPException(
            status_code=400,
            detail="Title is required"
        )

    for t in tasks:
        if t["id"] == task_id:
            t["title"] = task.title
            t["done"] = task.done
            return t

    raise HTTPException(
        status_code=404,
        detail=f"Task {task_id} not found"
    )


@app.delete("/tasks/{task_id}", status_code=204,summary="Delete a Task",description="Deletes a task by its ID. Returns 204 on successful deletion or 404 if the task is not found.")
def delete_task(task_id: int):

    for index, task in enumerate(tasks):
        if task["id"] == task_id:
            tasks.pop(index)
            return

    raise HTTPException(
        status_code=404,
        detail=f"Task {task_id} not found"
    )