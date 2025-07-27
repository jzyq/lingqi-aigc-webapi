from fastapi import FastAPI, Response
import uvicorn

app = FastAPI()


@app.get("/hello")
async def hello() -> Response:
    return Response(content="hello world from admin.")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
