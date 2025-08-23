/**
 * MateHub Frontend Application
 * Main script that initializes the chat client and handles UI interactions
 */

// Global variables
let chatClient = null;
let configPanelVisible = true;

/**
 * Initialize the application when DOM is loaded
 */
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

/**
 * Initialize the application
 */
function initializeApp() {
    try {
        // Initialize chat client
        chatClient = new ChatClient();
        
        // Setup configuration panel
        setupConfigPanel();
        
        // Setup API buttons
        setupApiButtons();
        
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
    const toggleBtn = document.getElementById('toggleConfig');
    const configPanel = document.getElementById('configPanel');
    
    if (toggleBtn && configPanel) {
        toggleBtn.addEventListener('click', () => {
            configPanelVisible = !configPanelVisible;
            
            if (configPanelVisible) {
                configPanel.classList.remove('hidden');
                toggleBtn.textContent = 'Hide';
            } else {
                configPanel.classList.add('hidden');
                toggleBtn.textContent = 'Show';
            }
        });
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
        const inputId = `${type}IdInput`;
        const currentId = `current${type.charAt(0).toUpperCase() + type.slice(1)}Id`;
        
        const input = document.getElementById(inputId);
        const current = document.getElementById(currentId);
        
        if (input && current) {
            const value = parseInt(input.value);
            if (chatClient.updateId(type, value)) {
                current.textContent = value;
                input.value = value; // Reset input to valid value
            } else {
                input.value = current.textContent; // Reset to current value
            }
        }
    };
    
    // Add Enter key support for ID inputs
    ['user', 'character', 'story', 'phrase'].forEach(type => {
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
    getConfig: () => chatClient?.config,
    getHistory: () => chatClient?.conversationHistory,
    clearStorage: () => {
        localStorage.removeItem('matehub-config');
        location.reload();
    },
    testApi: async () => {
        if (!chatClient) return 'Chat client not initialized';
        try {
            const health = await chatClient.apiService.checkLlmHealth();
            return health;
        } catch (error) {
            return { error: error.message };
        }
    }
};

// Export for potential module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initializeApp,
        setupConfigPanel,
        setupApiButtons,
        setupIdUpdates
    };
}
