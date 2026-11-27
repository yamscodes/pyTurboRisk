# TurboRisk Web Application

A Flask-based web interface for the TurboRisk game engine.

## Overview

This web application provides a browser-based interface to play TurboRisk, the Risk-like strategy game. It uses the core pyTurboRisk game engine and provides a responsive web UI.

## Features

- **Game Setup**: Configure number of players (2-6)
- **Interactive Map**: Click on territories to perform actions
- **Territory Assignment**: Automatic random assignment of territories
- **Army Placement**: Place your initial armies on your territories
- **Attack Phase**: Attack adjacent enemy territories
- **Movement Phase**: Move armies between your territories
- **Real-time Updates**: Game state updates automatically

## Installation

### Prerequisites

- Python 3.7+
- pip

### Setup

1. Navigate to the webapp directory:
   ```bash
   cd python_port/webapp
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python run.py
   ```

4. Open your browser and navigate to:
   ```
   http://localhost:5001
   ```

## Usage

### Starting a New Game

1. Click "New Game" or navigate to `/setup`
2. Select the number of players (2-6)
3. Click "Start Game"

### Gameplay

#### Placement Phase
- Click on your territories to place armies
- Place all your initial armies before proceeding

#### Attack Phase
- Click on one of your territories with more than 1 army to select as attack source
- Click on an adjacent enemy territory to select as target
- Click again to confirm the attack
- Dice will be rolled and results displayed

#### Movement Phase
- After attacking, you can move armies between your territories
- Click "End Turn" to finish your turn

### Game Rules

- Each player starts with a number of territories and initial armies
- On your turn, place all new armies first
- Attack adjacent enemy territories by rolling dice (attacker up to 3 dice, defender up to 2)
- Conquer territories by defeating all defending armies
- Move armies between your territories at the end of your turn
- Collect cards for conquering territories (to be implemented)
- Win by conquering all territories on the map

## Project Structure

```
webapp/
├── __init__.py          # Flask app initialization
├── routes.py            # Main game routes and logic
├── run.py               # Application entry point
├── requirements.txt     # Python dependencies
├── README.md            # This file
├── templates/
│   ├── base.html        # Base template
│   ├── game.html        # Main game page
│   ├── setup.html       # Game setup page
│   ├── 404.html         # 404 error page
│   └── 500.html         # 500 error page
└── static/
    ├── css/
    │   └── style.css     # Main stylesheet
    └── js/
        └── game.js       # Game JavaScript logic
```

## API Endpoints

### GET Routes
- `/` - Main game page
- `/setup` - Game setup page
- `/new_game` - Start a new game
- `/get_game_state` - Get current game state as JSON
- `/territory_info/<terr_id>` - Get detailed info about a territory
- `/select_territory/<terr_id>` - Select a territory
- `/attack/<from_terr>/<to_terr>` - Perform an attack
- `/move/<from_terr>/<to_terr>` - Move armies
- `/cancel_action` - Cancel current action
- `/end_turn` - End current turn

### POST Routes
- `/place_armies/<terr_id>` - Place armies on a territory
- `/set_placement_armies` - Set number of armies to place

## Configuration

The Flask app uses the following configuration:
- `SECRET_KEY`: Used for session management (change in production)
- `DEBUG`: Set to True in development
- `HOST`: 0.0.0.0 (accessible from network)
- `PORT`: 5001

## Development

To run in development mode with auto-reload:
```bash
python run.py
```

## Production Deployment

For production deployment, consider:

1. Using a production WSGI server like Gunicorn or uWSGI
2. Setting up a reverse proxy with Nginx or Apache
3. Using environment variables for configuration
4. Setting up proper logging
5. Implementing proper security measures

Example with Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 webapp:app
```

## License

This web application is part of the pyTurboRisk project and inherits its license.

## Contributing

Contributions are welcome! Please follow the main pyTurboRisk contribution guidelines.
