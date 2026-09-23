import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=12, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        # Runs before EmailStr's own syntax validation, so a value with
        # surrounding whitespace or mixed case is validated in its
        # canonical, persisted form.
        if isinstance(value, str):
            return value.strip().lower()
        return value


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    created_at: datetime


class RegisterResponse(BaseModel):
    data: UserPublic
