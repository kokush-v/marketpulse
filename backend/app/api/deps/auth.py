from dataclasses import dataclass

from fastapi import Header, HTTPException, status


@dataclass(frozen=True)
class AuthenticatedUser:
    bearer_token: str


def require_authenticated_user(
    authorization: str | None = Header(default=None),
) -> AuthenticatedUser:
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthorized", "message": "Authentication is required."},
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthorized", "message": "A bearer token is required."},
        )

    return AuthenticatedUser(bearer_token=token.strip())
