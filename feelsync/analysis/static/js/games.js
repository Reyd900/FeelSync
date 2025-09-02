// FeelSync Games Module

const games = {
    currentGame: null,
    gameStats: {
        breathingMinutes: 0,
        memoryMatches: 0,
        gamesPlayed: 0,
        achievements: []
    },

    // Game definitions
    gameTypes: {
        breathing: {
            id: 'breathing',
            name: 'Breathing Garden',
            description: 'Practice mindful breathing with guided exercises to reduce stress and anxiety.',
            icon: '🌸',
            benefits: [
                'Reduces stress and anxiety',
                'Improves focus and concentration',
                'Promotes relaxation and calm',
                'Enhances emotional regulation'
            ]
        },
        memory: {
            id: 'memory',
            name: 'Mood Memory Match',
            description: 'Train your cognitive skills while exploring positive emotions and feelings.',
            icon: '🧠',
            benefits: [
                'Improves memory and cognition',
                'Enhances focus and attention',
                'Builds positive associations',
                'Increases mental agility'
            ]
        },
        gratitude: {
            id: 'gratitude',
            name: 'Gratitude Garden',
            description: 'Cultivate thankfulness by collecting and nurturing gratitude moments.',
            icon: '🌻',
            benefits: [
                'Builds positive mindset',
                'Increases life satisfaction',
                'Reduces negative thoughts',
                'Strengthens resilience'
            ]
        }
    },

    // Initialize games module
    init() {
        this.loadGameStats();
        this.renderGameCards();
        this.setupEventListeners();
    },

    // Load game statistics
    loadGameStats() {
        this.gameStats = utils.loadFromStorage('feelSyncGameStats', this.gameStats);
    },

    // Save game statistics
    saveGameStats() {
        utils.saveToStorage('feelSyncGameStats', this.gameStats);
    },

    // Render game cards
    renderGameCards() {
        const gamesGrid = document.querySelector('.games-grid');
        if (!gamesGrid) return;

        gamesGrid.innerHTML = Object.values(this.gameTypes).map(game => `
            <div class="game-card">
                <div class="game-icon">${game.icon}</div>
                <h3>${game.name}</h3>
                <p>${game.description}</p>
                <ul class="game-benefits">
                    ${game.benefits.map(benefit => `<li>${benefit}</li>`).join('')}
                </ul>
                <button class="play-btn" data-game="${game.id}">Play Now</button>
            </div>
        `).join('');
    },

    // Setup event listeners
    setupEventListeners() {
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('play-btn')) {
                const gameId = e.target.dataset.game;
                this.startGame(gameId);
            }
            
            if (e.target.classList.contains('back-btn')) {
                this.exitGame();
            }
        });
    },

    // Start a game
    startGame(gameId) {
        this.currentGame = gameId;
        
        // Hide games grid
        document.querySelector('.games-grid').style.display = 'none';
        
        // Show game arena
        let arena = document.querySelector('.game-arena');
        if (!arena) {
            arena = document.createElement('div');
            arena.className = 'game-arena';
            document.querySelector('.games-container').appendChild(arena);
        }
        
        arena.classList.add('active');
        this.renderGameArena(gameId);
        
        // Update stats
        this.gameStats.gamesPlayed++;
        this.saveGameStats();
    },

    // Exit current game
    exitGame() {
        // Hide arena
        const arena = document.querySelector('.game-arena');
        if (arena) {
            arena.classList.remove('active');
        }
        
        // Show games grid
        document.querySelector('.games-grid').style.display = 'grid';
        
        // Clear current game
        this.currentGame = null;
    },

    // Render game arena
    renderGameArena(gameId) {
        const arena = document.querySelector('.game-arena');
        const game = this.gameTypes[gameId];
        
        arena.innerHTML = `
            <div class="game-header-arena">
                <button class="back-btn">← Back to Games</button>
                <h2>${game.name}</h2>
                <div class="game-stats">
                    <div class="stat-item">
                        <span class="stat-value" id="game-score">0</span>
                        <span class="stat-label">Score</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value" id="game-time">0:00</span>
                        <span class="stat-label">Time</span>
                    </div>
                </div>
            </div>
            <div class="game-content" id="game-content">
                ${this.getGameContent(gameId)}
            </div>
        `;
        
        // Initialize specific game
        this.initializeGame(gameId);
    },

    // Get game-specific content
    getGameContent(gameId) {
        switch (gameId) {
            case 'breathing':
                return this.getBreathingContent();
            case 'memory':
                return this.getMemoryContent();
            case 'gratitude':
                return this.getGratitudeContent();
            default:
                return '<p>Game not found</p>';
        }
    },

    // Breathing game content
    getBreathingContent() {
        return `
            <div class="breathing-game">
                <div class="breathing-instructions">
                    <h3>Mindful Breathing Exercise</h3>
                    <p>Follow the circle's rhythm. Breathe in as it expands, breathe out as it contracts.</p>
                </div>
                
                <div class="breathing-circle" id="breathing-circle">
                    <div class="breathing-text" id="breathing-text">Ready to start?</div>
                </div>
                
                <div class="breathing-controls">
                    <button id="breathing-start">Start Exercise</button>
                    <button id="breathing-pause" style="display:none;">Pause</button>
                    <button id="breathing-stop" style="display:none;">Stop</button>
                </div>
                
                <div class="breathing-settings">
                    <label for="breathing-duration">Duration (minutes):</label>
                    <select id="breathing-duration">
                        <option value="1">1 minute</option>
                        <option value="3" selected>3 minutes</option>
                        <option value="5">5 minutes</option>
                        <option value="10">10 minutes</option>
                    </select>
                    
                    <label for="breathing-pattern">Pattern:</label>
                    <select id="breathing-pattern">
                        <option value="4-4-4-4">Box Breathing (4-4-4-4)</option>
                        <option value="4-7-8">Relaxing (4-7-8)</option>
                        <option value="6-2-6-2" selected>Calm (6-2-6-2)</option>
                    </select>
                </div>
            </div>
        `;
    },

    // Memory game content
    getMemoryContent() {
        return `
            <div class="memory-game">
                <div class="memory-instructions">
                    <h3>Mood Memory Match</h3>
                    <p>Find matching pairs of positive emotions. Click cards to flip them over!</p>
                </div>
                
                <div class="memory-stats">
                    <div class="stat">Matches: <span id="memory-matches">0</span></div>
                    <div class="stat">Moves: <span id="memory-moves">0</span></div>
                    <div class="stat">Time: <span id="memory-timer">0:00</span></div>
                </div>
                
                <div class="memory-grid" id="memory-grid">
                    <!-- Cards will be generated here -->
                </div>
                
                <div class="memory-controls">
                    <button id="memory-new-game">New Game</button>
                    <select id="memory-difficulty">
                        <option value="easy">Easy (4x3)</option>
                        <option value="medium" selected>Medium (4x4)</option>
                        <option value="hard">Hard (6x4)</option>
                    </select>
                </div>
            </div>
        `;
    },

    // Gratitude game content
    getGratitudeContent() {
        return `
            <div class="gratitude-game">
                <div class="gratitude-instructions">
                    <h3>Gratitude Garden</h3>
                    <p>Plant seeds of gratitude and watch your garden grow. What are you thankful for today?</p>
                </div>
                
                <div class="gratitude-garden" id="gratitude-garden">
                    <div class="garden-plot"></div>
                </div>
                
                <div class="gratitude-input">
                    <textarea id="gratitude-text" placeholder="I am grateful for..." maxlength="200"></textarea>
                    <button id="plant-gratitude">Plant Gratitude Seed 🌱</button>
                </div>
                
                <div class="gratitude-collection">
                    <h4>Your Gratitude Collection</h4>
                    <div id="gratitude-list">
                        <!-- Gratitude items will appear here -->
                    </div>
                </div>
            </div>
        `;
    },

    // Initialize specific game
    initializeGame(gameId) {
        switch (gameId) {
            case 'breathing':
                this.initBreathingGame();
                break;
            case 'memory':
                this.initMemoryGame();
                break;
            case 'gratitude':
                this.initGratitudeGame();
                break;
        }
    },

    // Breathing game logic
    initBreathingGame() {
        let breathingInterval;
        let breathingTimer;
        let currentPhase = 'ready';
        let cycleCount = 0;
        let startTime;

        const circle = document.getElementById('breathing-circle');
        const text = document.getElementById('breathing-text');
        const startBtn = document.getElementById('breathing-start');
        const pauseBtn = document.getElementById('breathing-pause');
        const stopBtn = document.getElementById('breathing-stop');

        startBtn.addEventListener('click', startBreathing);
        pauseBtn.addEventListener('click', pauseBreathing);
        stopBtn.addEventListener('click', stopBreathing);

        function startBreathing() {
            const duration = parseInt(document.getElementById('breathing-duration').value);
            const pattern = document.getElementById('breathing-pattern').value.split('-').map(Number);
            const [inhale, hold1, exhale, hold2] = pattern;

            startTime = Date.now();
            cycleCount = 0;
            currentPhase = 'inhale';

            startBtn.style.display = 'none';
            pauseBtn.style.display = 'inline-block';
            stopBtn.style.display = 'inline-block';

            // Start breathing cycle
            breathingInterval = setInterval(() => {
                switch (currentPhase) {
                    case 'inhale':
                        text.textContent = 'Breathe In';
                        circle.classList.add('inhale');
                        circle.classList.remove('exhale');
                        setTimeout(() => {
                            currentPhase = hold1 > 0 ? 'hold1' : 'exhale';
                        }, inhale * 1000);
                        break;
                    case 'hold1':
                        text.textContent = 'Hold';
                        setTimeout(() => {
                            currentPhase = 'exhale';
                        }, hold1 * 1000);
                        break;
                    case 'exhale':
                        text.textContent = 'Breathe Out';
                        circle.classList.add('exhale');
                        circle.classList.remove('inhale');
                        setTimeout(() => {
                            currentPhase = hold2 > 0 ? 'hold2' : 'inhale';
                            cycleCount++;
                        }, exhale * 1000);
                        break;
                    case 'hold2':
                        text.textContent = 'Hold';
                        setTimeout(() => {
                            currentPhase = 'inhale';
                            cycleCount++;
                        }, hold2 * 1000);
                        break;
                }
            }, (inhale + hold1 + exhale + hold2) * 1000);

            // Timer
            breathingTimer = setInterval(() => {
                const elapsed = Math.floor((Date.now() - startTime) / 1000);
                const minutes = Math.floor(elapsed / 60);
                const seconds = elapsed % 60;
                document.getElementById('game-time').textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
                document.getElementById('game-score').textContent = cycleCount;

                if (elapsed >= duration * 60) {
                    stopBreathing();
                    completeBreathingSession(duration);
                }
            }, 1000);
        }

        function pauseBreathing() {
            clearInterval(breathingInterval);
            clearInterval(breathingTimer);
            text.textContent = 'Paused';
            startBtn.style.display = 'inline-block';
            pauseBtn.style.display = 'none';
            startBtn.textContent = 'Resume';
        }

        function stopBreathing() {
            clearInterval(breathingInterval);
            clearInterval(breathingTimer);
            circle.classList.remove('inhale', 'exhale');
            text.textContent = 'Session Complete!';
            
            startBtn.style.display = 'inline-block';
            pauseBtn.style.display = 'none';
            stopBtn.style.display = 'none';
            startBtn.textContent = 'Start Exercise';
        }

        function completeBreathingSession(minutes) {
            games.gameStats.breathingMinutes += minutes;
            games.saveGameStats();
            utils.showNotification(`Great job! You completed ${minutes} minutes of breathing exercise.`, 'success');
        }
    },

    // Memory game logic
    initMemoryGame() {
        const emotions = [
            { id: 1, emoji: '😊', name: 'Joy' },
            { id: 2, emoji: '🥰', name: 'Love' },
            { id: 3, emoji: '😌', name: 'Peace' },
            { id: 4, emoji: '🤗', name: 'Comfort' },
            { id: 5, emoji: '😄', name: 'Happiness' },
            { id: 6, emoji: '✨', name: 'Wonder' },
            { id: 7, emoji: '🌟', name: 'Hope' },
            { id: 8, emoji: '💚', name: 'Gratitude' },
            { id: 9, emoji: '🦋', name: 'Freedom' },
            { id: 10, emoji: '🌈', name: 'Optimism' },
            { id: 11, emoji: '🎉', name: 'Excitement' },
            { id: 12, emoji: '😇', name: 'Serenity' }
        ];

        let gameCards = [];
        let flippedCards = [];
        let matchedPairs = 0;
        let moves = 0;
        let gameTimer;
        let startTime;

        const grid = document.getElementById('memory-grid');
        const newGameBtn = document.getElementById('memory-new-game');
        const difficultySelect = document.getElementById('memory-difficulty');

        newGameBtn.addEventListener('click', initNewGame);
        difficultySelect.addEventListener('change', initNewGame);

        function initNewGame() {
            const difficulty = difficultySelect.value;
            let pairs;
            
            switch (difficulty) {
                case 'easy':
                    pairs = 6;
                    grid.style.gridTemplateColumns = 'repeat(4, 1fr)';
                    break;
                case 'medium':
                    pairs = 8;
                    grid.style.gridTemplateColumns = 'repeat(4, 1fr)';
                    break;
                case 'hard':
                    pairs = 12;
                    grid.style.gridTemplateColumns = 'repeat(6, 1fr)';
                    break;
            }

            // Reset game state
            gameCards = [];
            flippedCards = [];
            matchedPairs = 0;
            moves = 0;
            startTime = Date.now();

            // Create card pairs
            const selectedEmotions = emotions.slice(0, pairs);
            const cardPairs = [...selectedEmotions, ...selectedEmotions];
            
            // Shuffle cards
            cardPairs.sort(() => Math.random() - 0.5);

            // Create card elements
            grid.innerHTML = cardPairs.map((emotion, index) => `
                <div class="memory-card" data-emotion="${emotion.id}" data-index="${index}">
                    <div class="card-front">?</div>
                    <div class="card-back">${emotion.emoji}</div>
                </div>
            `).join('');

            // Add event listeners
            document.querySelectorAll('.memory-card').forEach(card => {
                card.addEventListener('click', flipCard);
            });

            // Start timer
            if (gameTimer) clearInterval(gameTimer);
            gameTimer = setInterval(updateTimer, 1000);

            // Update display
            updateStats();
        }

        function flipCard(e) {
            const card = e.currentTarget;
            
            if (card.classList.contains('flipped') || card.classList.contains('matched') || flippedCards.length === 2) {
                return;
            }

            card.classList.add('flipped');
            flippedCards.push(card);

            if (flippedCards.length === 2) {
                moves++;
                updateStats();
                checkForMatch();
            }
        }

        function checkForMatch() {
            const [card1, card2] = flippedCards;
            const emotion1 = card1.dataset.emotion;
            const emotion2 = card2.dataset.emotion;

            setTimeout(() => {
                if (emotion1 === emotion2) {
                    // Match!
                    card1.classList.add('matched');
                    card2.classList.add('matched');
                    matchedPairs++;
                    games.gameStats.memoryMatches++;
                    
                    if (matchedPairs === gameCards.length / 2) {
                        endGame();
                    }
                } else {
                    // No match
                    card1.classList.remove('flipped');
                    card2.classList.remove('flipped');
                }
                
                flippedCards = [];
                updateStats();
            }, 1000);
        }

        function updateStats() {
            document.getElementById('memory-matches').textContent = matchedPairs;
            document.getElementById('memory-moves').textContent = moves;
            document.getElementById('game-score').textContent = matchedPairs;
        }

        function updateTimer() {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            const timeString = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            document.getElementById('memory-timer').textContent = timeString;
            document.getElementById('game-time').textContent = timeString;
        }

        function endGame() {
            clearInterval(gameTimer);
            games.saveGameStats();
            utils.showNotification('Congratulations! You matched all pairs! 🎉', 'success');
        }

        // Initialize first game
        initNewGame();
    },

    // Gratitude game logic
    initGratitudeGame() {
        const gratitudeList = utils.loadFromStorage('feelSyncGratitude', []);
        const textArea = document.getElementById('gratitude-text');
        const plantBtn = document.getElementById('plant-gratitude');
        const garden = document.getElementById('gratitude-garden');
        const collection = document.getElementById('gratitude-list');

        plantBtn.addEventListener('click', plantGratitude);
        
        function plantGratitude() {
            const gratitudeText = textArea.value.trim();
            if (!gratitudeText) {
                utils.showNotification('Please write something you\'re grateful for!', 'error');
                return;
            }

            const gratitudeItem = {
                id: utils.generateId(),
                text: gratitudeText,
                date: new Date().toISOString(),
                planted: Date.now()
            };

            gratitudeList.unshift(gratitudeItem);
            utils.saveToStorage('feelSyncGratitude', gratitudeList);

            // Add to garden
            addToGarden(gratitudeItem);
            
            // Update collection
            updateCollection();
            
            // Clear input
            textArea.value = '';
            
            utils.showNotification('Gratitude seed planted! 🌱', 'success');
        }

        function addToGarden(item) {
            const seed = document.createElement('div');
            seed.className = 'gratitude-seed';
            seed.innerHTML = `
                <div class="seed-plant">🌱</div>
                <div class="seed-text">${item.text.substring(0, 30)}...</div>
            `;
            
            // Random position in garden
            const plot = garden.querySelector('.garden-plot');
            seed.style.left = Math.random() * 80 + '%';
            seed.style.top = Math.random() * 80 + '%';
            plot.appendChild(seed);

            // Grow animation
            setTimeout(() => {
                seed.classList.add('grown');
                seed.querySelector('.seed-plant').textContent = '🌸';
            }, 2000);
        }

        function updateCollection() {
            collection.innerHTML = gratitudeList.slice(0, 10).map(item => `
                <div class="gratitude-item">
                    <div class="gratitude-text">${item.text}</div>
                    <div class="gratitude-date">${utils.formatDate(item.date)}</div>
                </div>
            `).join('');
        }

        // Load existing gratitude items
        updateCollection();
        gratitudeList.forEach(item => addToGarden(item));
    }
};

// Make games available globally
window.games = games;
