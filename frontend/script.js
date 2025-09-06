class TradingAgentUI {
    constructor() {
        this.isLoggedIn = false;
        this.isProcessing = false;
        this.initializeLoginListeners();
        this.savedStocks = this.loadSavedStocks();
        // Lazy loading for chat messages
        this.messagesPerPage = 20;
        this.currentMessageOffset = 0;
        this.totalMessages = 0;
    }
    
    initializeApp() {
        this.chatMessages = document.getElementById('chatMessages');
        this.chatInput = document.getElementById('chatInput');
        this.sendButton = document.getElementById('sendButton');
        
        this.initializeEventListeners();
        this.loadChatHistory();
        this.loadSavedStockCards();
    }
    
    initializeLoginListeners() {
        const loginButton = document.getElementById('loginButton');
        const apiKeyInput = document.getElementById('apiKeyInput');
        const loginError = document.getElementById('loginError');
        
        loginButton.addEventListener('click', () => this.handleLogin());
        apiKeyInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleLogin();
            }
        });
    }
    
    async handleLogin() {
        const apiKeyInput = document.getElementById('apiKeyInput');
        const loginButton = document.getElementById('loginButton');
        const loginButtonText = document.getElementById('loginButtonText');
        const loginSpinner = document.getElementById('loginSpinner');
        const loginError = document.getElementById('loginError');
        
        const apiKey = apiKeyInput.value.trim();
        
        if (!apiKey) {
            this.showLoginError('Please enter your API key');
            return;
        }
        
        // Show loading state
        loginButton.disabled = true;
        loginButtonText.style.display = 'none';
        loginSpinner.style.display = 'block';
        loginError.style.display = 'none';
        
        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ apiKey })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.isLoggedIn = true;
                this.showMainApp();
                this.initializeApp();
            } else {
                this.showLoginError(data.error);
            }
        } catch (error) {
            this.showLoginError(`Connection error: ${error.message}`);
        } finally {
            // Reset loading state
            loginButton.disabled = false;
            loginButtonText.style.display = 'block';
            loginSpinner.style.display = 'none';
        }
    }
    
    showLoginError(message) {
        const loginError = document.getElementById('loginError');
        loginError.textContent = message;
        loginError.style.display = 'block';
    }
    
    showMainApp() {
        document.getElementById('loginContainer').style.display = 'none';
        document.getElementById('mainContainer').style.display = 'flex';
    }
    
    async handleLogout() {
        try {
            await fetch('/api/logout', { method: 'POST' });
            this.isLoggedIn = false;
            document.getElementById('loginContainer').style.display = 'flex';
            document.getElementById('mainContainer').style.display = 'none';
            document.getElementById('apiKeyInput').value = '';
            this.clearChatHistory();
        } catch (error) {
            console.error('Logout error:', error);
        }
    }

    initializeEventListeners() {
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
        
        // Clear chat button
        const clearChatBtn = document.getElementById('clearChatBtn');
        if (clearChatBtn) {
            clearChatBtn.addEventListener('click', () => {
                if (confirm('Clear all chat history?')) {
                    this.clearChatHistory();
                }
            });
        }
        
        // Logout button
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                if (confirm('Are you sure you want to logout?')) {
                    this.handleLogout();
                }
            });
        }
    }

    async sendMessage() {
        const message = this.chatInput.value.trim();
        if (!message || this.isProcessing) return;

        // Disable input while processing
        this.setProcessingState(true);
        
        this.addMessage(message, 'user');
        this.chatInput.value = '';
        
        // Show thinking message with loading indicator
        const thinkingMessage = this.addMessage('🧠 Analyzing with Dan Zanger methodology and fetching live market data...', 'system');
        this.addLoadingIndicator(thinkingMessage);
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message })
            });
            
            const data = await response.json();
            
            // Remove thinking message
            this.removeMessage(thinkingMessage);
            
            if (data.success) {
                this.handleAnalysisResponse(data.analysis);
            } else {
                this.addMessage(`❌ Error: ${data.error}`, 'system');
            }
        } catch (error) {
            this.removeMessage(thinkingMessage);
            this.addMessage(`❌ Connection error: ${error.message}`, 'system');
        } finally {
            // Re-enable input
            this.setProcessingState(false);
        }
    }

    addMessage(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        
        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = this.formatTime(new Date());
        
        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(timeDiv);
        
        this.chatMessages.appendChild(messageDiv);
        setTimeout(() => {
            messageDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }, 10);
        
        // Save to localStorage
        this.saveChatHistory();
        
        return messageDiv;
    }

    addSectionedMessage(title, content) {
        console.log('Adding section:', title, 'Content:', content); // Debug
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system sectioned';
        
        const titleDiv = document.createElement('div');
        titleDiv.className = 'section-title';
        titleDiv.textContent = title;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'section-content';
        // Simple test - just show the content directly first
        contentDiv.textContent = content;
        
        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = this.formatTime(new Date());
        
        messageDiv.appendChild(titleDiv);
        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(timeDiv);
        
        this.chatMessages.appendChild(messageDiv);
        setTimeout(() => {
            messageDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }, 10);
    }

    handleAnalysisResponse(analysis) {
        // Simple response with spacing between sections
        const response = 
            `📊 ANALYSIS SUMMARY\n${analysis.analysis_summary}\n\n` +
            `📈 MARKET DATA\n` +
            `Current Price: ${analysis.current_data.price}\n` +
            `Volume vs Average: ${analysis.current_data.volume_vs_avg}\n` +
            `Earnings Growth: ${analysis.current_data.earnings_growth}\n` +
            `Sector Performance: ${analysis.current_data.sector_performance}\n\n` +
            `🔍 ZANGER METHODOLOGY\n` +
            `Pattern Type: ${analysis.zanger_analysis.pattern_type}\n` +
            `Volume Ratio: ${analysis.zanger_analysis.volume_ratio}\n` +
            `Breakout Level: ${analysis.zanger_analysis.breakout_level}\n` +
            `Meets Criteria: ${analysis.zanger_analysis.meets_zanger_criteria}\n\n` +
            `🎯 RECOMMENDATION: ${analysis.recommendation.action}\n` +
            `Confidence: ${analysis.recommendation.confidence}\n` +
            `Reasoning: ${analysis.recommendation.reasoning}\n\n` +
            `💼 TRADING SETUP\n` +
            `Entry Price: ${analysis.trading_details.entry_price}\n` +
            `Stop Loss: ${analysis.trading_details.stop_loss}\n` +
            `Target Price: ${analysis.trading_details.target_price}\n` +
            `Position Size: ${analysis.trading_details.position_size}\n` +
            `Time Horizon: ${analysis.trading_details.time_horizon}\n\n` +
            `⚠️ RISK ASSESSMENT\n` +
            `Risk Level: ${analysis.risk_assessment.risk_level}\n` +
            `Risk/Reward Ratio: ${analysis.risk_assessment.risk_reward_ratio}\n` +
            `Key Risks: ${analysis.risk_assessment.key_risks.join(', ')}`;
            
        this.addMessage(response, 'system');
        
        // Update stock overview panel with stock data
        if (analysis.symbols_analyzed && analysis.symbols_analyzed.length > 0) {
            this.updateStockOverview(analysis);
        }
    }
    
    updateStockOverview(analysis) {
        const tradingContent = document.querySelector('.trading-content');
        
        // Remove empty state if it exists
        const emptyState = tradingContent.querySelector('.empty-state');
        if (emptyState) {
            emptyState.remove();
        }
        
        // Get stock symbol
        const symbol = analysis.symbols_analyzed[0];
        
        // Check if we already have a stock card for this symbol
        const existingCard = tradingContent.querySelector(`[data-symbol="${symbol}"]`);
        
        if (existingCard) {
            // Update existing card and ensure it's expanded
            this.updateStockCard(existingCard, analysis, symbol);
            
            // Expand the card if it's collapsed
            const details = existingCard.querySelector('.stock-details');
            const toggleIcon = existingCard.querySelector('.toggle-icon');
            if (details.classList.contains('collapsed')) {
                details.classList.remove('collapsed');
                toggleIcon.textContent = '▼';
                this.saveStock(symbol, false);
            }
            
            // Update timestamp
            const lastUpdated = existingCard.querySelector('.last-updated');
            lastUpdated.textContent = `Updated: ${new Date().toLocaleTimeString()}`;
        } else {
            // Create new stock card
            const newCard = this.createStockCard(analysis, symbol);
            tradingContent.appendChild(newCard);
        }
    }
    
    updateStockCard(card, analysis, symbol) {
        // Extract financial data from the analysis
        // We need to parse this from the current_data or get it from the backend
        const currentData = analysis.current_data;
        
        card.querySelector('.symbol').textContent = symbol;
        
        const rows = card.querySelectorAll('.detail-row');
        if (rows[0]) rows[0].querySelector('.value').textContent = currentData.price || 'N/A';
        if (rows[1]) rows[1].querySelector('.value').textContent = 'N/A'; // P/E ratio
        if (rows[2]) rows[2].querySelector('.value').textContent = 'N/A'; // Market cap
        if (rows[3]) rows[3].querySelector('.value').textContent = 'N/A'; // 52-week range
        if (rows[4]) rows[4].querySelector('.value').textContent = 'N/A'; // Quarterly EPS
    }
    
    createStockCard(analysis, symbol) {
        const currentData = analysis.current_data;
        const card = document.createElement('div');
        card.className = 'stock-card';
        card.setAttribute('data-symbol', symbol);
        
        const isCollapsed = this.savedStocks[symbol]?.collapsed || false;
        
        card.innerHTML = `
            <div class="stock-header">
                <div class="stock-header-left">
                    <span class="symbol">${symbol}</span>
                    <span class="last-updated">Updated: ${new Date().toLocaleTimeString()}</span>
                </div>
                <button class="toggle-btn">
                    <span class="toggle-icon">${isCollapsed ? '▶' : '▼'}</span>
                </button>
            </div>
            <div class="stock-details ${isCollapsed ? 'collapsed' : ''}">
                <div class="detail-row">
                    <span class="label">Current Price:</span>
                    <span class="value">${currentData.price || 'N/A'}</span>
                </div>
                <div class="detail-row">
                    <span class="label">P/E Ratio:</span>
                    <span class="value">Loading...</span>
                </div>
                <div class="detail-row">
                    <span class="label">Market Cap:</span>
                    <span class="value">Loading...</span>
                </div>
                <div class="detail-row">
                    <span class="label">52-Week Range:</span>
                    <span class="value">Loading...</span>
                </div>
                <div class="detail-row">
                    <span class="label">Quarterly EPS:</span>
                    <span class="value">Loading...</span>
                </div>
                <button class="remove-stock-btn">
                    ✕ Remove
                </button>
            </div>
        `;
        
        // Add event listeners for toggle functionality
        const toggleBtn = card.querySelector('.toggle-btn');
        const removeBtn = card.querySelector('.remove-stock-btn');
        
        toggleBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleStockCard(card);
        });
        
        removeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.removeStockCard(symbol);
        });
        
        // Make header clickable for toggle
        card.querySelector('.stock-header').addEventListener('click', (e) => {
            if (e.target !== toggleBtn && e.target !== removeBtn) {
                this.toggleStockCard(card);
            }
        });
        
        // Fetch detailed financial data for this stock
        this.loadDetailedStockData(symbol, card);
        
        // Save this stock
        this.saveStock(symbol);
        
        return card;
    }
    
    async loadDetailedStockData(symbol, card) {
        try {
            const response = await fetch('/api/stock-data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ symbol })
            });
            
            const data = await response.json();
            
            if (data.success) {
                const stockData = data.data;
                const rows = card.querySelectorAll('.detail-row');
                
                // Update Current Price
                if (rows[0]) {
                    rows[0].querySelector('.value').textContent = 
                        stockData.current_price ? `$${stockData.current_price}` : 'N/A';
                }
                
                // Update P/E Ratio
                if (rows[1]) {
                    rows[1].querySelector('.value').textContent = 
                        stockData.pe_ratio ? stockData.pe_ratio.toFixed(2) : 'N/A';
                }
                
                // Update Market Cap
                if (rows[2]) {
                    const marketCap = stockData.market_cap;
                    let formattedCap = 'N/A';
                    if (marketCap) {
                        if (marketCap >= 1e12) {
                            formattedCap = `$${(marketCap / 1e12).toFixed(2)}T`;
                        } else if (marketCap >= 1e9) {
                            formattedCap = `$${(marketCap / 1e9).toFixed(2)}B`;
                        } else if (marketCap >= 1e6) {
                            formattedCap = `$${(marketCap / 1e6).toFixed(2)}M`;
                        } else {
                            formattedCap = `$${marketCap.toLocaleString()}`;
                        }
                    }
                    rows[2].querySelector('.value').textContent = formattedCap;
                }
                
                // Update 52-Week Range
                if (rows[3]) {
                    const low = stockData['52_week_low'];
                    const high = stockData['52_week_high'];
                    rows[3].querySelector('.value').textContent = 
                        (low && high) ? `$${low} - $${high}` : 'N/A';
                }
                
                // Update Quarterly EPS
                if (rows[4]) {
                    rows[4].querySelector('.value').textContent = 
                        stockData.quarterly_eps ? `$${stockData.quarterly_eps}` : 'N/A';
                }
            } else {
                // Show error in all fields
                const rows = card.querySelectorAll('.detail-row');
                for (let i = 1; i < rows.length; i++) {
                    rows[i].querySelector('.value').textContent = 'Error';
                }
            }
        } catch (error) {
            console.error('Error loading stock data:', error);
            // Show error in all fields
            const rows = card.querySelectorAll('.detail-row');
            for (let i = 1; i < rows.length; i++) {
                rows[i].querySelector('.value').textContent = 'Error';
            }
        }
    }
    
    createSummaryCard() {
        const card = document.createElement('div');
        card.className = 'summary-card';
        card.innerHTML = `
            <h3>Portfolio Summary</h3>
            <div class="summary-details">
                <div class="detail-row">
                    <span class="label">Total Positions:</span>
                    <span class="value" id="totalPositions">1</span>
                </div>
                <div class="detail-row">
                    <span class="label">Active Recommendations:</span>
                    <span class="value" id="activeRecs">1</span>
                </div>
                <div class="detail-row">
                    <span class="label">Last Updated:</span>
                    <span class="value" id="lastUpdated">${this.formatTime(new Date())}</span>
                </div>
            </div>
        `;
        return card;
    }

    formatTime(date) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    updatePositionData(positionData) {
        // This method can be used to update position data from backend
        console.log('Updating position data:', positionData);
    }

    updatePortfolioSummary(summaryData) {
        // This method can be used to update portfolio summary from backend
        console.log('Updating portfolio summary:', summaryData);
    }

    saveChatHistory() {
        const messages = Array.from(this.chatMessages.children).map(messageDiv => {
            const content = messageDiv.querySelector('.message-content').textContent;
            const time = messageDiv.querySelector('.message-time').textContent;
            const type = messageDiv.classList.contains('user') ? 'user' : 'system';
            return { content, time, type };
        });
        
        localStorage.setItem('tradingAgentChatHistory', JSON.stringify(messages));
    }

    loadChatHistory() {
        const savedHistory = localStorage.getItem('tradingAgentChatHistory');
        if (savedHistory) {
            try {
                const messages = JSON.parse(savedHistory);
                
                // Clear existing messages except the initial system message
                const systemMessage = this.chatMessages.querySelector('.message.system');
                this.chatMessages.innerHTML = '';
                if (systemMessage) {
                    this.chatMessages.appendChild(systemMessage);
                }
                
                // Restore saved messages
                messages.forEach(msg => {
                    if (msg.content !== 'Trading agent initialized. Ready to assist with your trading decisions.') {
                        this.restoreMessage(msg.content, msg.type, msg.time);
                    }
                });
                
                setTimeout(() => {
                    this.chatMessages.scrollTo({ top: this.chatMessages.scrollHeight, behavior: 'smooth' });
                }, 100);
            } catch (error) {
                console.error('Error loading chat history:', error);
            }
        }
    }

    restoreMessage(content, type, time) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        
        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = time;
        
        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(timeDiv);
        
        this.chatMessages.appendChild(messageDiv);
    }

    clearChatHistory() {
        localStorage.removeItem('tradingAgentChatHistory');
        location.reload(); // Refresh to show clean state
    }
    
    // Stock card persistence methods
    loadSavedStocks() {
        try {
            const saved = localStorage.getItem('tradingAgentStocks');
            return saved ? JSON.parse(saved) : {};
        } catch (error) {
            console.error('Error loading saved stocks:', error);
            return {};
        }
    }
    
    saveStock(symbol, collapsed = false) {
        this.savedStocks[symbol] = {
            symbol: symbol,
            collapsed: collapsed,
            timestamp: Date.now()
        };
        try {
            localStorage.setItem('tradingAgentStocks', JSON.stringify(this.savedStocks));
        } catch (error) {
            console.error('Error saving stock:', error);
        }
    }
    
    removeStockCard(symbol) {
        // Remove from DOM
        const card = document.querySelector(`[data-symbol="${symbol}"]`);
        if (card) {
            card.remove();
        }
        
        // Remove from saved stocks
        delete this.savedStocks[symbol];
        try {
            localStorage.setItem('tradingAgentStocks', JSON.stringify(this.savedStocks));
        } catch (error) {
            console.error('Error removing stock:', error);
        }
        
        // Show empty state if no cards left
        const tradingContent = document.querySelector('.trading-content');
        const hasCards = tradingContent.querySelector('.stock-card');
        if (!hasCards) {
            const emptyState = document.createElement('div');
            emptyState.className = 'empty-state';
            emptyState.innerHTML = `
                <div class="empty-icon">📈</div>
                <h3>No Stock Selected</h3>
                <p>Ask me about a specific stock to see detailed financial information</p>
            `;
            tradingContent.appendChild(emptyState);
        }
    }
    
    toggleStockCard(card) {
        const details = card.querySelector('.stock-details');
        const toggleIcon = card.querySelector('.toggle-icon');
        const symbol = card.getAttribute('data-symbol');
        
        const isCurrentlyCollapsed = details.classList.contains('collapsed');
        
        if (isCurrentlyCollapsed) {
            // Expand
            details.classList.remove('collapsed');
            toggleIcon.textContent = '▼';
            this.saveStock(symbol, false);
            
            // Refresh the stock data when expanding
            this.refreshStockData(symbol, card);
        } else {
            // Collapse
            details.classList.add('collapsed');
            toggleIcon.textContent = '▶';
            this.saveStock(symbol, true);
        }
    }
    
    async refreshStockData(symbol, card) {
        // Show loading state
        const rows = card.querySelectorAll('.detail-row');
        if (rows[0]) rows[0].querySelector('.value').textContent = 'Loading...';
        
        // Update timestamp
        const lastUpdated = card.querySelector('.last-updated');
        lastUpdated.textContent = `Updating...`;
        
        // Fetch fresh data
        await this.loadDetailedStockData(symbol, card);
        
        // Update timestamp
        lastUpdated.textContent = `Updated: ${new Date().toLocaleTimeString()}`;
    }
    
    loadSavedStockCards() {
        const tradingContent = document.querySelector('.trading-content');
        
        // Remove empty state
        const emptyState = tradingContent.querySelector('.empty-state');
        if (emptyState) {
            emptyState.remove();
        }
        
        // Load each saved stock
        Object.keys(this.savedStocks).forEach(symbol => {
            const stockInfo = this.savedStocks[symbol];
            
            // Create a minimal analysis object for the saved stock
            const mockAnalysis = {
                symbols_analyzed: [symbol],
                current_data: {
                    price: 'Loading...'
                }
            };
            
            // Create the card
            const card = this.createStockCard(mockAnalysis, symbol);
            tradingContent.appendChild(card);
            
            // If the card is expanded, immediately refresh data
            if (!stockInfo.collapsed) {
                this.refreshStockData(symbol, card);
            }
        });
    }

    setProcessingState(processing) {
        this.isProcessing = processing;
        this.chatInput.disabled = processing;
        this.sendButton.disabled = processing;
        
        // Update visual state
        if (processing) {
            this.chatInput.placeholder = "Processing your request...";
            this.sendButton.style.opacity = "0.5";
            this.chatInput.style.opacity = "0.5";
        } else {
            this.chatInput.placeholder = "Ask your trading agent anything...";
            this.sendButton.style.opacity = "1";
            this.chatInput.style.opacity = "1";
        }
    }

    addLoadingIndicator(messageElement) {
        const loadingDots = document.createElement('span');
        loadingDots.className = 'loading-dots';
        loadingDots.innerHTML = '<span>.</span><span>.</span><span>.</span>';
        
        const messageContent = messageElement.querySelector('.message-content');
        messageContent.appendChild(loadingDots);
    }

    removeMessage(messageElement) {
        if (messageElement && messageElement.parentNode) {
            messageElement.remove();
            this.saveChatHistory();
        }
    }
}

// Initialize the UI when the page loads
document.addEventListener('DOMContentLoaded', () => {
    const tradingUI = new TradingAgentUI();
    
    // Simulate real-time updates (optional)
    setInterval(() => {
        // This could connect to a websocket or API to get real-time data
        // tradingUI.updatePositionData(newData);
    }, 5000);
});