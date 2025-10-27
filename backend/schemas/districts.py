from typing import Optional, Annotated
from pydantic import BaseModel, StringConstraints

NameStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

class District(BaseModel):
    id: Optional[int] = None
    region_id: int
    name: NameStr
