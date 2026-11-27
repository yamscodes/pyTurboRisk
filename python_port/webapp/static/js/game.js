/**
 * TurboRisk Web Application - Game JavaScript
 * Handles client-side game logic and interactions
 */

// Game state variables
let gameState = {
    selectedTerritory: null,
    attackFrom: null,
    attackTo: null,
    moveFrom: null,
    moveTo: null,
    placementArmies: 1,
    currentPhase: null
};

// Territory positions on the map
const TERRITORY_POSITIONS = {
    1: { x: 50, y: 100 },   // Alaska
    2: { x: 150, y: 100 },  // Northwest Territory
    3: { x: 250, y: 50 },   // Greenland
    4: { x: 150, y: 150 },  // Alberta
    5: { x: 250, y: 150 },  // Ontario
    6: { x: 300, y: 150 },  // Quebec
    7: { x: 150, y: 200 },  // Western US
    8: { x: 250, y: 200 },  // Eastern US
    9: { x: 200, y: 250 },  // Central America
    10: { x: 200, y: 300 }, // Venezuela
    11: { x: 200, y: 350 }, // Peru
    12: { x: 250, y: 350 }, // Brazil
    13: { x: 250, y: 400 }, // Argentina
    14: { x: 400, y: 300 }, // North Africa
    15: { x: 450, y: 300 }, // Egypt
    16: { x: 450, y: 350 }, // East Africa
    17: { x: 400, y: 350 }, // Congo
    18: { x: 450, y: 400 }, // South Africa
    19: { x: 500, y: 400 }, // Madagascar
    20: { x: 400, y: 50 },  // Iceland
    21: { x: 450, y: 100 }, // Scandinavia
    22: { x: 500, y: 100 }, // Ukraine
    23: { x: 450, y: 150 }, // Northern Europe
    24: { x: 400, y: 150 }, // Great Britain
    25: { x: 400, y: 200 }, // Western Europe
    26: { x: 450, y: 200 }, // Southern Europe
    27: { x: 500, y: 200 }, // Middle East
    28: { x: 600, y: 100 }, // Yamal-Nemets
    29: { x: 600, y: 150 }, // Kazakhstan
    30: { x: 600, y: 200 }, // India
    31: { x: 650, y: 250 }, // Siam
    32: { x: 650, y: 200 }, // China
    33: { x: 650, y: 150 }, // Mongolia
    34: { x: 700, y: 100 }, // Taymyr
    35: { x: 750, y: 100 }, // Yakut
    36: { x: 700, y: 150 }, // Buryat
    37: { x: 750, y: 150 }, // Koryak
    38: { x: 800, y: 150 }, // Japan
    39: { x: 700, y: 300 }, // Indonesia
    40: { x: 750, y: 350 }, // Western Australia
    41: { x: 800, y: 350 }, // Eastern Australia
    42: { x: 750, y: 300 }  // New Guinea
};

// Player colors
const PLAYER_COLORS = [
    '#0000ff', '#ff0000', '#00ff00', '#ffff00', 
    '#ff00ff', '#00ffff', '#800000', '#008000'
];

/**
 * Initialize the game board
 */
function initGameBoard() {
    const svg = document.getElementById('map-svg');
    if (!svg) return;
    
    // Clear existing content
    svg.innerHTML = '<rect width="100%" height="100%" fill="#1a252f" />';
    
    // Draw territory circles and labels
    for (let terrId = 1; terrId <= 42; terrId++) {
        const pos = TERRITORY_POSITIONS[terrId];
        if (!pos) continue;
        
        // Create territory circle (clickable area)
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', pos.x);
        circle.setAttribute('cy', pos.y);
        circle.setAttribute('r', 25);
        circle.setAttribute('class', 'territory-overlay');
        circle.setAttribute('data-id', terrId);
        circle.setAttribute('stroke', 'transparent');
        circle.setAttribute('stroke-width', '2');
        circle.setAttribute('fill', 'transparent');
        circle.style.cursor = 'pointer';
        circle.addEventListener('click', () => handleTerritoryClick(terrId));
        circle.addEventListener('mouseenter', () => highlightTerritory(terrId));
        circle.addEventListener('mouseleave', () => unhighlightTerritory(terrId));
        svg.appendChild(circle);
        
        // Create territory label (abbreviated name)
        const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        label.setAttribute('x', pos.x);
        label.setAttribute('y', pos.y - 30);
        label.setAttribute('text-anchor', 'middle');
        label.setAttribute('fill', 'white');
        label.setAttribute('font-size', '10');
        label.setAttribute('font-weight', 'bold');
        label.textContent = getTerritoryName(terrId).substring(0, 3);
        label.classList.add('territory-label');
        svg.appendChild(label);
        
        // Create army count display
        const armyText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        armyText.setAttribute('x', pos.x);
        armyText.setAttribute('y', pos.y + 10);
        armyText.setAttribute('text-anchor', 'middle');
        armyText.setAttribute('fill', 'white');
        armyText.setAttribute('font-size', '14');
        armyText.setAttribute('font-weight', 'bold');
        armyText.textContent = '0';
        armyText.classList.add('army-count');
        armyText.setAttribute('data-id', terrId);
        svg.appendChild(armyText);
    }
    
    // Load territory data
    loadTerritoryData();
}

