from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str = Field(min_length=6, max_length=128)


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    username: str

    model_config = {"from_attributes": True}