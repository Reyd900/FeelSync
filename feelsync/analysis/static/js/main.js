// FeelSync - Main JavaScript File

// Global application state
const FeelSync = {
    currentUser: null,
    currentMood: null,
    activities: [],
    streakData: {
        current: 0,
        longest: 0,
        lastCheckin: null
    },
    settings: {
        notifications: true,
        darkMode: false,
        reminderTime: '20:00'
    }
};

// Utility functions
const utils = {
    // Generate unique ID
    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    },

    // Format date
    formatDate(date) {
        return new Intl.DateTimeFormat('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        }).format(new Date(date));
    },

    // Format time
    formatTime(date) {
        return new Intl.DateTimeFormat('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        }).format(new Date(date));
    },

    // Calculate streak
    calculateStreak(entries) {
        if (!entries || entries.length === 0) return 0;

        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        let streak = 0;
        let currentDate = new Date(today);

        // Sort entries by date (newest first)
        const sortedEntries = entries.sort((a, b) => new Date(b.date) - new Date(a.date));

        for (let entry of sortedEntries) {
            const entryDate = new Date(entry.date);
            entryDate.setHours(0, 0, 0, 0);

            if (entryDate.getTime() === currentDate.getTime()) {
                streak++;
                currentDate.setDate(currentDate.getDate() - 1);
            } else if (entryDate.getTime() < currentDate.getTime()) {
                break;
            }
        }

        return streak;
    },

    // Show notification
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span>${message}</span>
            <button onclick="this.parentElement.remove()" class="notification-close">×</button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    },

    // Animate element
    animateElement(element, animation = 'fadeIn', duration = 300) {
        element.style.animation = `${animation} ${duration}ms ease`;
        
        setTimeout(() => {
            element.style.animation = '';
        }, duration);
    },

    // Validate form data
    validateForm(formData, rules) {
        const errors = {};
        
        for (let field in rules) {
            const value = formData[field];
            const rule = rules[field];
            
            if (rule.required && (!value || value.trim() === '')) {
                errors[field] = `${field} is required`;
            }
            
            if (value && rule.minLength && value.length < rule.minLength) {
                errors[field] = `${field} must be at least ${rule.minLength} characters`;
            }
            
            if (value && rule.email && !this.isValidEmail(value)) {
                errors[field] = 'Please enter a valid email address';
            }
        }
        
        return Object.keys(errors).length === 0 ? null : errors;
    },

    // Email validation
    isValidEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },

    // Local storage helpers
    saveToStorage(key, data) {
        try {
            localStorage.setItem(key, JSON.stringify(data));
            return true;
        } catch (error) {
            console.error('Error saving to localStorage:', error);
            return false;
        }
    },

    loadFromStorage(key, defaultValue = null) {
        try {
            const data = localStorage.getItem(key);
            return data ? JSON.parse(data) : defaultValue;
        } catch (error) {
            console.error('Error loading from localStorage:', error);
            return defaultValue;
        }
    }
};

