from app import db


# Simple tags that can be added to scope items for automatic tagging
class Tag(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String, index=True, unique=True, nullable=False)
