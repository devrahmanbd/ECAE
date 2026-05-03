from pydantic import BaseModel
from typing import Optional, Dict

class StoreRequest(BaseModel):
    text: str
    metadata: Optional[Dict] = None

class SearchResponse(BaseModel):
    text: str
    metadata: Dict

class ExecuteRequest(BaseModel):
    command: str
    image: Optional[str] = None
    workdir: Optional[str] = "."
