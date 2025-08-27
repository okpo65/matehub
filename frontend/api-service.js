/**
 * API Service for MateHub LLM/Chat endpoints
 * Handles all backend communication with proper error handling
 */
class ApiService {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.defaultTimeout = 10000; // 10 seconds
    }

    /**
     * Generic fetch wrapper with timeout and error handling
     */
    async fetchWithTimeout(url, options = {}) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.defaultTimeout);

        try {
            console.log(`Making request to: ${url}`);
            console.log('Request options:', options);

            const response = await fetch(url, {
                ...options,
                signal: controller.signal,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            clearTimeout(timeoutId);

            console.log(`Response status: ${response.status} ${response.statusText}`);

            if (!response.ok) {
                let errorDetail = `HTTP ${response.status}: ${response.statusText}`;
                try {
                    const errorBody = await response.text();
                    console.log('Error response body:', errorBody);
                    if (errorBody) {
                        try {
                            const errorJson = JSON.parse(errorBody);
                            errorDetail = errorJson.detail || errorDetail;
                        } catch (e) {
                            errorDetail = errorBody;
                        }
                    }
                } catch (e) {
                    console.log('Could not read error response body');
                }
                throw new Error(errorDetail);
            }

            const result = await response.json();
            console.log('Response data:', result);
            return result;
        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error('Request timeout');
            }
            console.error('Fetch error:', error);
            throw error;
        }
    }

    /**
     * Health check for main API
     */
    async checkApiHealth() {
        return this.fetchWithTimeout(`${this.baseUrl}/health`);
    }

    /**
     * Send chat message to LLM
     */
    async sendChatMessage(chatRequest) {
        const payload = {
            message: chatRequest.message,
            user_id: chatRequest.userId || null,
            character_id: chatRequest.characterId || null,
            story_id: chatRequest.storyId || null,
            model: chatRequest.model || 'llama3.2'
        };

        console.log('Sending chat request:', payload);

        try {
            const response = await this.fetchWithTimeout(`${this.baseUrl}/llm/chat`, {
                method: 'POST',
                body: JSON.stringify(payload)
            });
            console.log('Chat response:', response);
            return response;
        } catch (error) {
            console.error('Chat request failed:', error);
            throw error;
        }
    }

    /**
     * Get available models
     */
    async getAvailableModels() {
        try {
            const response = await this.fetchWithTimeout(`${this.baseUrl}/llm/models`);
            console.log('Available models response:', response);
            return response;
        } catch (error) {
            console.error('Failed to get available models:', error);
            throw error;
        }
    }

    /**
     * Generate text using Ollama LLM
     */
    async generateText(llmRequest) {
        const payload = {
            prompt: llmRequest.prompt,
            model: llmRequest.model || 'llama3.2',
            max_tokens: llmRequest.maxTokens || 1000,
            temperature: llmRequest.temperature || 0.7,
            system_prompt: llmRequest.systemPrompt || null,
            user_id: llmRequest.userId || null
        };

        return this.fetchWithTimeout(`${this.baseUrl}/llm/generate-ollama`, {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }

    /**
     * Get task status and result
     */
    async getTaskStatus(taskId) {
        return this.fetchWithTimeout(`${this.baseUrl}/llm/jobs/${taskId}`);
    }

    /**
     * Get chat history status
     */
    async getChatHistoryStatus(storyChatHistoryId) {
        return this.fetchWithTimeout(`${this.baseUrl}/llm/chat_history_status/${storyChatHistoryId}`);
    }

    /**
     * Get chat history details
     */
    async getChatHistory(storyChatHistoryId) {
        return this.fetchWithTimeout(`${this.baseUrl}/llm/chat_history/${storyChatHistoryId}`);
    }

    /**
     * Get detailed task information
     */
    async getTaskDetails(taskId) {
        return this.fetchWithTimeout(`${this.baseUrl}/task/${taskId}/detailed`);
    }

    /**
     * List all active tasks
     */
    async getActiveTasks() {
        return this.fetchWithTimeout(`${this.baseUrl}/tasks`);
    }

    /**
     * Poll for task completion with exponential backoff
     */
    async pollTaskResult(taskId, options = {}) {
        const {
            maxAttempts = 60,
            initialDelay = 1000,
            maxDelay = 5000,
            backoffFactor = 1.2,
            onProgress = null
        } = options;

        let attempts = 0;
        let delay = initialDelay;

        return new Promise((resolve, reject) => {
            const poll = async () => {
                if (attempts >= maxAttempts) {
                    reject(new Error('Task polling timeout'));
                    return;
                }

                try {
                    const result = await this.getTaskStatus(taskId);
                    attempts++;

                    // Call progress callback if provided
                    if (onProgress) {
                        onProgress(result, attempts);
                    }

                    if (result.state === 'SUCCESS') {
                        resolve(result);
                    } else if (result.state === 'FAILURE') {
                        reject(new Error(result.error || 'Task failed'));
                    } else if (result.state === 'PENDING' || result.state === 'PROGRESS') {
                        // Continue polling with exponential backoff
                        delay = Math.min(delay * backoffFactor, maxDelay);
                        setTimeout(poll, delay);
                    } else {
                        // Unknown state, continue polling
                        setTimeout(poll, delay);
                    }
                } catch (error) {
                    if (attempts >= maxAttempts) {
                        reject(error);
                    } else {
                        // Retry on network errors
                        setTimeout(poll, delay);
                    }
                }
            };

            // Start polling
            poll();
        });
    }

    /**
     * Poll for chat history status completion with exponential backoff
     */
    async pollChatHistoryStatus(storyChatHistoryId, options = {}) {
        const {
            maxAttempts = 60,
            initialDelay = 1000,
            maxDelay = 5000,
            backoffFactor = 1.2,
            onProgress = null
        } = options;

        let attempts = 0;
        let delay = initialDelay;

        return new Promise((resolve, reject) => {
            const poll = async () => {
                if (attempts >= maxAttempts) {
                    reject(new Error('Chat history status polling timeout'));
                    return;
                }

                try {
                    const result = await this.getChatHistoryStatus(storyChatHistoryId);
                    attempts++;

                    // Call progress callback if provided
                    if (onProgress) {
                        onProgress(result, attempts);
                    }

                    // Check if the status indicates completion
                    if (result.status === 'completed') {
                        // Fetch the full chat history details
                        try {
                            const chatHistory = await this.getChatHistory(storyChatHistoryId);
                            resolve({
                                ...result,
                                chatHistory: chatHistory
                            });
                        } catch (historyError) {
                            console.error('Failed to fetch chat history details:', historyError);
                            // Still resolve with the status result if history fetch fails
                            resolve(result);
                        }
                    } else if (result.status === 'failed') {
                        reject(new Error(result.error_message || 'Chat history processing failed'));
                    } else if (result.status === 'pending' || result.status === 'processing') {
                        // Continue polling with exponential backoff
                        delay = Math.min(delay * backoffFactor, maxDelay);
                        setTimeout(poll, delay);
                    } else {
                        // Unknown status, continue polling
                        setTimeout(poll, delay);
                    }
                } catch (error) {
                    if (attempts >= maxAttempts) {
                        reject(error);
                    } else {
                        // Retry on network errors
                        setTimeout(poll, delay);
                    }
                }
            };

            // Start polling
            poll();
        });
    }

    /**
     * Batch request helper for multiple API calls
     */
    async batchRequest(requests) {
        try {
            const promises = requests.map(request => 
                this.fetchWithTimeout(request.url, request.options)
            );
            return await Promise.allSettled(promises);
        } catch (error) {
            throw new Error(`Batch request failed: ${error.message}`);
        }
    }

    /**
     * Upload file (if needed for future features)
     */
    async uploadFile(file, endpoint = '/upload') {
        const formData = new FormData();
        formData.append('file', file);

        return fetch(`${this.baseUrl}${endpoint}`, {
            method: 'POST',
            body: formData
        }).then(response => {
            if (!response.ok) {
                throw new Error(`Upload failed: ${response.statusText}`);
            }
            return response.json();
        });
    }

    /**
     * Get server configuration/info
     */
    async getServerInfo() {
        return this.fetchWithTimeout(`${this.baseUrl}/`);
    }

    /**
     * Validate request payload
     */
    validateChatRequest(request) {
        if (!request.message || typeof request.message !== 'string') {
            throw new Error('Message is required and must be a string');
        }
        if (request.message.trim().length === 0) {
            throw new Error('Message cannot be empty');
        }
        if (request.message.length > 4000) {
            throw new Error('Message too long (max 4000 characters)');
        }
        return true;
    }

    /**
     * Format error message for user display
     */
    formatError(error) {
        if (error.message.includes('timeout')) {
            return 'Request timed out. Please try again.';
        }
        if (error.message.includes('HTTP 500')) {
            return 'Server error. Please try again later.';
        }
        if (error.message.includes('HTTP 404')) {
            return 'Service not found. Please check your connection.';
        }
        if (error.message.includes('Failed to fetch')) {
            return 'Connection failed. Please check your internet connection.';
        }
        return error.message || 'An unexpected error occurred';
    }
}

// Export for use in other modules
window.ApiService = ApiService;
