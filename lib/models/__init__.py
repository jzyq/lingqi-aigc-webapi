from pymongo.asynchronous.database import AsyncDatabase
from . import inferences
from . import logs


async def init(db: AsyncDatabase) -> None:
    from beanie import init_beanie

    await init_beanie(
        db,
        document_models=[
            inferences.Inference,
            inferences.StandardTask,
            inferences.CompositeTask,
            logs.Logs,
        ],
    )
