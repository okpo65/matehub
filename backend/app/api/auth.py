from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from app.database.connection import get_db
from app.database.models import User
from app.api.jwt_auth import (
    create_tokens_for_user,
    create_access_token_for_user,
    get_current_user_optional,
    get_current_user_required
)
from app.api.jwt_auth import REFRESH_TOKEN_EXPIRE_DAYS
from datetime import timedelta
from typing import Optional


router = APIRouter(prefix="/auth", tags=["authentication"])


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str = None
    token_type: str
    user_type: str  # "anonymous" or "authenticated"
    user_id: int = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    kakao_id: Optional[int] = None
    is_anonymous: bool


@router.post("/anonymous-token", response_model=TokenResponse)
async def create_anonymous_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """익명 사용자용 JWT 토큰 발급"""
    user = db.query(User).filter(
        User.refresh_token == request.refresh_token,
        User.refresh_token_expires_at > datetime.utcnow()
    ).first()

    if not user:
        user = User(
            is_anonymous=True,
            is_active=True
        )
        tokens = create_tokens_for_user(user.id, is_anonymous=True)
        user.refresh_token = tokens["refresh_token"]
        user.refresh_token_expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        tokens = create_tokens_for_user(user.id, is_anonymous=True)
        user.refresh_token = tokens["refresh_token"]
        user.refresh_token_expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        db.commit()
        db.refresh(user)

    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type="bearer",
        user_type="anonymous",
        user_id=user.id
    )


# @router.post("/kakao-token", response_model=TokenResponse)
# async def create_kakao_user_token(
#     request: KakaoTokenRequest,
#     db: Session = Depends(get_db)
# ):
#     """카카오 로그인 후 JWT 토큰 발급 (사용자 생성 또는 업데이트)"""
#     # 기존 사용자 확인
#     user = db.query(User).filter(User.kakao_id == request.kakao_id).first()
#     if user:
#         tokens = create_tokens_for_user(user.id, is_anonymous=False)
#         # 기존 사용자 정보 업데이트
#         user.is_anonymous = False
#         user.refresh_token = tokens["refresh_token"]
#         user.refresh_token_expires_at = datetime.utcnow() + timedelta(days=30)
#         db.commit()
#         db.refresh(user)
#     else:
#         # 새 사용자 생성
#         user = User(
#             kakao_id=request.kakao_id,
#             is_anonymous=False,
#             is_active=True
#         )
#         tokens = create_tokens_for_user(user.id, is_anonymous=False)
#         user.refresh_token = tokens["refresh_token"]
#         user.refresh_token_expires_at = datetime.utcnow() + timedelta(days=30)
#         db.add(user)
#         db.commit()
#         db.refresh(user)
    
#     return TokenResponse(
#         access_token=tokens["access_token"],
#         refresh_token=tokens["refresh_token"],
#         token_type="bearer",
#         user_type="authenticated",
#         user_id=user.id
#     )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """refresh_token으로 새로운 access_token 발급"""
    user = db.query(User).filter(
        User.refresh_token == request.refresh_token,
        User.refresh_token_expires_at > datetime.utcnow()
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # 새로운 토큰 생성
    access_token = create_access_token_for_user(user.id)

    user.refresh_token_expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    db.commit()
    db.refresh(user)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=user.refresh_token,
        token_type="bearer",
        user_type="authenticated",
        user_id=user.id
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user_id: int = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """현재 인증된 사용자 정보 조회"""
    print(f"User ID in me: {user_id}")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    print("User: ", user.id, user.kakao_id)
    kakao_id = user.kakao_id if user.kakao_id else None
    return UserResponse(
        kakao_id=kakao_id,
        is_anonymous=user.is_anonymous
    )

@router.get("/validate")
async def validate_token(
    user_id: int = Depends(get_current_user_optional)
):
    """토큰 유효성 검증"""
    if user_id:
        return {
            "valid": True,
            "user_id": user_id,
        }
    else:
        return {
            "valid": False,
        }
