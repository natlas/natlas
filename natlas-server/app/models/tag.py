from app import db
from app.models.dict_serializable import DictSerializable


# Simple tags that can be added to scope items for automatic tagging
class Tag(db.Model, DictSerializable):  # type: ignore[misc, name-defined]
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True, unique=True, nullable=False)

    @staticmethod
    def create_if_none(tag):  # type: ignore[no-untyped-def]
        """If tag exists, return it. If not, create it and return it."""
        tag = tag.strip()
        existingTag = Tag.query.filter_by(name=tag).first()
        if not existingTag:
            newTag = Tag(name=tag)
            db.session.add(newTag)
            return newTag
        return existingTag
