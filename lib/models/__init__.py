from pymongo.asynchronous.database import AsyncDatabase
from . import inferences
import gridfs

__fs: gridfs.AsyncGridFS | None = None


async def init(db: AsyncDatabase) -> None:
    from beanie import init_beanie

    await init_beanie(
        db,
        document_models=[
            inferences.Inference,
            inferences.StandardTask,
            inferences.CompositeTask,
        ],
    )

    # Init grid fs.
    global __fs
    __fs = gridfs.AsyncGridFS(db)


def get_gridfs() -> gridfs.AsyncGridFS:
    if __fs:
        return __fs
    raise ValueError("fs must be init first")