/**
 * Load territory data from the server
 */
function loadTerritoryData() {
    fetch('/get_game_state')
        .then(response => response.json())
        .then(data => {
            gameState.currentPhase = data.game_state;
            
            // Update all territories
            for (const [terrId, terrData] of Object.entries(data.territories)) {
                updateTerritory(parseInt(terrId), terrData);
            }
            
            // Update player info
            updatePlayerInfo(data.players);
            
            // Update message
            updateGameMessage(data.message);
            
            // Set attack state if present
            if (data.attack_from) {
                gameState.attackFrom = data.attack_from;
                gameState.selectedTerritory = data.attack_from;
            }
            if (data.attack_to) {
                gameState.attackTo = data.attack_to;
            }
            
            updateTerritoryStates();
        })
        .catch(error => {
            console.error('Error loading territory data:', error);
        });
}

/**
 * Update a territory's display
 */
function updateTerritory(terrId, terrData) {
    const pos = TERRITORY_POSITIONS[terrId];
    if (!pos) return;
    
    // Update army count
    const armyText = document.querySelector(`text.army-count[data-id="${terrId}"]`);
    if (armyText) {
        armyText.textContent = terrData.army;
    }
    
    // Update owner indicator
    const svg = document.getElementById('map-svg');
    if (!svg) return;
    
    // Remove existing owner indicator
    const existing = document.querySelector(`.owner-indicator[data-id="${terrId}"]`);
    if (existing) {
        existing.remove();
    }
    
    // Add new owner indicator if territory has an owner
    if (terrData.owner > 0) {
        const ownerCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        ownerCircle.setAttribute('cx', pos.x);
        ownerCircle.setAttribute('cy', pos.y);
        ownerCircle.setAttribute('r', 12);
        ownerCircle.setAttribute('fill', PLAYER_COLORS[terrData.owner - 1]);
        ownerCircle.setAttribute('data-id', terrId);
        ownerCircle.classList.add('owner-indicator');
        svg.appendChild(ownerCircle);
    }
}

/**
 * Get territory name from ID
 */
function getTerritoryName(terrId) {
    const names = {
        1: 'Alaska', 2: 'Northwest Territory', 3: 'Greenland',
        4: 'Alberta', 5: 'Ontario', 6: 'Quebec',
        7: 'Western US', 8: 'Eastern US', 9: 'Central America',
        10: 'Venezuela', 11: 'Peru', 12: 'Brazil',
        13: 'Argentina', 14: 'North Africa', 15: 'Egypt',
        16: 'East Africa', 17: 'Congo', 18: 'South Africa',
        19: 'Madagascar', 20: 'Iceland', 21: 'Scandinavia',
        22: 'Ukraine', 23: 'Northern Europe', 24: 'Great Britain',
        25: 'Western Europe', 26: 'Southern Europe', 27: 'Middle East',
        28: 'Yamal-Nemets', 29: 'Kazakhstan', 30: 'India',
        31: 'Siam', 32: 'China', 33: 'Mongolia',
        34: 'Taymyr', 35: 'Yakut', 36: 'Buryat',
        37: 'Koryak', 38: 'Japan', 39: 'Indonesia',
        40: 'Western Australia', 41: 'Eastern Australia', 42: 'New Guinea'
    };
    return names[terrId] || `Territory ${terrId}`;
}

/**
 * Handle territory click
 */
function handleTerritoryClick(terrId) {
    // Get current phase from the page
    const phaseElement = document.getElementById('phase-indicator');
    const currentPhase = phaseElement ? phaseElement.textContent.toLowerCase() : '';
    
    if (currentPhase.includes('placement') || currentPhase.includes('distributing')) {
        // Placement phase - place army
        placeArmyOnTerritory(terrId);
    } else if (currentPhase.includes('attack')) {
        // Attack phase
        if (gameState.attackFrom === null) {
            // Selecting attack source
            selectAttackSource(terrId);
        } else if (gameState.attackFrom !== null && gameState.attackTo === null) {
            // Selecting attack target
            selectAttackTarget(terrId);
        } else if (gameState.attackFrom !== null && gameState.attackTo !== null) {
            // Confirming attack
            if (terrId === gameState.attackTo) {
                confirmAttack();
            } else {
                // Cancel and select new
                cancelAction();
                selectAttackSource(terrId);
            }
        }
    }
}

