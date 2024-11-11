from sqlalchemy.orm import Mapped, mapped_column
from database import db
from datetime import datetime
class Url(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    url:Mapped[str]
    shortened_url:Mapped[str]
    created: Mapped[datetime] = mapped_column(default=lambda: datetime.now())