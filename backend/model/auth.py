import datetime
import uuid

import attrs
from pydantic import EmailStr


@attrs.define(frozen=True, kw_only=True)
class Auth:
    id: uuid.UUID = attrs.field(default=uuid.uuid4)
    user_id: uuid.UUID
    password: str = attrs.field(repr=False)  # will be hashed
    email: EmailStr
    is_verified: bool = attrs.field(default=False)

    failed_attempts: int = attrs.field(default=0)
    locked_until: datetime.datetime | None = attrs.field(default=None)

    created_at: datetime.datetime = attrs.field(
        factory=lambda: datetime.datetime.now(datetime.UTC),
    )
    updated_at: datetime.datetime = attrs.field(
        factory=lambda: datetime.datetime.now(datetime.UTC),
    )