/**
 * Select territory as attack source
 */
function selectAttackSource(terrId) {
    fetch(`/select_territory/${terrId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (data.action === 'select_attack_source') {
                    gameState.attackFrom = terrId;
                    gameState.selectedTerritory = terrId;
                    gameState.attackTo = null;
                    updateTerritoryStates();
                    updateGameMessage(data.message);
                } else {
                    updateGameMessage(data.message);
                }
            } else {
                updateGameMessage(data.message);
            }
        });
}

/**
 * Select territory as attack target
 */
function selectAttackTarget(terrId) {
    fetch(`/select_territory/${terrId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (data.action === 'select_attack_target') {
                    gameState.attackTo = terrId;
                    gameState.selectedTerritory = terrId;
                    updateTerritoryStates();
                    updateGameMessage(data.message);
                } else {
                    updateGameMessage(data.message);
                }
            } else {
                updateGameMessage(data.message);
            }
        });
}

/**
 * Place army on territory
 */
function placeArmyOnTerritory(terrId) {
    fetch(`/select_territory/${terrId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateGameMessage(data.message);
                
                // Update army count
                updateArmyCount(terrId, data.territory_army);
                
                // Update new army count display
                updateNewArmyCount(data.new_army);
                
                // Check if we need to move to next phase
                if (data.new_army <= 0) {
                    window.location.reload();
                }
            } else {
                updateGameMessage(data.message);
            }
        });
}

/**
 * Confirm and perform attack
 */
function confirmAttack() {
    if (gameState.attackFrom && gameState.attackTo) {
        fetch(`/attack/${gameState.attackFrom}/${gameState.attackTo}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateGameMessage(data.message);
                    
                    // Update army counts
                    updateArmyCount(gameState.attackFrom, data.from_army);
                    updateArmyCount(gameState.attackTo, data.to_army);
                    
                    // Update owner if conquered
                    if (data.conquest && data.to_owner > 0) {
                        updateOwner(gameState.attackTo, data.to_owner);
                    }
                    
                    // Reset attack state
                    if (!data.message.includes('can attack again')) {
                        gameState.attackFrom = null;
                        gameState.attackTo = null;
                        gameState.selectedTerritory = null;
                    }
                    
                    updateTerritoryStates();
                }
            });
    }
}

/**
 * Cancel current action
 */
function cancelAction() {
    fetch('/cancel_action')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                gameState.attackFrom = null;
                gameState.attackTo = null;
                gameState.selectedTerritory = null;
                updateTerritoryStates();
                updateGameMessage(data.message);
            }
        });
}

/**
 * End current turn
 */
function endTurn() {
    fetch('/end_turn')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateGameMessage(data.message);
                window.location.reload();
            }
        });
}

/**
 * Update territory visual states
 */
function updateTerritoryStates() {
    const svg = document.getElementById('map-svg');
    if (!svg) return;
    
    const circles = svg.querySelectorAll('.territory-overlay');
    
    circles.forEach(circle => {
        circle.classList.remove('selected', 'attack-source', 'attack-target');
        
        const terrId = parseInt(circle.getAttribute('data-id'));
        if (gameState.selectedTerritory === terrId) {
            circle.classList.add('selected');
        }
        if (gameState.attackFrom === terrId) {
            circle.classList.add('attack-source');
        }
        if (gameState.attackTo === terrId) {
            circle.classList.add('attack-target');
        }
    });
}

/**
 * Highlight territory on hover
 */
function highlightTerritory(terrId) {
    const circle = document.querySelector(`[data-id="${terrId}"]`);
    if (circle && !circle.classList.contains('selected') && 
        !circle.classList.contains('attack-source') && 
        !circle.classList.contains('attack-target')) {
        circle.setAttribute('stroke', '#f1c40f');
    }
}

/**
 * Remove highlight from territory
 */
function unhighlightTerritory(terrId) {
    const circle = document.querySelector(`[data-id="${terrId}"]`);
    if (circle && !circle.classList.contains('selected') && 
        !circle.classList.contains('attack-source') && 
        !circle.classList.contains('attack-target')) {
        circle.setAttribute('stroke', 'transparent');
    }
}

/**
 * Update army count display for a territory
 */
function updateArmyCount(terrId, count) {
    const armyText = document.querySelector(`text.army-count[data-id="${terrId}"]`);
    if (armyText) {
        armyText.textContent = count;
    }
}

/**
 * Update owner display for a territory
 */
