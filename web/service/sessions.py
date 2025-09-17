from dataio.sessions import Session


async def create_new_session(uid: int, nickname: str) -> str:
    ses = await Session.new(uid, nickname)
    return ses.token


async def get_session_or_none(token: str) -> Session | None:
    ses = await Session.get(token)
    return ses


async def delete_session(token: str):
    ses = await Session.get(token)
    if ses:
        await ses.delete()


async def refresh_session(token: str):
    ses = await Session.get(token)
    if not ses:
        return
    await ses.refresh()


async def find_session_by_uid(uid: int) -> tuple[str, Session] | None:
    ses = await Session.find_by_uid(uid)
    if not ses:
        return ses
    return (ses.token, ses)
