from typing import Optional

from app.auth.auth import get_current_active_user
from app.dependencies import get_db
from app.repositories import events as events_repository
from app.schemas import event as event_schemas
from app.schemas import user as user_schemas
from fastapi import APIRouter, Depends, HTTPException, Security, status
from sqlalchemy.orm import Session

router = APIRouter()


async def get_events_parameters(
    skip: int = 0,
    limit: int = 100,
    id: Optional[int] = None,
    info: Optional[str] = None,
):
    return {"skip": skip, "limit": limit, "filters": {"id": id, "info": info}}


@router.get("/events/", response_model=list[event_schemas.Event])
async def get_events(
    params: dict = Depends(get_events_parameters),
    db: Session = Depends(get_db),
    user: user_schemas.User = Security(get_current_active_user, scopes=["events:read"]),
):
    return events_repository.get_events(
        db, params["skip"], params["limit"], params["filters"]
    )


@router.get("/events/{event_id}", response_model=event_schemas.Event)
def get_event_by_id(
    event_id: int,
    db: Session = Depends(get_db),
    user: user_schemas.User = Security(get_current_active_user, scopes=["events:read"]),
):
    db_event = events_repository.get_event_by_id(db, event_id=event_id)
    if db_event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )
    return db_event


@router.post("/events/", response_model=event_schemas.Event, status_code=201)
def create_event(
    event: event_schemas.EventCreate,
    db: Session = Depends(get_db),
    user: user_schemas.User = Security(
        get_current_active_user, scopes=["events:create"]
    ),
):
    db_event = events_repository.get_user_by_info(db, info=event.info)
    if db_event:
        raise HTTPException(
            status_code=400, detail="An event with this info already exists"
        )
    return events_repository.create_event(db=db, event=event)


@router.patch("/events/{event_id}", response_model=event_schemas.Event)
def update_event(
    event_id: int,
    event: event_schemas.EventUpdate,
    db: Session = Depends(get_db),
    user: user_schemas.User = Security(
        get_current_active_user, scopes=["events:update"]
    ),
):
    return events_repository.update_event(db=db, event_id=event_id, event=event)
