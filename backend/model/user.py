import uuid

import attrs


@attrs.define(frozen=True, kw_only=True)
class User:
    user_id: uuid.UUID
    username: str = attrs.field(default="")
    avatar: str = attrs.field(default="")