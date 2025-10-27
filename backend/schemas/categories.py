from typing import Optional, Annotated
from pydantic import BaseModel, StringConstraints

NameStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

class Category(BaseModel):
    id: Optional[int] = None
    name: NameStr
    description: Optional[str] = None
