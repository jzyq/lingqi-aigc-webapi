import asyncio
import dataio
import rpcclient
from fastapi import FastAPI
from web.service import api
from web import wxproxy
import uvicorn


async def main() -> None:
    await dataio.init("mongodb://localhost:27017/")
    await rpcclient.init("http://127.0.0.1:8000", prefix=rpcclient.Prefix())

    app = FastAPI()

    app.include_router(api.wx.router)

    app.mount("/wechat", wxproxy.make_app())

    srv_conf = uvicorn.Config(app, host="0.0.0.0")
    srv = uvicorn.Server(srv_conf)
    await srv.serve()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