function updateOwner(terrId, playerId) {
    const svg = document.getElementById('map-svg');
    if (!svg) return;
    
    // Remove existing owner indicator
    const existing = document.querySelector(`.owner-indicator[data-id="${terrId}"]`);
    if (existing) {
        existing.remove();
    }
    
    // Add new owner indicator
    const pos = TERRITORY_POSITIONS[terrId];
    if (pos) {
        const ownerCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        ownerCircle.setAttribute('cx', pos.x);
        ownerCircle.setAttribute('cy', pos.y);
        ownerCircle.setAttribute('r', 12);
        ownerCircle.setAttribute('fill', PLAYER_COLORS[playerId - 1]);
        ownerCircle.setAttribute('data-id', terrId);
        ownerCircle.classList.add('owner-indicator');
        svg.appendChild(ownerCircle);
    }
}

/**
 * Update new army count display
 */
function updateNewArmyCount(count) {
    const newArmyDisplay = document.querySelector('.stat-value:last-child');
    if (newArmyDisplay) {
        newArmyDisplay.textContent = count;
    }
}

/**
 * Update player info display
 */
function updatePlayerInfo(players) {
    // This could be enhanced to update player stats dynamically
}

/**
 * Update game message
 */
function updateGameMessage(message) {
    const messageEl = document.getElementById('game-message');
    if (messageEl) {
        messageEl.textContent = message;
    }
}

/**
 * Show territory info modal
 */
function showTerritoryInfo(terrId) {
    fetch(`/territory_info/${terrId}`)
        .then(response => response.json())
        .then(data => {
            const modal = document.getElementById('territory-modal');
            const title = document.getElementById('modal-title');
            const content = document.getElementById('modal-content');
            
            if (modal && title && content) {
                title.textContent = data.name;
                content.innerHTML = `
                    <p><strong>Continent:</strong> ${data.continent}</p>
                    <p><strong>Owner:</strong> ${data.owner_name || 'None'}</p>
                    <p><strong>Armies:</strong> ${data.army}</p>
                    <p><strong>Borders:</strong> ${data.borders.map(b => b.name).join(', ')}</p>
                `;
                modal.style.display = 'block';
            }
        });
}

/**
 * Close territory info modal
 */
function closeModal() {
    const modal = document.getElementById('territory-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

/**
 * Show army placement modal
 */
function showArmyModal() {
    const modal = document.getElementById('army-modal');
    if (modal) {
        modal.style.display = 'block';
    }
}

/**
 * Close army placement modal
 */
function closeArmyModal() {
    const modal = document.getElementById('army-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

/**
 * Place selected number of armies
 */
function placeSelectedArmies() {
    const terrId = gameState.selectedTerritory;
    const armies = parseInt(document.getElementById('army-count').value);
    
    if (terrId && armies > 0) {
        fetch(`/place_armies/${terrId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ armies: armies })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateGameMessage(data.message);
                updateArmyCount(terrId, data.territory_army);
                closeArmyModal();
                
                updateNewArmyCount(data.new_army);
                
                if (data.new_army <= 0) {
                    window.location.reload();
                }
            }
        });
    }
}

/**
 * Select territory from list
 */
function selectTerritoryFromList(terrId) {
    gameState.selectedTerritory = terrId;
    // Could highlight the territory on the map
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Initialize the game board
    initGameBoard();
    
    // Set up event listeners for action buttons
    const confirmAttackBtn = document.querySelector('.btn-danger');
    if (confirmAttackBtn) {
        confirmAttackBtn.addEventListener('click', confirmAttack);
    }
    
    const endTurnBtn = document.querySelector('.btn-success');
    if (endTurnBtn) {
        endTurnBtn.addEventListener('click', endTurn);
    }
    
    // Set up modal close buttons
    const closeModalBtn = document.querySelector('#territory-modal button');
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', closeModal);
    }
    
    const closeArmyBtn = document.querySelector('#army-modal .btn-secondary');
    if (closeArmyBtn) {
        closeArmyBtn.addEventListener('click', closeArmyModal);
    }
    
    const placeArmyBtn = document.querySelector('#army-modal .btn-primary');
    if (placeArmyBtn) {
        placeArmyBtn.addEventListener('click', placeSelectedArmies);
    }
    
    // Close modals on outside click
    window.addEventListener('click', (event) => {
        const territoryModal = document.getElementById('territory-modal');
        const armyModal = document.getElementById('army-modal');
        
        if (territoryModal && event.target === territoryModal) {
            closeModal();
        }
        if (armyModal && event.target === armyModal) {
            closeArmyModal();
        }
    });
    
    // Auto-refresh game state periodically
    setInterval(loadTerritoryData, 5000);
});

// Make functions globally available
window.selectTerritory = selectTerritoryFromList;
window.placeArmy = showArmyModal;
window.confirmAttack = confirmAttack;
window.cancelAction = cancelAction;
window.endTurn = endTurn;
window.closeModal = closeModal;
window.closeArmyModal = closeArmyModal;
window.placeSelectedArmies = placeSelectedArmies;
