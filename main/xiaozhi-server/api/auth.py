from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

security = HTTPBearer(auto_error=False)


async def verify_api_key(
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
):
    """
    验证 API Key

    通过 Authorization: Bearer <api_key> 头传递
    或在查询参数中传递 ?api_key=<api_key>
    """
    api_key = request.app.state.config["server"].get("auth_key", "")

    if not api_key:
        return

    api_key_from_header = credentials.credentials if credentials else None
    api_key_from_query = request.query_params.get("api_key")
    provided_key = api_key_from_header or api_key_from_query

    if not provided_key or provided_key != api_key:
        raise HTTPException(
            status_code=401,
            detail="无效的 API Key，请在 Authorization 头或 api_key 参数中提供正确的密钥",
            headers={"WWW-Authenticate": "Bearer"},
        )