// Mood tracking functionality
const moodTracker = {
    moods: [
        { id: 'ecstatic', label: 'Ecstatic', emoji: '🤩', value: 5, color: '#10B981' },
        { id: 'happy', label: 'Happy', emoji: '😊', value: 4, color: '#34D399' },
        { id: 'neutral', label: 'Neutral', emoji: '😐', value: 3, color: '#FCD34D' },
        { id: 'sad', label: 'Sad', emoji: '😢', value: 2, color: '#F87171' },
        { id: 'terrible', label: 'Terrible', emoji: '😭', value: 1, color: '#EF4444' }
    ],

    factors: [
        'Sleep Quality', 'Work Stress', 'Social Interaction', 'Exercise', 
        'Weather', 'Health', 'Family', 'Finances', 'Creativity', 'Food'
    ],

    // Initialize mood tracking
    init() {
        this.loadMoodHistory();
        this.renderMoodSelector();
        this.setupEventListeners();
    },

    // Load mood history from storage
    loadMoodHistory() {
        FeelSync.moodHistory = utils.loadFromStorage('feelSyncMoodHistory', []);
        this.updateStreak();
    },

    // Render mood selector
    renderMoodSelector() {
        const moodSelector = document.getElementById('mood-selector');
        if (!moodSelector) return;

        moodSelector.innerHTML = this.moods.map(mood => `
            <button class="mood-option" data-mood="${mood.id}" style="--mood-color: ${mood.color}">
                <span class="mood-emoji">${mood.emoji}</span>
                <span class="mood-label">${mood.label}</span>
            </button>
        `).join('');
    },

    // Setup event listeners
    setupEventListeners() {
        // Mood selection
        document.addEventListener('click', (e) => {
            if (e.target.closest('.mood-option')) {
                this.selectMood(e.target.closest('.mood-option'));
            }
        });

        // Mood submission
        const submitBtn = document.getElementById('submit-mood');
        if (submitBtn) {
            submitBtn.addEventListener('click', () => this.submitMood());
        }
    },

    // Select mood
    selectMood(moodElement) {
        // Remove previous selection
        document.querySelectorAll('.mood-option').forEach(el => el.classList.remove('selected'));
        
        // Add selection
        moodElement.classList.add('selected');
        FeelSync.currentMood = this.moods.find(m => m.id === moodElement.dataset.mood);
        
        // Show additional inputs
        this.showMoodDetails();
    },

    // Show mood details form
    showMoodDetails() {
        const detailsSection = document.getElementById('mood-details');
        if (!detailsSection) return;

        detailsSection.style.display = 'block';
        detailsSection.innerHTML = `
            <div class="mood-details-content">
                <h3>Tell us more about your ${FeelSync.currentMood.label.toLowerCase()} mood</h3>
                
                <div class="form-group">
                    <label for="mood-note">What's on your mind? (Optional)</label>
                    <textarea id="mood-note" placeholder="Share your thoughts, experiences, or what's affecting your mood..."></textarea>
                </div>

                <div class="form-group">
                    <label>What's influencing your mood today?</label>
                    <div class="mood-factors">
                        ${this.factors.map(factor => `
                            <label class="factor-option">
                                <input type="checkbox" value="${factor}">
                                <span>${factor}</span>
                            </label>
                        `).join('')}
                    </div>
                </div>

                <div class="form-group">
                    <label for="mood-intensity">Mood Intensity</label>
                    <div class="intensity-slider">
                        <input type="range" id="mood-intensity" min="1" max="10" value="5">
                        <div class="intensity-labels">
                            <span>Mild</span>
                            <span>Intense</span>
                        </div>
                    </div>
                </div>

                <button id="submit-mood" class="btn btn-primary">Save Mood Entry</button>
            </div>
        `;

        utils.animateElement(detailsSection, 'slideDown');
    },

    // Submit mood entry
    submitMood() {
        if (!FeelSync.currentMood) {
            utils.showNotification('Please select a mood first', 'error');
            return;
        }

        const note = document.getElementById('mood-note')?.value || '';
        const intensity = document.getElementById('mood-intensity')?.value || 5;
        const factors = Array.from(document.querySelectorAll('.factor-option input:checked')).map(cb => cb.value);

        const moodEntry = {
            id: utils.generateId(),
            mood: FeelSync.currentMood,
            note: note.trim(),
            intensity: parseInt(intensity),
            factors: factors,
            date: new Date().toISOString(),
            timestamp: Date.now()
        };

        // Save to history
        FeelSync.moodHistory.unshift(moodEntry);
        utils.saveToStorage('feelSyncMoodHistory', FeelSync.moodHistory);

        // Update streak
        this.updateStreak();

        // Show success message
        utils.showNotification('Mood entry saved successfully! 🎉', 'success');

        // Reset form
        this.resetMoodForm();

        // Update dashboard if visible
        if (window.dashboard) {
            dashboard.updateStats();
            dashboard.renderMoodChart();
        }
    },

    // Update streak calculation
    updateStreak() {
        const streak = utils.calculateStreak(FeelSync.moodHistory);
        FeelSync.streakData.current = streak;
        
        if (streak > FeelSync.streakData.longest) {
            FeelSync.streakData.longest = streak;
        }
        
        FeelSync.streakData.lastCheckin = FeelSync.moodHistory.length > 0 ? FeelSync.moodHistory[0].date : null;
        
        utils.saveToStorage('feelSyncStreakData', FeelSync.streakData);
    },

    // Reset mood form
    resetMoodForm() {
        document.querySelectorAll('.mood-option').forEach(el => el.classList.remove('selected'));
        const detailsSection = document.getElementById('mood-details');
        if (detailsSection) {
            detailsSection.style.display = 'none';
        }
        FeelSync.currentMood = null;
    },

    // Get mood statistics
    getMoodStats() {
        const history = FeelSync.moodHistory;
        if (history.length === 0) return null;

        const last7Days = history.filter(entry => {
            const entryDate = new Date(entry.date);
            const weekAgo = new Date();
            weekAgo.setDate(weekAgo.getDate() - 7);
            return entryDate >= weekAgo;
        });

        const averageMood = last7Days.reduce((sum, entry) => sum + entry.mood.value, 0) / last7Days.length;
        const averageIntensity = last7Days.reduce((sum, entry) => sum + entry.intensity, 0) / last7Days.length;

        // Find most common factors
        const factorCounts = {};
        last7Days.forEach(entry => {
            entry.factors.forEach(factor => {
                factorCounts[factor] = (factorCounts[factor] || 0) + 1;
            });
        });

        const topFactors = Object.entries(factorCounts)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 3)
            .map(([factor]) => factor);

        return {
            totalEntries: history.length,
            weekEntries: last7Days.length,
            averageMood: Math.round(averageMood * 10) / 10,
            averageIntensity: Math.round(averageIntensity * 10) / 10,
            streak: FeelSync.streakData.current,
            longestStreak: FeelSync.streakData.longest,
            topFactors: topFactors
        };
    }
};

