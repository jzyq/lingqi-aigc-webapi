from . import make_app
import uvicorn
import dataio
import asyncio


async def main() -> None:
    await dataio.init("mongodb://localhost:27017/")

    conf = uvicorn.Config(app=make_app(), host="0.0.0.0")
    server = uvicorn.Server(conf)
    await server.serve()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
