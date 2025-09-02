// FeelSync Dashboard Module

const dashboard = {
    chartInstance: null,
    updateInterval: null,

    // Initialize dashboard
    init() {
        this.updateStats();
        this.renderMoodChart();
        this.renderRecentEntries();
        this.renderQuickActions();
        this.renderInsights();
        this.setupEventListeners();
        this.startAutoUpdate();
    },

    // Setup event listeners
    setupEventListeners() {
        // Quick mood buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('quick-mood-btn')) {
                const moodId = e.target.dataset.mood;
                this.quickMoodEntry(moodId);
            }
        });

        // Chart period selector
        const periodSelector = document.getElementById('chart-period');
        if (periodSelector) {
            periodSelector.addEventListener('change', () => {
                this.renderMoodChart();
            });
        }
    },

    // Update dashboard statistics
    updateStats() {
        const stats = moodTracker.getMoodStats();
        const user = FeelSync.currentUser;

        // Update welcome message
        const welcomeEl = document.getElementById('welcome-message');
        if (welcomeEl && user) {
            const hour = new Date().getHours();
            let greeting = 'Good morning';
            if (hour >= 12 && hour < 17) greeting = 'Good afternoon';
            else if (hour >= 17) greeting = 'Good evening';
            
            welcomeEl.textContent = `${greeting}, ${user.name}!`;
        }

        if (!stats) {
            this.renderEmptyState();
            return;
        }

        // Update stat cards
        this.updateStatCard('current-streak', stats.streak, 'days');
        this.updateStatCard('total-entries', stats.totalEntries, 'entries');
        this.updateStatCard('week-average', stats.averageMood.toFixed(1), '/5.0');
        this.updateStatCard('longest-streak', stats.longestStreak, 'days');

        // Update mood trend
        const trendEl = document.getElementById('mood-trend');
        if (trendEl) {
            const trend = this.calculateMoodTrend();
            trendEl.innerHTML = `
                <div class="trend-indicator ${trend.direction}">
                    <span class="trend-icon">${trend.icon}</span>
                    <span class="trend-text">${trend.text}</span>
                </div>
            `;
        }

        // Update progress towards goals
        this.updateProgress();
    },

    // Update individual stat card
    updateStatCard(id, value, suffix = '') {
        const element = document.getElementById(id);
        if (element) {
            const valueEl = element.querySelector('.stat-value');
            const currentValue = parseInt(valueEl.textContent) || 0;
            
            // Animate number change
            this.animateNumber(valueEl, currentValue, value, suffix);
        }
    },

    // Animate number changes
    animateNumber(element, start, end, suffix = '') {
        const duration = 1000;
        const startTime = Date.now();
        
        const animate = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const current = Math.round(start + (end - start) * progress);
            
            element.textContent = current + suffix;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        animate();
    },

    // Calculate mood trend
    calculateMoodTrend() {
        const history = FeelSync.moodHistory;
        if (history.length < 2) {
            return { direction: 'neutral', icon: '→', text: 'Not enough data' };
        }

        const recent = history.slice(0, 3);
        const older = history.slice(3, 6);

        const recentAvg = recent.reduce((sum, entry) => sum + entry.mood.value, 0) / recent.length;
        const olderAvg = older.length > 0 ? older.reduce((sum, entry) => sum + entry.mood.value, 0) / older.length : recentAvg;

        const diff = recentAvg - olderAvg;

        if (diff > 0.3) {
            return { direction: 'up', icon: '↗️', text: 'Trending up' };
        } else if (diff < -0.3) {
            return { direction: 'down', icon: '↘️', text: 'Trending down' };
        } else {
            return { direction: 'stable', icon: '→', text: 'Stable' };
        }
    },

    // Update progress towards goals
    updateProgress() {
        const streakProgress = document.getElementById('streak-progress');
        const entriesProgress = document.getElementById('entries-progress');
        
        if (streakProgress) {
            const currentStreak = FeelSync.streakData.current;
            const streakGoal = 7; // Weekly goal
            const progress = Math.min((currentStreak / streakGoal) * 100, 100);
            
            streakProgress.innerHTML = `
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${progress}%"></div>
                </div>
                <div class="progress-text">${currentStreak}/${streakGoal} days this week</div>
            `;
        }

        if (entriesProgress) {
            const thisWeek = FeelSync.moodHistory.filter(entry => {
                const entryDate = new Date(entry.date);
                const weekAgo = new Date();
                weekAgo.setDate(weekAgo.getDate() - 7);
                return entryDate >= weekAgo;
            }).length;
            
            const weeklyGoal = 7;
            const progress = Math.min((thisWeek / weeklyGoal) * 100, 100);
            
            entriesProgress.innerHTML = `
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${progress}%"></div>
                </div>
                <div class="progress-text">${thisWeek}/${weeklyGoal} entries this week</div>
            `;
        }
    },

    // Render mood chart
    renderMoodChart() {
        const canvas = document.getElementById('mood-chart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const period = document.getElementById('chart-period')?.value || '7days';
        
        // Clear previous chart
        if (this.chartInstance) {
            this.chartInstance.destroy();
        }

        const chartData = this.getMoodChartData(period);
        
        // Simple canvas-based chart
        this.drawMoodChart(ctx, chartData);
    },

    // Get chart data based on period
    getMoodChartData(period) {
        const history = FeelSync.moodHistory;
        const now = new Date();
        let days = 7;
        
        switch (period) {
            case '7days':
                days = 7;
                break;
            case '30days':
                days = 30;
                break;
            case '90days':
                days = 90;
                break;
        }

        const data = [];
        for (let i = days - 1; i >= 0; i--) {
            const date = new Date(now);
            date.setDate(date.getDate() - i);
            date.setHours(0, 0, 0, 0);

            const dayEntries = history.filter(entry => {
                const entryDate = new Date(entry.date);
                entryDate.setHours(0, 0, 0, 0);
                return entryDate.getTime() === date.getTime();
            });

            const average = dayEntries.length > 0 
                ? dayEntries.reduce((sum, entry) => sum + entry.mood.value, 0) / dayEntries.length
                : null;

            data.push({
                date: date,
                average: average,
                count: dayEntries.length
            });
        }

        return data;
    },

    // Draw mood chart on canvas
    drawMoodChart(ctx, data) {
        const canvas = ctx.canvas;
        const width = canvas.width;
        const height = canvas.height;
        
        // Clear canvas
        ctx.clearRect(0, 0, width, height);
        
        // Chart settings
        const padding = 40;
        const chartWidth = width - padding * 2;
        const chartHeight = height - padding * 2;
        
        // Draw background
        ctx.fillStyle = '#f8fafc';
        ctx.fillRect(0, 0, width, height);
        
        // Draw grid
        ctx.strokeStyle = '#e2e8f0';
        ctx.lineWidth = 1;
        
        // Horizontal grid lines
        for (let i = 0; i <= 5; i++) {
            const y = padding + (i * chartHeight / 5);
            ctx.beginPath();
            ctx.moveTo(padding, y);
            ctx.lineTo(width - padding, y);
            ctx.stroke();
            
            // Y-axis labels
            ctx.fillStyle = '#64748b';
            ctx.font = '12px Inter';
            ctx.textAlign = 'right';
            ctx.fillText((5 - i).toString(), padding - 10, y + 4);
        }
        
        // Filter data points that have values
        const validData = data.filter(d => d.average !== null);
        if (validData.length === 0) return;
        
        // Draw line
        ctx.strokeStyle = '#667eea';
        ctx.lineWidth = 3;
        ctx.beginPath();
        
        validData.forEach((point, index) => {
            const x = padding + (index * chartWidth / (validData.length - 1));
            const y = padding + chartHeight - (point.average * chartHeight / 5);
            
            if (index === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        
        ctx.stroke();
        
        // Draw data points
        validData.forEach((point, index) => {
            const x = padding + (index * chartWidth / (validData.length - 1));
            const y = padding + chartHeight - (point.average * chartHeight / 5);
            
            ctx.fillStyle = '#667eea';
            ctx.beginPath();
            ctx.arc(x, y, 4, 0, 2 * Math.PI);
            ctx.fill();
            
            // Draw point label on hover (simplified)
            if (point.count > 0) {
                ctx.fillStyle = '#1f2937';
                ctx.font = '10px Inter';
                ctx.textAlign = 'center';
                ctx.fillText(point.average.toFixed(1), x, y - 10);
            }
        });
        
        // Draw x-axis labels
        ctx.fillStyle = '#64748b';
        ctx.font = '11px Inter';
        ctx.textAlign = 'center';
        
        const labelStep = Math.max(1, Math.floor(data.length / 7));
        data.forEach((point, index) => {
            if (index % labelStep === 0) {
                const x = padding + (index * chartWidth / (data.length - 1));
                const label = point.date.getDate().toString();
                ctx.fillText(label, x, height - 10);
            }
        });
    },

    // Render recent mood entries
    renderRecentEntries() {
        const container = document.getElementById('recent-entries');
        if (!container) return;

        const recentEntries = FeelSync.moodHistory.slice(0, 5);
        
        if (recentEntries.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>No mood entries yet. Start tracking your mood to see insights here!</p>
                    <button class="btn btn-primary" data-nav="mood">Track Your Mood</button>
                </div>
            `;
            return;
        }

        container.innerHTML = recentEntries.map(entry => `
            <div class="recent-entry">
                <div class="entry-mood">
                    <span class="mood-emoji">${entry.mood.emoji}</span>
                    <span class="mood-label">${entry.mood.label}</span>
                </div>
                <div class="entry-details">
                    <div class="entry-time">${utils.formatTime(entry.date)}</div>
                    <div class="entry-date">${utils.formatDate(entry.date)}</div>
                    ${entry.note ? `<div class="entry-note">"${entry.note.substring(0, 50)}${entry.note.length > 50 ? '...' : ''}"</div>` : ''}
                </div>
                <div class="entry-intensity">
                    <div class="intensity-bar">
                        <div class="intensity-fill" style="width: ${entry.intensity * 10}%"></div>
                    </div>
                    <span class="intensity-text">${entry.intensity}/10</span>
                </div>
            </div>
        `).join('');
    },

    // Render quick actions
    renderQuickActions() {
        const container = document.getElementById('quick-actions');
        if (!container) return;

        const quickMoods = [
            { id: 'happy', emoji: '😊', label: 'Happy' },
            { id: 'neutral', emoji: '😐', label: 'Neutral' },
            { id: 'sad', emoji: '😢', label: 'Sad' }
        ];

        container.innerHTML = `
            <div class="quick-actions-section">
                <h3>Quick Mood Check-in</h3>
                <div class="quick-mood-buttons">
                    ${quickMoods.map(mood => `
                        <button class="quick-mood-btn" data-mood="${mood.id}">
                            <span class="mood-emoji">${mood.emoji}</span>
                            <span class="mood-label">${mood.label}</span>
                        </button>
                    `).join('')}
                </div>
            </div>
            
            <div class="action-buttons">
                <button class="action-btn" data-nav="mood">
                    <span class="btn-icon">📝</span>
                    <span>Detailed Entry</span>
                </button>
                <button class="action-btn" data-nav="games">
                    <span class="btn-icon">🎮</span>
                    <span>Play Games</span>
                </button>
                <button class="action-btn" data-nav="insights">
                    <span class="btn-icon">📊</span>
                    <span>View Insights</span>
                </button>
            </div>
        `;
    },

    // Quick mood entry
    quickMoodEntry(moodId) {
        const mood = moodTracker.moods.find(m => m.id === moodId);
        if (!mood) return;

        const moodEntry = {
            id: utils.generateId(),
            mood: mood,
            note: '',
            intensity: 5,
            factors: [],
            date: new Date().toISOString(),
            timestamp: Date.now()
        };

        // Save to history
        FeelSync.moodHistory.unshift(moodEntry);
        utils.saveToStorage('feelSyncMoodHistory', FeelSync.moodHistory);

        // Update streak
        moodTracker.updateStreak();

        // Show success message
        utils.showNotification(`Quick ${mood.label} mood logged! 🎉`, 'success');

        // Update dashboard
        this.updateStats();
        this.renderMoodChart();
        this.renderRecentEntries();
    },

    // Render insights and recommendations
    renderInsights() {
        const container = document.getElementById('dashboard-insights');
        if (!container) return;

        const stats = moodTracker.getMoodStats();
        if (!stats || stats.totalEntries < 3) {
            container.innerHTML = `
                <div class="insight-card">
                    <h4>🌱 Getting Started</h4>
                    <p>Track your mood for a few more days to unlock personalized insights and patterns!</p>
                </div>
            `;
            return;
        }

        const insights = this.generateInsights(stats);
        
        container.innerHTML = insights.map(insight => `
            <div class="insight-card ${insight.type}">
                <h4>${insight.icon} ${insight.title}</h4>
                <p>${insight.description}</p>
                ${insight.action ? `<button class="insight-action" ${insight.action.attribute}>${insight.action.text}</button>` : ''}
            </div>
        `).join('');
    },

    // Generate personalized insights
    generateInsights(stats) {
        const insights = [];

        // Streak insights
        if (stats.streak >= 7) {
            insights.push({
                type: 'positive',
                icon: '🔥',
                title: 'Amazing Streak!',
                description: `You've been consistent for ${stats.streak} days! Keep up the great work.`,
                action: null
            });
        } else if (stats.streak === 0) {
            insights.push({
                type: 'motivational',
                icon: '💪',
                title: 'Start Your Streak',
                description: 'Regular mood tracking helps build self-awareness. Try to check in daily!',
                action: { text: 'Track Mood Now', attribute: 'data-nav="mood"' }
            });
        }

        // Mood trend insights
        const trend = this.calculateMoodTrend();
        if (trend.direction === 'up') {
            insights.push({
                type: 'positive',
                icon: '📈',
                title: 'Positive Trend',
                description: 'Your mood has been improving lately. What\'s been working well for you?',
                action: null
            });
        } else if (trend.direction === 'down') {
            insights.push({
                type: 'supportive',
                icon: '🤗',
                title: 'Gentle Reminder',
                description: 'It looks like you\'ve been having some tough days. Consider trying our breathing exercises or games.',
                action: { text: 'Try Games', attribute: 'data-nav="games"' }
            });
        }

        // Weekly activity insights
        if (stats.weekEntries < 3) {
            insights.push({
                type: 'motivational',
                icon: '⏰',
                title: 'More Check-ins',
                description: 'You\'ve logged fewer moods this week. Regular tracking provides better insights!',
                action: { text: 'Set Reminder', attribute: 'onclick="dashboard.setReminder()"' }
            });
        }

        // Factor-based insights
        if (stats.topFactors.length > 0) {
            insights.push({
                type: 'informational',
                icon: '🎯',
                title: 'Key Influences',
                description: `Your mood is often influenced by: ${stats.topFactors.join(', ')}. Consider focusing on these areas.`,
                action: null
            });
        }

        // Achievement insights
        if (stats.totalEntries >= 30) {
            insights.push({
                type: 'achievement',
                icon: '🏆',
                title: '30-Day Milestone',
                description: 'Congratulations on tracking your mood for over a month! You\'re building great habits.',
                action: null
            });
        }

        return insights.slice(0, 3); // Show max 3 insights
    },

    // Set mood reminder
    setReminder() {
        const time = prompt('What time would you like to be reminded? (e.g., 20:00)', FeelSync.settings.reminderTime);
        if (time && time.match(/^\d{2}:\d{2}$/)) {
            FeelSync.settings.reminderTime = time;
            utils.saveToStorage('feelSyncSettings', FeelSync.settings);
            utils.showNotification(`Reminder set for ${time} daily!`, 'success');
        }
    },

    // Render empty state
    renderEmptyState() {
        const statsContainer = document.querySelector('.dashboard-stats');
        if (statsContainer) {
            statsContainer.innerHTML = `
                <div class="empty-dashboard">
                    <div class="empty-icon">📊</div>
                    <h3>Welcome to FeelSync!</h3>
                    <p>Start tracking your mood to see personalized insights and statistics here.</p>
                    <button class="btn btn-primary btn-large" data-nav="mood">Track Your First Mood</button>
                </div>
            `;
        }
    },

    // Start auto-update interval
    startAutoUpdate() {
        // Update dashboard every 5 minutes
        this.updateInterval = setInterval(() => {
            this.updateStats();
            this.renderRecentEntries();
        }, 5 * 60 * 1000);
    },

    // Stop auto-update
    stopAutoUpdate() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    },

    // Clean up when leaving dashboard
    cleanup() {
        this.stopAutoUpdate();
        if (this.chartInstance) {
            this.chartInstance.destroy();
            this.chartInstance = null;
        }
    }
};

// Export dashboard module
window.dashboard = dashboard;
