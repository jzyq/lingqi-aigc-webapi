async def init(source: str) -> None:
    import pymongo
    import models

    client = pymongo.AsyncMongoClient(source)
    await models.init(client.aigc)
