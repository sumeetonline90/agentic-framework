from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="Agentic Framework API", version="0.1.0")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()


