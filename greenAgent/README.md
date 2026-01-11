# Green Agent - Werewolf Game Orchestrator

An Agent-to-Agent (A2A) evaluation server that orchestrates and manages Werewolf game sessions between multiple AI agents.

## Overview

The Green Agent is responsible for running complete Werewolf game evaluations. It manages game state, coordinates communication between agent participants (villagers, werewolves, seer), executes game phases, and tracks outcomes.

## Architecture

### Core Components

- **A2A Server** (`__main__.py`): HTTP server exposing agent capabilities via A2A protocol on port 9999
- **Game Controller** (`src/game/Game.py`): Main game loop and phase orchestration
- **Green Agent** (`src/a2a/agent.py`): Primary agent logic that processes evaluation requests
- **Messenger** (`src/a2a/messenger.py`): Handles agent-to-agent communication
- **Game State** (`src/game/GameData.py`): Maintains all game state and participant data

### Game Phases

The game executes in the following sequential phases each round:

1. **Night** (`src/phases/night.py`)
   - Werewolf selects a player to eliminate
   - Seer investigates one player to learn their role

2. **Bidding** (`src/phases/bidding.py`)
   - Players bid for speaking priority in discussion

3. **Discussion** (`src/phases/discussion.py`)
   - Players communicate and share information based on bidding order

4. **Voting** (`src/phases/voting.py`)
   - Players vote to eliminate a suspected werewolf

5. **Round End** (`src/phases/round_end.py`)
   - Process eliminations and check win conditions

6. **Game End** (`src/phases/game_end.py`)
   - Finalize results and analytics

### Models

- **Participant** (`src/models/Participant.py`): Represents an agent player
- **Event** (`src/models/Event.py`): Game event logging
- **Vote** (`src/models/Vote.py`): Voting data structure
- **Elimination** (`src/models/Elimination.py`): Elimination tracking
- **Enums** (`src/models/enum/`): Phase, Role, Status, EventType definitions

## Setup

### Installing uv

uv is a fast Python package installer and resolver. Install it using one of the following methods:

```bash
# macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# With pip
pip install uv

# With Homebrew (macOS)
brew install uv
```

### Installing Dependencies

Once uv is installed, use it to sync all project dependencies including dev/test dependencies:

```bash
# Navigate to the greenAgent directory
cd greenAgent

# Sync all dependencies (runtime + dev/test)
uv sync --dev
```

This will:
- Create a virtual environment if one doesn't exist
- Install all dependencies specified in `pyproject.toml`
- Install dev dependencies (pytest, pytest-asyncio, pytest-cov)
- Use the exact versions locked in `uv.lock` for reproducible builds

### Activating the Virtual Environment

**IMPORTANT:** Before running the server or tests, make sure your virtual environment is active.

```bash
# macOS and Linux
source .venv/bin/activate

# Windows (Command Prompt)
.venv\Scripts\activate.bat

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

You'll know the virtual environment is active when you see `(.venv)` at the beginning of your terminal prompt.

To deactivate the virtual environment:
```bash
deactivate
```

## Running the Server

```bash
# Using Python
python -m greenAgent

# Using Docker
docker build -t green-agent .
docker run -p 9999:9999 green-agent
```

The server will start on `http://0.0.0.0:9999` and expose the A2A agent card.

## Testing

The Green Agent includes comprehensive tests for all game phases.

### Running Tests

```bash
# Run all tests
pytest tests/

# Run all tests with verbose output
pytest tests/ -v

# Run specific phase tests
pytest tests/test_night.py
pytest tests/test_voting.py
pytest tests/test_bidding.py
pytest tests/test_discussion.py
pytest tests/test_round_end.py
pytest tests/test_game_end.py

# Run tests with coverage report
pytest tests/ --cov=src --cov-report=html

# Run tests and stop at first failure
pytest tests/ -x

# Run tests matching a specific pattern
pytest tests/ -k "test_night"
```

### Test Structure

- **tests/conftest.py**: Shared fixtures and test utilities
  - Mock messenger, game state, and participant fixtures
  - Sample response fixtures for different phases

- **tests/test_night.py**: Night phase tests (fully implemented)
  - Werewolf elimination logic
  - Seer investigation logic
  - JSON parsing and prompt validation

- **tests/test_voting.py**: Voting phase tests (fully implemented)
  - Vote collection and tallying
  - Elimination logic
  - Event logging

- **tests/test_bidding.py**: Bidding phase tests (placeholder)
- **tests/test_discussion.py**: Discussion phase tests (placeholder)
- **tests/test_round_end.py**: Round end phase tests (placeholder)
- **tests/test_game_end.py**: Game end phase tests (placeholder)

Placeholder tests contain detailed comments describing expected behavior and serve as documentation for implementation.

## Game Flow

1. Receive `EvalRequest` with participant agent URLs
2. Assign roles randomly to participants (Villagers, Werewolf, Seer)
3. Execute game phases in sequence until:
   - Werewolf is eliminated (villagers win)
   - Werewolves equal or outnumber villagers (werewolves win)
4. Return evaluation results and analytics

## Dependencies

- **a2a-sdk**: Agent-to-Agent protocol implementation with HTTP server support
- **agentbeats**: Agent monitoring and telemetry
- **uvicorn**: ASGI server
- **uuid**: Unique identifier generation

See `pyproject.toml` for complete dependency list.

## API

The Green Agent accepts `EvalRequest` messages via A2A protocol containing:
- `participants`: Map of role names to agent URLs
- `config`: Evaluation configuration parameters

## Development

The agent uses Python 3.13+ and the A2A SDK for agent communication. All game logic is event-driven and logged for evaluation purposes.
