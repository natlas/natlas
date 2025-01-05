from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app import db
from app.models.dict_serializable import DictSerializable


# Simple tags that can be added to scope items for automatic tagging
class Tag(db.Model, DictSerializable):  # type: ignore[misc, name-defined]
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), index=True, unique=True)

    @staticmethod
    def create_if_none(tag: str) -> "Tag":
        """If tag exists, return it. If not, create it and return it."""
        tag = tag.strip()
        existingTag = Tag.query.filter_by(name=tag).first()
        if not existingTag:
            newTag = Tag(name=tag)
            db.session.add(newTag)
            return newTag
        return existingTag  # type: ignore[no-any-return]
