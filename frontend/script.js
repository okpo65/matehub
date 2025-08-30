/**
 * MateHub Frontend Application
 * Main script that initializes the chat client and handles UI interactions
 */

// Global variables
let chatClient = null;
let configPanelVisible = true;
let kakaoAuth = null;
let apiService = null;

/**
 * Initialize the application when DOM is loaded
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM 로드 완료, 앱 초기화 시작...');
    console.log('현재 URL:', window.location.href);
    initializeApp();
});

/**
 * Initialize the application
 */
async function initializeApp() {
    try {
        console.log('앱 초기화 시작...');
        
        // Initialize API service
        apiService = new ApiService();
        
        // Initialize authentication (get anonymous token if needed)
        await apiService.initializeAuth();
        
        // Try to get current user info if authenticated
        try {
            const validation = await apiService.validateToken();
            if (validation.user_type === 'authenticated') {
                const currentUser = await apiService.getCurrentUser();
                console.log('Current user:', currentUser);
                updateUserInfo(currentUser);
            } else {
                console.log('Using anonymous authentication');
                updateAnonymousUserInfo();
            }
        } catch (error) {
            console.error('Failed to validate token or get user info:', error);
            updateAnonymousUserInfo();
        }
        
        // URL 파라미터를 먼저 확인하고 저장
        const urlParams = new URLSearchParams(window.location.search);
        const loginSuccess = urlParams.get('login_success');
        const kakaoId = urlParams.get('kakao_id');
        
        console.log('초기화 시 URL 파라미터:', {
            loginSuccess,
            kakaoId,
            fullUrl: window.location.href
        });
        
        // Initialize Kakao auth first
        kakaoAuth = new KakaoAuthClient();
        await kakaoAuth.init();
        kakaoAuth.setupEventListeners();
        
        // Initialize chat client
        chatClient = new ChatClient();
        
        // Setup configuration panel
        setupConfigPanel();
        
        // Setup API buttons
        setupApiButtons();
        
        // Load user info and update user ID if logged in
        loadUserInfo();
        
        // Setup ID update functions
        setupIdUpdates();
        
        console.log('MateHub application initialized successfully');
    } catch (error) {
        console.error('Failed to initialize application:', error);
        showInitializationError(error);
    }
}

/**
 * Setup configuration panel toggle
 */
function setupConfigPanel() {
    const toggleBtn = document.getElementById('toggleSidebar');
    const sidebar = document.getElementById('sidebar');
    
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
            
            // Save sidebar state to localStorage
            const isCollapsed = sidebar.classList.contains('collapsed');
            localStorage.setItem('sidebar-collapsed', isCollapsed.toString());
        });
        
        // Restore sidebar state from localStorage
        const savedState = localStorage.getItem('sidebar-collapsed');
        if (savedState === 'true') {
            sidebar.classList.add('collapsed');
        }
    }
}

/**
 * Setup API action buttons
 */
function setupApiButtons() {
    // Test connection button
    const testBtn = document.getElementById('testConnectionBtn');
    if (testBtn) {
        testBtn.addEventListener('click', async () => {
            testBtn.disabled = true;
            testBtn.textContent = 'Testing...';
            
            try {
                await chatClient.checkServerHealth();
                testBtn.className = 'api-btn success';
                testBtn.textContent = 'Connected ✓';
                
                setTimeout(() => {
                    testBtn.className = 'api-btn';
                    testBtn.textContent = 'Test Connection';
                    testBtn.disabled = false;
                }, 2000);
            } catch (error) {
                testBtn.className = 'api-btn danger';
                testBtn.textContent = 'Failed ✗';
                
                setTimeout(() => {
                    testBtn.className = 'api-btn';
                    testBtn.textContent = 'Test Connection';
                    testBtn.disabled = false;
                }, 2000);
            }
        });
    }
    
    // Clear chat button
    const clearBtn = document.getElementById('clearChatBtn');
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to clear the chat history?')) {
                chatClient.clearChat();
            }
        });
    }
    
    // Export chat button
    const exportBtn = document.getElementById('exportChatBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', () => {
            chatClient.exportChat();
        });
    }
}

/**
 * Setup ID update functionality
 */
function setupIdUpdates() {
    // Make updateId function globally available
    window.updateId = (type) => {
        // 카카오 로그인 사용자의 경우 User ID 변경 방지
        if (type === 'user' && kakaoAuth && kakaoAuth.isUserLoggedIn()) {
            const isAnonymous = localStorage.getItem('is_anonymous') === 'true';
            if (!isAnonymous) {
                alert('카카오 로그인 사용자는 User ID를 변경할 수 없습니다');
                return;
            }
        }
        
        const inputId = `${type}IdInput`;
        const currentId = `current${type.charAt(0).toUpperCase() + type.slice(1)}Id`;
        
        const input = document.getElementById(inputId);
        const current = document.getElementById(currentId);
        
        if (input && current) {
            const value = parseInt(input.value);
            if (chatClient.updateId(type, value)) {
                if (type === 'user') {
                    // Update display based on login status
                    updateUserIdDisplay(value);
                } else {
                    current.textContent = value;
                }
                input.value = value; // Reset input to valid value
            } else {
                input.value = current.textContent; // Reset to current value
            }
        }
    };
    
    // Add Enter key support for ID inputs
    ['user', 'character', 'story'].forEach(type => {
        const input = document.getElementById(`${type}IdInput`);
        if (input) {
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    updateId(type);
                }
            });
        }
    });
}

/**
 * Update user ID display based on login status
 */
