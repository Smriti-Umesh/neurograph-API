from pydantic import BaseModel

# for the user who sends to create a network
class NetworkCreate(BaseModel):
    name: str

# API response
class NetworkResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}