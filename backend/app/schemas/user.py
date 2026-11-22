from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=8, max_length=72)
    # Roll number for students, or institutional identifier
    roll_number: str | None = Field(default=None, max_length=50)
    institutional_id: str | None = Field(default=None, max_length=50)
    # Optional direct email; if not provided, derived automatically from roll number
    email: EmailStr | None = None
    phone_number: str | None = Field(default=None, max_length=20)


class UserLogin(BaseModel):
    # Allows logging in with either Roll Number / Employee ID OR Email address
    identifier: str | None = None
    email: str | None = None
    password: str


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    institutional_id: str | None = None
    role: str
    is_active: bool
    phone_number: str | None = None
    department_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse | None = None
