import httpx
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from app.config import settings

class KakaoOAuth:
    def __init__(self):
        self.client_id = settings.kakao_rest_api_key
        self.client_secret = settings.kakao_client_secret
        self.redirect_uri = settings.kakao_redirect_uri
        
    def get_authorization_url(self) -> str:
        """카카오 로그인 URL 생성"""
        base_url = "https://kauth.kakao.com/oauth/authorize"
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code"
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_string}"
    
    async def get_tokens(self, code: str) -> Optional[Dict[str, Any]]:
        """인증 코드로 액세스 토큰과 리프레시 토큰 획득"""
        url = "https://kauth.kakao.com/oauth/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "code": code
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data)
            if response.status_code == 200:
                token_data = response.json()
                
                # 토큰 만료 시간 계산 (현재 시간 + expires_in 초)
                expires_in = token_data.get("expires_in", 21600)  # 기본 6시간
                expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                
                return {
                    "access_token": token_data.get("access_token"),
                    "refresh_token": token_data.get("refresh_token"),
                    "expires_at": expires_at,
                    "token_type": token_data.get("token_type", "bearer"),
                    "scope": token_data.get("scope")
                }
            return None
    
    async def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """리프레시 토큰으로 액세스 토큰 갱신"""
        url = "https://kauth.kakao.com/oauth/token"
        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data)
            if response.status_code == 200:
                token_data = response.json()
                
                # 토큰 만료 시간 계산
                expires_in = token_data.get("expires_in", 21600)
                expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                
                return {
                    "access_token": token_data.get("access_token"),
                    "refresh_token": token_data.get("refresh_token", refresh_token),  # 새 리프레시 토큰이 없으면 기존 것 유지
                    "expires_at": expires_at,
                    "token_type": token_data.get("token_type", "bearer"),
                    "scope": token_data.get("scope")
                }
            return None
    
    async def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """액세스 토큰으로 사용자 정보 획득"""
        url = "https://kapi.kakao.com/v2/user/me"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            return None
    
    async def revoke_token(self, access_token: str) -> bool:
        """토큰 무효화 (로그아웃)"""
        url = "https://kapi.kakao.com/v1/user/logout"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers)
            return response.status_code == 200

kakao_oauth = KakaoOAuth()
