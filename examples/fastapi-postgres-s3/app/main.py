"""Simple Todo API with FastAPI and PostgreSQL."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncpg

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is required")


class TodoCreate(BaseModel):
    title: str
    completed: bool = False


class Todo(BaseModel):
    id: int
    title: str
    completed: bool


pool: asyncpg.Pool | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)

    # Create table if not exists
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                completed BOOLEAN DEFAULT FALSE
            )
        """)

    yield

    await pool.close()


app = FastAPI(
    title="Todo API",
    description="Simple Todo API demonstrating NestVault backups",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return {"message": "Todo API - PostgreSQL backed up by NestVault"}


@app.get("/todos", response_model=list[Todo])
async def list_todos():
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, title, completed FROM todos ORDER BY id")
        return [dict(row) for row in rows]


@app.post("/todos", response_model=Todo)
async def create_todo(todo: TodoCreate):
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO todos (title, completed) VALUES ($1, $2) RETURNING id, title, completed",
            todo.title,
            todo.completed,
        )
        return dict(row)


@app.get("/todos/{todo_id}", response_model=Todo)
async def get_todo(todo_id: int):
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, title, completed FROM todos WHERE id = $1", todo_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="Todo not found")
        return dict(row)


@app.put("/todos/{todo_id}", response_model=Todo)
async def update_todo(todo_id: int, todo: TodoCreate):
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "UPDATE todos SET title = $1, completed = $2 WHERE id = $3 RETURNING id, title, completed",
            todo.title,
            todo.completed,
            todo_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Todo not found")
        return dict(row)


@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: int):
    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM todos WHERE id = $1", todo_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Todo not found")
        return {"message": "Todo deleted"}


@app.get("/health")
async def health():
    try:
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}
