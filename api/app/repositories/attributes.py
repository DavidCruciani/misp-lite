import time

from app.models import attribute as attribute_models
from app.schemas import attribute as attribute_schemas
from app.schemas import event as event_schemas
from pymisp import MISPAttribute
from sqlalchemy.orm import Session


def get_attributes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(attribute_models.Attribute).offset(skip).limit(limit).all()


def get_attribute_by_id(db: Session, attribute_id: int):
    return (
        db.query(attribute_models.Attribute)
        .filter(attribute_models.Attribute.id == attribute_id)
        .first()
    )


def create_attribute(db: Session, attribute: attribute_schemas.AttributeCreate):
    # TODO: Attribute::beforeValidate() && Attribute::$validate
    db_attribute = attribute_models.Attribute(
        event_id=attribute.event_id,
        object_id=attribute.object_id,
        object_relation=attribute.object_relation,
        category=attribute.category,
        type=attribute.type,
        value=attribute.value,
        to_ids=attribute.to_ids,
        uuid=attribute.uuid,
        timestamp=attribute.timestamp or time.time(),
        distribution=attribute.distribution,
        sharing_group_id=attribute.sharing_group_id,
        comment=attribute.comment,
        deleted=attribute.deleted,
        disable_correlation=attribute.disable_correlation,
        first_seen=attribute.first_seen,
        last_seen=attribute.last_seen,
    )
    db.add(db_attribute)
    db.commit()
    db.refresh(db_attribute)

    return db_attribute


def create_attribute_from_pulled_attribute(
    db: Session, pulled_attribute: MISPAttribute, local_event_id: int
):
    # TODO: process sharing group // captureSG
    # TODO: enforce warninglist

    db_attribute = create_attribute(
        db,
        attribute_models.Attribute(
            event_id=local_event_id,
            category=pulled_attribute.category,
            type=pulled_attribute.type,
            value=pulled_attribute.value,
            to_ids=pulled_attribute.to_ids,
            uuid=pulled_attribute.uuid,
            timestamp=pulled_attribute.timestamp.timestamp(),
            distribution=event_schemas.DistributionLevel(pulled_attribute.distribution),
            comment=pulled_attribute.comment,
            sharing_group_id=pulled_attribute.sharing_group_id,
            deleted=pulled_attribute.deleted,
            disable_correlation=pulled_attribute.disable_correlation,
            object_id=pulled_attribute.object_id,
            object_relation=getattr(pulled_attribute, "object_relation", None),
            first_seen=pulled_attribute.first_seen.timestamp()
            if hasattr(pulled_attribute, "first_seen")
            else None,
            last_seen=pulled_attribute.last_seen.timestamp()
            if hasattr(pulled_attribute, "last_seen")
            else None,
        ),
    )

    # TODO: process attribute tags
    # TODO: process sigthings

    db.add(db_attribute)
    db.commit()
    db.refresh(db_attribute)

    return db_attribute
