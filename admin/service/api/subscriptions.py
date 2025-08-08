from fastapi import APIRouter, Depends
from .. import depends, models
import database
from sqlalchemy import Engine, delete
from sqlmodel import Session, select
from loguru import logger
from pydantic import BaseModel


class DeletePlansRequest(BaseModel):
    ids: list[int]


router = APIRouter(prefix="/subscription", dependencies=[Depends(depends.get_session)])


@router.post("/plan")
async def add_new_plan(
    plan: database.subscription.SubscriptionPlans,
    engine: Engine = Depends(depends.get_db),
) -> models.APIResponse:

    with Session(engine) as ses:
        ses.add(plan)
        ses.commit()
        ses.refresh(plan)
        logger.info(f"add new subscription plan, id: {plan.id}")

    return models.APIResponse()


@router.get("/plan")
async def get_plans(engine: Engine = Depends(depends.get_db)) -> models.APIResponse:
    with Session(engine) as ses:
        plans = ses.exec(select(database.subscription.SubscriptionPlans)).all()
        return models.APIResponse(data=plans)


@router.delete("/plan")
async def delete_plans(
    req: DeletePlansRequest, engine: Engine = Depends(depends.get_db)
) -> models.APIResponse:
    with Session(engine) as ses:
        stmt = delete(database.subscription.SubscriptionPlans).where(
            database.subscription.SubscriptionPlans.id.in_(req.ids)  # type: ignore
        )
        ses.exec(stmt)  # type: ignore
        ses.commit()

    return models.APIResponse()


@router.post("/plan/{pid}/enable")
async def disenable_plan(
    pid: int, engine: Engine = Depends(depends.get_db)
) -> models.APIResponse:
    with Session(engine) as ses:
        plan = ses.get(database.subscription.SubscriptionPlans, pid)
        if plan:
            plan.enable = True
            ses.commit()

    return models.APIResponse()


@router.post("/plan/{pid}/disable")
async def enable_plan(
    pid: int, engine: Engine = Depends(depends.get_db)
) -> models.APIResponse:
    with Session(engine) as ses:
        plan = ses.get(database.subscription.SubscriptionPlans, pid)
        if plan:
            plan.enable = False
            ses.commit()

    return models.APIResponse()
