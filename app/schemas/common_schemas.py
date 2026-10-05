from typing import Generic, TypeVar, Optional, Any, Dict
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")

class APIErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None

class APIResponse(BaseModel, Generic[DataT]):
    success: bool = True
    data: Optional[DataT] = None
    error: Optional[APIErrorDetail] = None

def success_response(data: Any = None) -> Dict[str, Any]:
    return {
        "success": True,
        "data": data,
    }

def error_response(code: str, message: str, details: Optional[Any] = None) -> Dict[str, Any]:
    resp: Dict[str, Any] = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        },
    }
    if details:
        resp["error"]["details"] = details
    return resp
