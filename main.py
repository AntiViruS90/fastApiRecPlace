from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.api import user
from app.api import movie
from app.db.session import create_db_and_tables
import uvicorn

# Инициализация FastAPI
app = FastAPI(title="Movie Favorite API")


# Настройка CORS, если приложение будет доступно из разных источников
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Можно ограничить список разрешённых источников
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router, tags=["users"])
app.include_router(movie.router, tags=["movies"])


# Миграции базы данных при старте приложения (если необходимо)
@app.on_event("startup")
async def on_startup():
    # Создание базы данных и таблиц (если они ещё не созданы)
    await create_db_and_tables()


# Указываем способ работы с базой данных для маршрутов (если это необходимо)
@app.on_event("shutdown")
async def shutdown():
    # Код для корректного завершения работы приложения
    pass


# Запуск приложения с uvicorn (если запускаете приложение через команду `python main.py`)
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
