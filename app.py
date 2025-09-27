# app.py
from fastapi import FastAPI
from sqlmodel import SQLModel

from config import engine
from Controller.UserController import router as user_router
from Controller.ProblemController import router as problem_router




def create_db_and_tables():
    """初始化数据库表"""
    SQLModel.metadata.create_all(engine)


def create_app() -> FastAPI:
    app = FastAPI(title="Online Judge API", version="1.0.0")

    # 注册路由
    app.include_router(user_router, prefix="/users", tags=["User"])
    app.include_router(problem_router, prefix="/problems", tags=["Problem"])


    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    create_db_and_tables()
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
