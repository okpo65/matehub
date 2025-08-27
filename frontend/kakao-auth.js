/**
 * Kakao OAuth Login Client - Simple PostMessage Version
 * 팝업과 postMessage를 사용하는 간단한 카카오 로그인 클라이언트
 */
class KakaoAuthClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.currentUser = null;
        this.isLoggedIn = false;
        this.popupWindow = null;
    }

    /**
     * Initialize auth client and check current login status
     */
    async init() {
        try {
            console.log('KakaoAuth 초기화 시작...');
            await this.checkLoginStatus();
        } catch (error) {
            console.error('Auth initialization error:', error);
            this.showLoginButtons();
        }
    }

    /**
     * Check current login status from localStorage
     */
    async checkLoginStatus() {
        try {
            const storedUser = localStorage.getItem('kakao_user');
            const userId = localStorage.getItem('user_id');
            const kakaoId = localStorage.getItem('kakao_id');
            const isAnonymous = localStorage.getItem('is_anonymous') === 'true';

            if (storedUser && userId && kakaoId && !isAnonymous) {
                this.currentUser = JSON.parse(storedUser);
                
                // Verify with backend using kakao_id
                const response = await fetch(`${this.baseUrl}/auth/user/${kakaoId}`);
                if (response.ok) {
                    this.isLoggedIn = true;
                    this.showUserInfo();
                    return;
                }
            }

            this.showLoginButtons();
        } catch (error) {
            console.error('Login status check error:', error);
            this.showLoginButtons();
        }
    }

    /**
     * Start Kakao login process
     */
    async startKakaoLogin() {
        try {
            this.showLoading('카카오 로그인 URL 생성 중...');

            const response = await fetch(`${this.baseUrl}/auth/kakao/login`);
            const data = await response.json();
            
            if (data.auth_url) {
                this.openKakaoPopup(data.auth_url);
            } else {
                throw new Error('로그인 URL을 받지 못했습니다');
            }
        } catch (error) {
            console.error('Kakao login start error:', error);
            alert(`카카오 로그인 시작 중 오류가 발생했습니다: ${error.message}`);
            this.hideLoading();
        }
    }

    /**
     * Open Kakao login popup
     */
    openKakaoPopup(authUrl) {
        const popupWidth = 500;
        const popupHeight = 600;
        const left = (window.screen.width - popupWidth) / 2;
        const top = (window.screen.height - popupHeight) / 2;

        this.popupWindow = window.open(
            authUrl,
            'kakaoLogin',
            `width=${popupWidth},height=${popupHeight},left=${left},top=${top},scrollbars=yes,resizable=yes`
        );

        if (!this.popupWindow) {
            alert('팝업이 차단되었습니다. 팝업 차단을 해제하고 다시 시도해주세요.');
            this.hideLoading();
            return;
        }

        this.showLoading('로그인 처리 중...');
        this.monitorPopup();
    }

    /**
     * Monitor popup for messages and closure
     */
    monitorPopup() {
        // Listen for messages from popup
        const messageHandler = (event) => {
            // Verify origin for security
            if (event.origin !== this.baseUrl) {
                return;
            }

            console.log('팝업에서 메시지 수신:', event.data);

            if (event.data.type === 'kakao_login_success') {
                this.cleanupPopup();
                this.handleLoginSuccess(event.data.data);
                window.removeEventListener('message', messageHandler);
            } else if (event.data.type === 'kakao_login_error') {
                this.cleanupPopup();
                this.handleLoginError(event.data);
                window.removeEventListener('message', messageHandler);
            }
        };

        window.addEventListener('message', messageHandler);
    }

    async handleLoginSuccess(loginData) {
        try {
            console.log('로그인 성공 처리:', loginData);

            const userInfo = {
                kakao_id: loginData.kakao_id,
                user_id: loginData.user_id, // DB의 실제 user ID
                is_new_user: loginData.is_new_user,
                login_timestamp: loginData.login_timestamp,
                created_at: new Date().toISOString()
            };

            localStorage.setItem('kakao_user', JSON.stringify(userInfo));
            localStorage.setItem('user_id', loginData.user_id); // DB user ID 사용
            localStorage.setItem('kakao_id', loginData.kakao_id); // kakao_id도 별도 저장
            localStorage.setItem('is_anonymous', 'false');

            this.currentUser = userInfo;
            this.isLoggedIn = true;

            const message = loginData.is_new_user ? 
                '🎉 카카오 로그인 성공! 새 계정이 생성되었습니다.' : 
                '✅ 카카오 로그인 성공! 기존 계정으로 로그인되었습니다.';

            this.showUserInfo();

            // Update chat client if available
            if (window.chatClient) {
                if (window.chatClient.updateId) {
                    window.chatClient.updateId('user', loginData.user_id); // DB user ID 사용
                }
                
                const userIdInput = document.getElementById('userIdInput');
                if (userIdInput) {
                    userIdInput.value = loginData.user_id; // DB user ID 사용
                }
            }

            if (window.updateUserIdDisplay) {
                window.updateUserIdDisplay(loginData.user_id); // DB user ID 사용
            }

            // Show success message and redirect to main chat
            this.showSuccessMessage(message);
            console.log('카카오 로그인 완료:', userInfo);
            this.redirectToMainChat();

        } catch (error) {
            console.error('Login success processing error:', error);
            this.hideLoading();
            this.showLoginButtons();
            alert(`로그인 정보 처리 중 오류가 발생했습니다: ${error.message}`);
        }
    }

    /**
     * Handle login error
     */
    handleLoginError(errorData) {
        console.error('로그인 오류:', errorData);

        let errorMessage = '카카오 로그인 중 오류가 발생했습니다.';
        if (errorData.message) {
            errorMessage = errorData.message;
        } else if (errorData.error) {
            switch (errorData.error) {
                case 'token_failed':
                    errorMessage = '토큰 획득에 실패했습니다.';
                    break;
                case 'no_access_token':
                    errorMessage = '액세스 토큰을 받지 못했습니다.';
                    break;
                case 'user_info_failed':
                    errorMessage = '사용자 정보 획득에 실패했습니다.';
                    break;
                case 'no_code':
                    errorMessage = '인증 코드를 받지 못했습니다.';
                    break;
                default:
                    errorMessage = `로그인 오류: ${errorData.error}`;
            }
        }

        this.hideLoading();
        this.showLoginButtons();
        alert(errorMessage);
    }

    /**
     * Cleanup popup
     */
    cleanupPopup() {
        if (this.popupWindow && !this.popupWindow.closed) {
            this.popupWindow.close();
        }
        this.popupWindow = null;
    }

    /**
     * Start anonymous session
     */
    async startAnonymousLogin() {
        try {
            this.showLoading('익명 세션 생성 중...');

            const anonymousUser = {
                user_id: 'anonymous_' + Date.now(),
                is_anonymous: true,
                created_at: new Date().toISOString()
            };

            localStorage.setItem('user_id', anonymousUser.user_id);
            localStorage.setItem('is_anonymous', 'true');
            localStorage.removeItem('kakao_user');

            this.currentUser = anonymousUser;
            this.isLoggedIn = true;

            alert('익명 세션이 시작되었습니다.');
            this.showUserInfo();

            if (window.chatClient && window.updateUserIdDisplay) {
                window.chatClient.updateId('user', anonymousUser.user_id);
                window.updateUserIdDisplay(anonymousUser.user_id);
            }

        } catch (error) {
            console.error('Anonymous login error:', error);
            alert(`익명 로그인 중 오류가 발생했습니다: ${error.message}`);
            this.hideLoading();
        }
    }

    /**
     * Logout user
     */
    async logout() {
        try {
            const kakaoId = localStorage.getItem('kakao_id');
            const isAnonymous = localStorage.getItem('is_anonymous') === 'true';

            if (!isAnonymous && kakaoId) {
                const response = await fetch(`${this.baseUrl}/auth/kakao/logout/${kakaoId}`, {
                    method: 'POST'
                });
                if (response.ok) {
                    console.log('Kakao logout successful');
                }
            }

            localStorage.removeItem('kakao_user');
            localStorage.removeItem('user_id');
            localStorage.removeItem('kakao_id');
            localStorage.removeItem('is_anonymous');
            localStorage.removeItem('recent_kakao_login');

            this.currentUser = null;
            this.isLoggedIn = false;

            alert('로그아웃되었습니다.');
            this.showLoginButtons();

            if (window.chatClient && window.updateUserIdDisplay) {
                window.chatClient.updateId('user', 1);
                window.updateUserIdDisplay(1);
            }

        } catch (error) {
            console.error('Logout error:', error);
            alert(`로그아웃 중 오류가 발생했습니다: ${error.message}`);
        }
    }

    /**
     * Show user info in UI
     */
    showUserInfo() {
        const userInfo = document.getElementById('userInfo');
        const loginButtons = document.getElementById('loginButtons');
        const userName = document.getElementById('userName');

        if (userInfo && loginButtons && userName) {
            const isAnonymous = localStorage.getItem('is_anonymous') === 'true';

            if (isAnonymous) {
                userName.innerHTML = `
                    <span class="user-display">
                        <span class="anonymous-user-id">익명 사용자</span>
                        <span class="user-type-badge anonymous">익명</span>
                    </span>
                `;
            } else if (this.currentUser && this.currentUser.kakao_id) {
                userName.innerHTML = `
                    <span class="user-display">
                        <span class="kakao-user-id">카카오 사용자 (${this.currentUser.kakao_id})</span>
                        <span class="user-type-badge kakao">카카오 로그인됨</span>
                    </span>
                `;
            } else {
                const storedKakaoUser = localStorage.getItem('kakao_user');
                if (storedKakaoUser && !isAnonymous) {
                    try {
                        const kakaoUser = JSON.parse(storedKakaoUser);
                        userName.innerHTML = `
                            <span class="user-display">
                                <span class="kakao-user-id">카카오 사용자 (${kakaoUser.kakao_id})</span>
                                <span class="user-type-badge kakao">카카오 로그인됨</span>
                            </span>
                        `;
                    } catch (e) {
                        userName.textContent = `사용자`;
                    }
                } else {
                    userName.textContent = `사용자`;
                }
            }

            userInfo.style.display = 'flex';
            loginButtons.style.display = 'none';
        }

        this.hideLoading();
    }

    /**
     * Show login buttons in UI
     */
    showLoginButtons() {
        const userInfo = document.getElementById('userInfo');
        const loginButtons = document.getElementById('loginButtons');

        if (userInfo && loginButtons) {
            userInfo.style.display = 'none';
            loginButtons.style.display = 'flex';
        }

        this.hideLoading();
    }

    /**
     * Show loading state
     */
    showLoading(message = '처리 중...') {
        const loginStatus = document.getElementById('loginStatus');
        if (loginStatus) {
            loginStatus.innerHTML = `
                <div style="text-align: center; padding: 20px; color: #666;">
                    <div style="margin-bottom: 10px;">⏳</div>
                    <div>${message}</div>
                </div>
            `;
        }
    }

    /**
     * Show success message
     */
    showSuccessMessage(message) {
        const loginStatus = document.getElementById('loginStatus');
        if (loginStatus) {
            loginStatus.innerHTML = `
                <div style="text-align: center; padding: 20px; color: #28a745; background: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px; margin: 10px 0;">
                    <div style="margin-bottom: 10px; font-size: 24px;">✅</div>
                    <div style="font-weight: bold; margin-bottom: 5px;">${message}</div>
                    <div style="font-size: 14px; color: #155724;">메인 채팅으로 이동합니다...</div>
                </div>
            `;
        }
    }

    /**
     * Redirect to main chat page
     */
    redirectToMainChat() {
        // If we're already on the main page, just refresh
        if (window.location.pathname === '/' || window.location.pathname === '/index.html') {
            window.location.reload();
        } else {
            // Navigate to main chat page
            window.location.href = '/';
        }
    }

    /**
     * Hide loading state
     */
    hideLoading() {
        // Loading will be cleared by showUserInfo() or showLoginButtons()
    }

    /**
     * Get current user ID for API calls
     */
    getCurrentUserId() {
        return localStorage.getItem('user_id');
    }

    /**
     * Check if user is logged in
     */
    isUserLoggedIn() {
        return this.isLoggedIn && this.getCurrentUserId();
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        const kakaoLoginBtn = document.getElementById('kakaoLoginBtn');
        if (kakaoLoginBtn) {
            kakaoLoginBtn.addEventListener('click', () => {
                this.startKakaoLogin();
            });
        }

        const anonymousLoginBtn = document.getElementById('anonymousLoginBtn');
        if (anonymousLoginBtn) {
            anonymousLoginBtn.addEventListener('click', () => {
                this.startAnonymousLogin();
            });
        }

        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                if (confirm('정말 로그아웃하시겠습니까?')) {
                    this.logout();
                }
            });
        }

        window.addEventListener('beforeunload', () => {
            this.cleanupPopup();
        });
    }
}

window.KakaoAuthClient = KakaoAuthClient;
