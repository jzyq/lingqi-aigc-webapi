import gridfs
from beanie import PydanticObjectId
from pymongo.asynchronous.database import AsyncDatabase
from typing import BinaryIO, AsyncIterator, Any
from contextlib import asynccontextmanager


__fs: gridfs.AsyncGridFS | None = None


async def init(db: AsyncDatabase) -> None:
    global __fs
    __fs = gridfs.AsyncGridFS(db)


def is_inited() -> bool:
    if __fs:
        return True
    else:
        return False


class OssWriter:

    def __init__(self, _in: gridfs.AsyncGridIn):
        self.__in = _in

    @property
    def file_id(self) -> str:
        return str(self.__in._id)

    async def write(self, content: BinaryIO):
        await self.__in.write(content)

    async def write_bytes(self, content: bytes):
        await self.__in.write(content)


class OssReader:

    def __init__(self, _out: gridfs.AsyncGridOut) -> None:
        self.__out = _out

    @property
    def length(self) -> int:
        return self.__out.length

    @property
    def content_type(self) -> str:
        return self.__out.content_type if self.__out.content_type else ""

    @property
    def filename(self) -> str:
        return self.__out.filename

    async def read(self, size: int = -1) -> bytes:
        return await self.__out.read(size)

    def __aiter__(self) -> Any:
        return self.__out


@asynccontextmanager
async def save_file(filename: str, content_type: str) -> AsyncIterator[OssWriter]:
    if not __fs:
        raise ValueError("must init oss first")

    async with __fs.new_file() as writer:
        try:
            yield OssWriter(writer)
        finally:
            writer.content_type = content_type
            await writer.set("filename", filename)


@asynccontextmanager
async def load_file(fid: str) -> AsyncIterator[OssReader]:
    if not __fs:
        raise ValueError("must init oss first")

    fp = await __fs.get(PydanticObjectId(fid))
    try:
        yield OssReader(fp)
    finally:
        await fp.close()