function updateUserIdDisplay(userId) {
    const currentUserId = document.getElementById('currentUserId');
    const headerUserId = document.getElementById('headerUserId');
    
    if (currentUserId) {
        const isAnonymous = localStorage.getItem('is_anonymous') === 'true';
        const urlParams = new URLSearchParams(window.location.search);
        const loginSuccess = urlParams.get('login_success');
        const kakaoId = urlParams.get('kakao_id');
        
        // Check if this is from Kakao login callback
        if (loginSuccess === 'true' && kakaoId) {
            currentUserId.innerHTML = `<span class="kakao-user-id">${kakaoId}</span> <span class="user-type-badge kakao">카카오 로그인됨</span>`;
        } else if (isAnonymous) {
            currentUserId.innerHTML = `<span class="anonymous-user-id">${userId}</span> <span class="user-type-badge anonymous">익명</span>`;
        } else if (kakaoAuth?.currentUser?.kakao_id) {
            const kakaoUserId = kakaoAuth.currentUser.kakao_id;
            currentUserId.innerHTML = `<span class="kakao-user-id">${kakaoUserId}</span> <span class="user-type-badge kakao">카카오 로그인됨</span>`;
        } else {
            // Check if we have stored kakao user info
            const storedKakaoUser = localStorage.getItem('kakao_user');
            if (storedKakaoUser && !isAnonymous) {
                try {
                    const kakaoUser = JSON.parse(storedKakaoUser);
                    currentUserId.innerHTML = `<span class="kakao-user-id">${kakaoUser.kakao_id}</span> <span class="user-type-badge kakao">카카오 로그인됨</span>`;
                } catch (e) {
                    currentUserId.innerHTML = `<span class="user-id">${userId}</span>`;
                }
            } else {
                currentUserId.innerHTML = `<span class="user-id">${userId}</span>`;
            }
        }
    }
    
    if (headerUserId) {
        headerUserId.textContent = userId;
    }
}

/**
 * Show initialization error
 */
function showInitializationError(error) {
    const errorDiv = document.createElement('div');
    errorDiv.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: #dc3545;
        color: white;
        padding: 1rem 2rem;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 10000;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    `;
    errorDiv.innerHTML = `
        <strong>Initialization Error</strong><br>
        ${error.message || 'Failed to start the application'}
    `;
    
    document.body.appendChild(errorDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (errorDiv.parentNode) {
            errorDiv.parentNode.removeChild(errorDiv);
        }
    }, 5000);
}

/**
 * Handle page unload
 */
window.addEventListener('beforeunload', () => {
    if (chatClient) {
        chatClient.isWaitingForResponse = false;
    }
});

/**
 * Handle errors globally
 */
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
});

/**
 * Utility functions for debugging
 */
window.debugUtils = {
    getChatClient: () => chatClient,
    getKakaoAuth: () => kakaoAuth,
    getConfig: () => chatClient?.config,
    getHistory: () => chatClient?.conversationHistory,
    clearStorage: () => {
        localStorage.removeItem('matehub-config');
        localStorage.removeItem('kakao_user');
        localStorage.removeItem('user_id');
        localStorage.removeItem('is_anonymous');
        location.reload();
    },
    testApi: async () => {
        if (!chatClient) return 'Chat client not initialized';
        try {
            const health = await chatClient.apiService.checkApiHealth();
            return health;
        } catch (error) {
            return { error: error.message };
        }
    }
};

/**
 * Load user info from localStorage and update UI
 */
function loadUserInfo() {
    // First check if we have URL parameters from Kakao callback
    const urlParams = new URLSearchParams(window.location.search);
    const loginSuccess = urlParams.get('login_success');
    const kakaoId = urlParams.get('kakao_id');
    
    // If we have successful login parameters, use them
    if (loginSuccess === 'true' && kakaoId) {
        const userIdInput = document.getElementById('userIdInput');
        
        if (userIdInput) {
            userIdInput.value = kakaoId;
            
            // Update display
            updateUserIdDisplay(kakaoId);
            
            // Update chat client configuration
            if (chatClient && chatClient.updateId) {
                chatClient.updateId('user', kakaoId);
            }
        }
        return;
    }
    
    // Otherwise, check localStorage
    const userId = localStorage.getItem('user_id');
    if (userId) {
        // Update user ID in the configuration
        const userIdInput = document.getElementById('userIdInput');
        
        if (userIdInput) {
            userIdInput.value = userId;
            
            // Update display
            updateUserIdDisplay(userId);
            
            // Update chat client configuration
            if (chatClient && chatClient.updateId) {
                chatClient.updateId('user', userId);
            }
        }
    }
}

/**
 * Update user info in the UI
 */
function updateUserInfo(user) {
    const userInfo = document.getElementById('userInfo');
    const userName = document.getElementById('userName');
    const loginButtons = document.getElementById('loginButtons');
    
    if (userInfo && userName && loginButtons) {
        userName.textContent = user.name || user.nickname;
        userInfo.style.display = 'block';
        loginButtons.style.display = 'none';
    }
    
    // Setup logout button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
}

/**
 * Update UI for anonymous user
 */
function updateAnonymousUserInfo() {
    const userInfo = document.getElementById('userInfo');
    const loginButtons = document.getElementById('loginButtons');
    
    if (userInfo && loginButtons) {
        userInfo.style.display = 'none';
        loginButtons.style.display = 'block';
    }
}

/**
 * Handle user logout
 */
function handleLogout() {
    if (apiService) {
        apiService.logout();
        // Get new anonymous token
        apiService.initializeAuth();
        updateAnonymousUserInfo();
    }
}

// Export for potential module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initializeApp,
        setupConfigPanel,
        setupApiButtons,
        setupIdUpdates,
        loadUserInfo,
        updateUserIdDisplay,
        updateUserInfo,
        handleLogout
    };
}