// Navigation functionality
const navigation = {
    currentPage: 'dashboard',

    init() {
        this.setupEventListeners();
        this.updateActiveNavigation();
    },

    setupEventListeners() {
        // Navigation links
        document.addEventListener('click', (e) => {
            if (e.target.closest('[data-nav]')) {
                e.preventDefault();
                const target = e.target.closest('[data-nav]').dataset.nav;
                this.navigateTo(target);
            }
        });

        // Handle back button
        window.addEventListener('popstate', (e) => {
            const page = e.state?.page || 'dashboard';
            this.navigateTo(page, false);
        });
    },

    navigateTo(page, pushState = true) {
        // Hide all pages
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        
        // Show target page
        const targetPage = document.getElementById(`${page}-page`);
        if (targetPage) {
            targetPage.classList.add('active');
            this.currentPage = page;
            
            // Update browser history
            if (pushState) {
                history.pushState({ page }, '', `#${page}`);
            }
            
            // Update navigation
            this.updateActiveNavigation();
            
            // Initialize page-specific functionality
            this.initializePage(page);
        }
    },

    updateActiveNavigation() {
        document.querySelectorAll('[data-nav]').forEach(nav => {
            nav.classList.toggle('active', nav.dataset.nav === this.currentPage);
        });
    },

    initializePage(page) {
        switch (page) {
            case 'dashboard':
                if (window.dashboard) dashboard.init();
                break;
            case 'mood':
                moodTracker.init();
                break;
            case 'games':
                if (window.games) games.init();
                break;
            case 'insights':
                if (window.insights) insights.init();
                break;
        }
    }
};

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    // Load user data
    FeelSync.currentUser = utils.loadFromStorage('feelSyncUser', null);
    FeelSync.streakData = utils.loadFromStorage('feelSyncStreakData', FeelSync.streakData);
    FeelSync.settings = utils.loadFromStorage('feelSyncSettings', FeelSync.settings);
    
    // Initialize core components
    navigation.init();
    moodTracker.init();
    
    // Set initial page based on URL hash
    const initialPage = window.location.hash.replace('#', '') || 'dashboard';
    navigation.navigateTo(initialPage, false);
    
    // Apply settings
    if (FeelSync.settings.darkMode) {
        document.body.classList.add('dark-mode');
    }
    
    console.log('FeelSync initialized successfully');
});

// Export for use in other modules
window.FeelSync = FeelSync;
window.utils = utils;
window.moodTracker = moodTracker;
window.navigation = navigation;
