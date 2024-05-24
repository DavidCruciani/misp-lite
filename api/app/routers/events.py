from typing import Optional

from app.auth.auth import get_current_active_user
from app.dependencies import get_db, get_opensearch_client
from app.repositories import events as events_repository
from app.repositories import tags as tags_repository
from app.schemas import event as event_schemas
from app.schemas import user as user_schemas
from fastapi import APIRouter, Depends, HTTPException, Response, Security
from fastapi_pagination import Page
from sqlalchemy.orm import Session
from starlette import status

router = APIRouter()


async def get_events_parameters(
    info: Optional[str] = None,
    deleted: Optional[bool] = None,
):
    return {"info": info, "deleted": deleted}


@router.get("/events/", response_model=Page[event_schemas.Event])
async def get_events(
    params: dict = Depends(get_events_parameters),
    db: Session = Depends(get_db),
    user: user_schemas.User = Security(get_current_active_user, scopes=["events:read"]),
):
    return events_repository.get_events(db, params["info"], params["deleted"])


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


@router.post(
    "/events/", response_model=event_schemas.Event, status_code=status.HTTP_201_CREATED
)
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An event with this info already exists",
        )
    event.user_id = user.id
    event.org_id = user.org_id
    db_event = events_repository.create_event(db=db, event=event)

    event = event_schemas.Event.model_validate(db_event)

    # push event to OpenSearch
    # TODO: move this to a background task
    OpenSearchClient = get_opensearch_client()

    response = OpenSearchClient.index(
        index="misp-events", id=event.uuid, body=event.model_dump()
    )

    if response["result"] not in ["created", "updated"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=response
        )

    return event


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


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    user: user_schemas.User = Security(
        get_current_active_user, scopes=["events:delete"]
    ),
):
    return events_repository.delete_event(db=db, event_id=event_id)


@router.post(
    "/events/{event_id}/tag/{tag_id}",
    status_code=status.HTTP_201_CREATED,
)
def tag_event(
    event_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    user: user_schemas.User = Security(
        get_current_active_user, scopes=["events:update"]
    ),
):
    event = events_repository.get_event_by_id(db, event_id=event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )

    tag = tags_repository.get_tag_by_id(db, tag_id=tag_id)
    if tag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
        )

    tags_repository.tag_event(db=db, event=event, tag=tag)

    return Response(status_code=status.HTTP_201_CREATED)
