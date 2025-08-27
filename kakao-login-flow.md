# 카카오 로그인 플로우 상세 가이드

## 개요
카카오 OAuth 2.0을 이용한 소셜 로그인 구현 과정을 단계별로 설명합니다.

## 전체 플로우 다이어그램
```
Frontend → Kakao Auth Server → Callback Page → Backend API → Frontend
    1           2                 3             4           5
```

## 단계별 상세 설명

### 1단계: 로그인 요청 (`auth/kakao/login`)

**목적**: 카카오 인증 서버로의 리다이렉트 URL 생성

**프로세스**:
- 사용자가 "카카오 로그인" 버튼 클릭
- 백엔드 API `auth/kakao/login` 호출
- 카카오 OAuth 인증 URL 생성 및 반환

**생성되는 URL**:
```
https://kauth.kakao.com/oauth/authorize?client_id=af8d24adce09ccf9de9d06fdd4e342cc&redirect_uri=http://localhost:8000/auth/kakao/callback/page&response_type=code
```

**URL 파라미터 설명**:
- `client_id`: 카카오 앱의 REST API 키
- `redirect_uri`: 인증 완료 후 리다이렉트될 콜백 URL
- `response_type=code`: Authorization Code Grant 방식 사용

### 2단계: 카카오 인증 서버 리다이렉트

**목적**: 사용자 인증 및 권한 승인

**프로세스**:
- 프론트엔드에서 새 창(팝업)으로 카카오 인증 URL 열기
- 사용자가 카카오 계정으로 로그인
- 앱 권한 승인 (프로필 정보, 이메일 등)
- 카카오에서 인증 완료 후 `redirect_uri`로 리다이렉트

**사용자 경험**:
1. 카카오 로그인 페이지 표시
2. 이메일/비밀번호 입력 또는 간편 로그인
3. 앱 권한 승인 화면
4. 승인 완료

### 3단계: 콜백 페이지 리다이렉트

**목적**: 인증 코드 수신 및 처리

**리다이렉트 URL**:
```
http://localhost:8000/auth/kakao/callback/page?code={authorization_code}
```

**프로세스**:
- 카카오에서 인증 성공 시 콜백 URL로 리다이렉트
- URL 쿼리 파라미터로 `code` 전달
- 콜백 페이지에서 `code` 추출

**코드 예시**:
```javascript
// 콜백 페이지에서 code 추출
const urlParams = new URLSearchParams(window.location.search);
const code = urlParams.get('code');
```

### 4단계: 토큰 교환 (`auth/kakao/callback`)

**목적**: Authorization Code를 Access Token으로 교환

**API 엔드포인트**: `auth/kakao/callback?code={code}`

**프로세스** (`AuthClient.processAuthCode` 함수):
1. 콜백 페이지에서 백엔드 API 호출
2. Authorization Code를 카카오 토큰 서버로 전송
3. Access Token 및 Refresh Token 수신
4. 사용자 정보 조회 (카카오 API 호출)
5. 사용자 정보 저장/업데이트
6. 애플리케이션 JWT 토큰 생성

**카카오 토큰 API 호출**:
```http
POST https://kauth.kakao.com/oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code
&client_id={REST_API_KEY}
&redirect_uri={REDIRECT_URI}
&code={AUTHORIZATION_CODE}
```

**응답 데이터**:
```json
{
  "access_token": "xxxxxx",
  "refresh_token": "xxxxxx", 
  "token_type": "bearer",
  "expires_in": 21599
}
```

### 5단계: 부모 창으로 결과 전달

**목적**: 팝업 창에서 메인 창으로 로그인 결과 전달

**프로세스** (`window.opener.postMessage`):
1. 콜백 페이지에서 로그인 처리 완료
2. `window.opener.postMessage`로 부모 창에 결과 전달
3. 팝업 창 자동 닫기
4. 메인 창에서 로그인 상태 업데이트

**PostMessage 데이터 구조**:
```javascript
// 성공 시
window.opener.postMessage({
  type: 'KAKAO_LOGIN_SUCCESS',
  data: {
    user: userInfo,
    tokens: {
      access_token: 'jwt_token',
      refresh_token: 'refresh_token'
    }
  }
}, '*');

// 실패 시  
window.opener.postMessage({
  type: 'KAKAO_LOGIN_ERROR',
  error: 'error_message'
}, '*');
```

## 보안 고려사항

### CSRF 방지
- `state` 파라미터 사용으로 CSRF 공격 방지
- 세션 기반 state 값 검증

### 토큰 보안
- Access Token: 짧은 만료 시간 (1-2시간)
- Refresh Token: 안전한 저장소에 보관
- HTTPS 통신 필수

### 리다이렉트 URI 검증
- 카카오 개발자 콘솔에 등록된 URI만 허용
- 정확한 도메인 및 경로 매칭

## 에러 처리

### 일반적인 에러 케이스
1. **사용자 취소**: 사용자가 인증 과정에서 취소
2. **잘못된 클라이언트 ID**: 카카오 앱 설정 오류
3. **리다이렉트 URI 불일치**: 등록된 URI와 다른 경우
4. **만료된 코드**: Authorization Code 만료 (10분)
5. **네트워크 오류**: API 호출 실패

### 에러 응답 예시
```json
{
  "error": "invalid_grant",
  "error_description": "authorization code not found for code=xxxxx"
}
```

## 개발 환경 설정

### 카카오 개발자 콘솔 설정
1. **앱 생성**: 카카오 개발자 콘솔에서 앱 등록
2. **플랫폼 추가**: Web 플랫폼 추가
3. **리다이렉트 URI 등록**: `http://localhost:8000/auth/kakao/callback/page`
4. **동의항목 설정**: 필요한 사용자 정보 권한 설정

### 환경 변수 설정
```env
KAKAO_CLIENT_ID=af8d24adce09ccf9de9d06fdd4e342cc
KAKAO_REDIRECT_URI=http://localhost:8000/auth/kakao/callback/page
```

## 테스트 시나리오

### 정상 플로우 테스트
1. 로그인 버튼 클릭
2. 카카오 로그인 팝업 확인
3. 테스트 계정으로 로그인
4. 권한 승인
5. 메인 페이지 로그인 상태 확인

### 에러 플로우 테스트
1. 사용자 취소 시나리오
2. 네트워크 오류 시나리오
3. 잘못된 설정 시나리오

## 참고 자료
- [카카오 로그인 REST API 가이드](https://developers.kakao.com/docs/latest/ko/kakaologin/rest-api)
- [OAuth 2.0 RFC 6749](https://tools.ietf.org/html/rfc6749)
- [카카오 개발자 콘솔](https://developers.kakao.com/console/app)
