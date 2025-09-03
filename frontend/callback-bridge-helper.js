// 백엔드에서 사용할 callback-bridge URL 생성 함수
function createCallbackBridgeUrl(accessToken, refreshToken, kakaoId, isNewUser) {
    const baseUrl = 'http://localhost:3000/callback-bridge.html';
    const params = new URLSearchParams({
        access_token: accessToken,
        refresh_token: refreshToken,
        kakao_id: kakaoId,
        is_new_user: isNewUser.toString()
    });
    return `${baseUrl}?${params.toString()}`;
}

// Python 백엔드 예시:
/*
from urllib.parse import urlencode

def create_callback_bridge_url(access_token, refresh_token, kakao_id, is_new_user):
    base_url = "http://localhost:3000/callback-bridge.html"
    params = {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'kakao_id': str(kakao_id),
        'is_new_user': str(is_new_user).lower()
    }
    return f"{base_url}?{urlencode(params)}"

# 사용 예시:
# redirect_url = create_callback_bridge_url(access_token, refresh_token, kakao_id, is_new_user)
# return redirect(redirect_url)
*/
