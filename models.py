from sqlalchemy.orm import Mapped, mapped_column
from database import db

class Url(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    url:Mapped[str]
    shortened_url:Mapped[str]