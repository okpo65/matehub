from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from datetime import datetime
from urllib.parse import quote
from app.database.connection import get_db
from app.database.models import User
from app.login.kakao import kakao_oauth
from app.config import settings
import logging
import os
from app.api.jwt_auth import create_tokens_for_user, get_current_user_required
from app.api.jwt_auth import REFRESH_TOKEN_EXPIRE_DAYS
from datetime import timedelta
from app.api.auth import RefreshTokenRequest
from app.profile.services import UserService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/kakao/login")
async def kakao_login():
    """카카오 로그인 URL 반환"""
    try:
        auth_url = kakao_oauth.get_authorization_url()
        return {"auth_url": auth_url}
    except Exception as e:
        logger.error(f"카카오 로그인 URL 생성 실패: {e}")
        raise HTTPException(status_code=500, detail="로그인 URL 생성에 실패했습니다")

@router.get("/kakao/callback/page")
async def kakao_callback_page():
    """카카오 콜백 처리 페이지 반환"""
    try:
        # Get the directory where this file is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        callback_html_path = os.path.join(current_dir, "callback.html")
        
        with open(callback_html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        return HTMLResponse(content=html_content, status_code=200)
    except Exception as e:
        logger.error(f"콜백 페이지 로드 실패: {e}")
        return HTMLResponse(
            content="<html><body><h1>Error loading callback page</h1></body></html>",
            status_code=500
        )

@router.get("/kakao/callback")
async def kakao_callback(
    code: str = Query(..., description="카카오에서 받은 인증 코드"),
    state: str = Query(None, description="상태 값"),
    db: Session = Depends(get_db)
):
    """카카오 로그인 콜백 처리 - JSON 응답"""
    try:
        logger.info(f"카카오 콜백 시작 - 인증 코드: {code[:10]}...")
        
        # 1. 인증 코드로 토큰들 획득
        token_data = await kakao_oauth.get_tokens(code)
        if not token_data:
            logger.error("토큰 획득 실패")
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "token_failed",
                    "message": "토큰 획득에 실패했습니다"
                }
            )
        
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_at = token_data.get("expires_at")
        if not access_token:
            logger.error("액세스 토큰이 없음")
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "no_access_token",
                    "message": "액세스 토큰을 받지 못했습니다"
                }
            )
        
        # 2. 액세스 토큰으로 사용자 정보 획득
        logger.info(f"액세스 토큰: {access_token}")
        user_info = await kakao_oauth.get_user_info(access_token)
        if not user_info:
            logger.error("사용자 정보 획득 실패")
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "user_info_failed",
                    "message": "사용자 정보 획득에 실패했습니다"
                }
            )
        
        # 3. 사용자 정보 파싱 - kakao_id만 사용
        kakao_id = str(user_info.get("id"))
        
        # 4. 데이터베이스에서 사용자 확인 또는 생성
        user = db.query(User).filter(User.kakao_id == kakao_id).first()
        is_new_user = False
        
        if not user:
            user_service = UserService(db)
            user = user_service.create_user(
                kakao_id=kakao_id,
                kakao_access_token=access_token,
                kakao_refresh_token=refresh_token,
                kakao_token_expires_at=expires_at,
                is_anonymous=False
            )
            # 새 사용자 생성 - 최소한의 정보만 저장

            db.add(user)
            db.commit()
            db.refresh(user)
            is_new_user = True
            logger.info(f"새 사용자 생성: kakao_id={kakao_id} (DB ID: {user.id})")
        else:
            # 기존 사용자 토큰만 업데이트
            user.kakao_access_token = access_token
            user.kakao_refresh_token = refresh_token
            user.kakao_token_expires_at = expires_at
            user.is_anonymous = False
            db.commit()

            logger.info(f"기존 사용자 토큰 업데이트: kakao_id={kakao_id} (DB ID: {user.id})")

        tokens = create_tokens_for_user(user.id, is_anonymous=False)
        user.refresh_token = tokens["refresh_token"]
        user.refresh_token_expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        user.access_token = tokens["access_token"]
        db.commit()
        db.refresh(user)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "로그인이 완료되었습니다",
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "is_new_user": is_new_user,
            }
        )
        
    except HTTPException as he:
        return JSONResponse(
            status_code=he.status_code,
            content={
                "success": False,
                "error": "http_exception",
                "message": str(he.detail)
            }
        )
    except Exception as e:
        logger.error(f"카카오 로그인 콜백 처리 실패: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "server_error",
                "message": "서버 처리 중 오류가 발생했습니다"
            }
        )

@router.get("/check/kakao-login")
async def check_kakao_login(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.refresh_token == request.refresh_token,
        User.refresh_token_expires_at > datetime.utcnow(),
        User.is_anonymous == False
        ).first()

    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    return {
        "kakao_id": user.kakao_id,
        "is_anonymous": user.is_anonymous,
        "refresh_token": user.refresh_token
    }

@router.post("/kakao/refresh/{kakao_id}")
async def refresh_kakao_token(
    kakao_id: str,
    db: Session = Depends(get_db)
):
    """카카오 토큰 갱신"""
    user = db.query(User).filter(User.kakao_id == kakao_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    if not user.kakao_refresh_token:
        raise HTTPException(status_code=400, detail="리프레시 토큰이 없습니다")
    
    try:
        # 리프레시 토큰으로 새 액세스 토큰 획득
        token_data = await kakao_oauth.refresh_access_token(user.kakao_refresh_token)
        if not token_data:
            raise HTTPException(status_code=400, detail="토큰 갱신에 실패했습니다")
        
        # 토큰 정보 업데이트
        user.kakao_access_token = token_data.get("access_token")
        user.kakao_refresh_token = token_data.get("refresh_token")
        user.kakao_token_expires_at = token_data.get("expires_at")
        db.commit()
        
        logger.info(f"사용자 {user.kakao_id}의 토큰 갱신 완료")
        
        return {
            "message": "토큰이 성공적으로 갱신되었습니다",
            "expires_at": token_data.get("expires_at")
        }
        
    except Exception as e:
        logger.error(f"토큰 갱신 실패: {e}")
        raise HTTPException(status_code=500, detail="토큰 갱신 중 오류가 발생했습니다")

@router.post("/kakao/logout")
async def kakao_logout(
    user_id: int = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """카카오 로그아웃 (토큰 무효화)"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    try:
        # 카카오 서버에서 토큰 무효화
        success = await kakao_oauth.revoke_token(user.kakao_access_token)
        
        # DB에서 토큰 정보 삭제
        user.kakao_access_token = None
        user.kakao_refresh_token = None
        user.kakao_token_expires_at = None
        user.is_anonymous = True
        db.commit()
        
        logger.info(f"사용자 {user.kakao_id} 로그아웃 완료")
        
        return {
            "message": "성공적으로 로그아웃되었습니다",
            "kakao_logout_success": success
        }
        
    except Exception as e:
        logger.error(f"로그아웃 실패: {e}")
        raise HTTPException(status_code=500, detail="로그아웃 중 오류가 발생했습니다")
