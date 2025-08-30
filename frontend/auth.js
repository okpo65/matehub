/**
 * JWT-based authentication helper for anonymous and Kakao OAuth login
 */
class AuthClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }

    /**
     * Get JWT token from localStorage or cookie
     */
    getToken() {
        // Try localStorage first
        let token = localStorage.getItem('access_token');
        if (token) return token;
        
        // Try cookie as fallback
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'access_token') {
                return value;
            }
        }
        return null;
    }

    /**
     * Set JWT token in localStorage and Authorization header
     */
    setToken(token) {
        if (token) {
            localStorage.setItem('access_token', token);
        } else {
            localStorage.removeItem('access_token');
        }
    }

    /**
     * Get Authorization headers for API calls
     */
    getAuthHeaders() {
        const token = this.getToken();
        return token ? {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        } : {
            'Content-Type': 'application/json'
        };
    }

    /**
     * Initialize anonymous user session
     */
    async initAnonymousUser() {
        try {
            const response = await fetch(`${this.baseUrl}/auth/anonymous`, {
                method: 'POST',
                credentials: 'include'  // Include cookies
            });
            
            if (!response.ok) {
                throw new Error('Anonymous login failed');
            }
            
            const data = await response.json();
            
            // Store token
            this.setToken(data.access_token);
            
            // Store user info as backup
            localStorage.setItem('user_id', data.user_id);
            localStorage.setItem('is_anonymous', 'true');
            
            return data;
        } catch (error) {
            console.error('Anonymous login error:', error);
            throw error;
        }
    }

    /**
     * Get Kakao authorization URL
     */
    async getKakaoAuthUrl() {
        try {
            const response = await fetch(`${this.baseUrl}/auth/kakao/url`);
            
            if (!response.ok) {
                throw new Error('Failed to get Kakao auth URL');
            }
            
            const data = await response.json();
            return data.authorization_url;
        } catch (error) {
            console.error('Kakao auth URL error:', error);
            throw error;
        }
    }

    /**
     * Start Kakao OAuth flow
     */
    async startKakaoLogin() {
        try {
            const authUrl = await this.getKakaoAuthUrl();
            
            // Redirect to Kakao authorization page
            window.location.href = authUrl;
        } catch (error) {
            console.error('Kakao login start error:', error);
            throw error;
        }
    }

    /**
     * Handle Kakao OAuth callback with authorization code
     */
    async handleKakaoCallback(authorizationCode) {
        try {
            const response = await fetch(`${this.baseUrl}/auth/kakao/callback`, {
                method: 'POST',
                headers: this.getAuthHeaders(),
                credentials: 'include',
                body: JSON.stringify({
                    authorization_code: authorizationCode
                })
            });
            
            if (!response.ok) {
                throw new Error('Kakao callback failed');
            }
            
            const data = await response.json();
            
            // Store new token
            localStorage.setItem('is_anonymous', 'false');
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            
            return data;
        } catch (error) {
            console.error('Kakao callback error:', error);
            throw error;
        }
    }

    /**
     * Get current user info
     */
    async getCurrentUser() {
        try {
            const response = await fetch(`${this.baseUrl}/auth/me`, {
                headers: this.getAuthHeaders(),
                credentials: 'include'
            });
            
            if (!response.ok) {
                if (response.status === 401) {
                    // No valid token, try anonymous login
                    return await this.initAnonymousUser();
                }
                throw new Error('Failed to get user info');
            }
            
            const data = await response.json();
            
            // Update localStorage
            localStorage.setItem('user_id', data.user_id);
            localStorage.setItem('is_anonymous', data.is_anonymous.toString());
            
            return data;
        } catch (error) {
            console.error('Get user error:', error);
            // Try anonymous login as fallback
            try {
                return await this.initAnonymousUser();
            } catch (fallbackError) {
                console.error('Fallback anonymous login failed:', fallbackError);
                throw error;
            }
        }
    }

    /**
     * Verify current token
     */
    async verifyToken() {
        try {
            const response = await fetch(`${this.baseUrl}/auth/verify`, {
                headers: this.getAuthHeaders(),
                credentials: 'include'
            });
            
            return response.ok;
        } catch (error) {
            console.error('Token verification error:', error);
            return false;
        }
    }

    /**
     * Logout user
     */
    async logout() {
        try {
            const response = await fetch(`${this.baseUrl}/auth/logout`, {
                method: 'POST',
                headers: this.getAuthHeaders(),
                credentials: 'include'
            });
            
            // Clear token and localStorage regardless of response
            this.setToken(null);
            localStorage.removeItem('user_id');
            localStorage.removeItem('is_anonymous');
            
            return await response.json();
        } catch (error) {
            console.error('Logout error:', error);
            // Clear local data even if request fails
            this.setToken(null);
            localStorage.removeItem('user_id');
            localStorage.removeItem('is_anonymous');
            throw error;
        }
    }

    /**
     * Get user ID from localStorage (fallback)
     */
    getUserId() {
        return localStorage.getItem('user_id');
    }

    /**
     * Check if user is anonymous
     */
    isAnonymous() {
        return localStorage.getItem('is_anonymous') !== 'false';
    }

    /**
     * Extract authorization code from URL (for callback page)
     */
    getAuthCodeFromUrl() {
        const url = new URL(window.location.href);
        const params = new URLSearchParams(url.search);
        
        // Debug logging
        console.log('Full URL:', window.location.href);
        console.log('Search params:', url.search);
        console.log('All params:', Object.fromEntries(params.entries()));
        
        const code = params.get('code');
        const error = params.get('error');
        const errorDescription = params.get('error_description');
        
        if (error) {
            console.error('OAuth error:', error, errorDescription);
            throw new Error(`Kakao OAuth error: ${error} - ${errorDescription}`);
        }
        
        if (code) {
            console.log('Authorization code found:', code.substring(0, 20) + '...');
        } else {
            console.warn('No authorization code found in URL');
        }
        
        return code;
    }

    /**
     * Check if current page is Kakao callback
     */
    isKakaoCallback() {
        // Check if URL has authorization code parameter
        const hasAuthCode = new URLSearchParams(window.location.search).has('code');
        
        // Check if URL has state parameter (Kakao OAuth includes this)
        const hasState = new URLSearchParams(window.location.search).has('state');
        
        // Return true if has both code and state parameters (indicating OAuth callback)
        return hasAuthCode && hasState;
    }

    /**
     * Make authenticated API request
     */
    async apiRequest(endpoint, options = {}) {
        const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`;
        
        const config = {
            headers: this.getAuthHeaders(),
            credentials: 'include',
            ...options
        };

        // Merge headers if provided in options
        if (options.headers) {
            config.headers = { ...config.headers, ...options.headers };
        }

        try {
            const response = await fetch(url, config);
            
            // Handle 401 - token might be expired
            if (response.status === 401) {
                // Try to refresh token or re-authenticate
                const isValid = await this.verifyToken();
                if (!isValid) {
                    // Token is invalid, try anonymous login
                    await this.initAnonymousUser();
                    // Retry the request with new token
                    config.headers = this.getAuthHeaders();
                    return await fetch(url, config);
                }
            }
            
            return response;
        } catch (error) {
            console.error('API request error:', error);
            throw error;
        }
    }
}