# SlotBot - AI-Powered Calendar Booking Assistant

SlotBot is an intelligent calendar booking chatbot that uses multi-agent AI orchestration to manage appointment scheduling through natural language conversations. Built with CrewAI and FastAPI, it provides a seamless experience for booking, checking, and managing calendar appointments via Google Calendar integration.

## Features

- **Natural Language Understanding**: Parse user intents for booking, checking availability, and managing appointments
- **Multi-Agent Architecture**: Specialized AI agents for different tasks (NLP parsing, session management, calendar operations, response formatting)
- **Google Calendar Integration**: Direct integration with Google Calendar for real-time availability and booking
- **Session Management**: Persistent conversation sessions for contextual interactions
- **Modern UI**: React-based frontend with Shadcn/UI components and Tailwind CSS
- **RESTful API**: FastAPI backend with async support and CORS configuration

## Architecture

### Backend Components

- **FastAPI Server**: Handles HTTP requests and manages session state
- **CrewAI Multi-Agent System**: Orchestrates specialized agents for task execution
  - **NLP Parser**: Extracts intents and entities from user messages
  - **Session Manager**: Maintains user context and validates required information
  - **Calendar Manager**: Executes calendar operations using Google Calendar API
  - **Response Agent**: Formats user-friendly responses
- **Conditional Task Execution**: Smart workflow routing based on conversation state

### Frontend Components

- **React + TypeScript**: Modern, type-safe frontend development
- **Vite**: Fast development and optimized production builds
- **Shadcn/UI**: Beautiful, accessible UI components
- **TanStack Query**: Efficient data fetching and state management

## Project Structure

```
slotbot/
├── api/                        # FastAPI application
│   ├── main.py                # Application entry point
│   ├── dependencies.py        # Shared dependencies
│   ├── schemas.py             # Pydantic models
│   └── routes/
│       ├── chat.py            # Chat endpoints
│       └── health.py          # Health check endpoints
├── src/slotbot/               # Core application logic
│   ├── crew.py                # CrewAI agent orchestration
│   ├── models.py              # Data models
│   ├── config/
│   │   ├── agents.yaml        # Agent configurations
│   │   └── tasks.yaml         # Task definitions
│   ├── tools/                 # Custom tools
│   │   └── calendar_tools.py  # Google Calendar integration
│   └── google_api/
│       └── Oauth_client.py    # OAuth authentication
├── frontend/                   # React frontend application
│   ├── src/
│   │   ├── App.tsx            # Main application component
│   │   └── main.tsx           # Application entry point
│   └── package.json
├── knowledge/                  # Knowledge base files
├── tests/                      # Test files
├── pyproject.toml             # Python project configuration
└── requirements.txt           # Python dependencies
```

## Prerequisites

- Python 3.10 - 3.13
- Node.js 18+ and npm/pnpm
- Google Cloud Project with Calendar API enabled
- Google OAuth 2.0 credentials

## Installation

### Backend Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd slotbot
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Set up Google Calendar API:
   - Create a Google Cloud Project
   - Enable Google Calendar API
   - Create OAuth 2.0 credentials
   - Download credentials and save as `credentials.json` in the project root

5. Configure environment variables:
```bash
# Create .env file
cp .env.example .env  # If available, or create manually
```

Add your API keys and configuration to `.env`.

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
# or
pnpm install
```

## Usage

### Running the Backend

Start the FastAPI server:

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

API Documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Running the Frontend

In a separate terminal, start the development server:

```bash
cd frontend
npm run dev
# or
pnpm dev
```

The frontend will be available at `http://localhost:5173`.

## API Endpoints

### Chat Endpoints

- **POST** `/start_chat` - Initialize a new chat session
  - Returns: `{ session_id: string, message: string }`

- **POST** `/chat` - Send a message and get a response
  - Request body:
    ```json
    {
      "session_id": "string",
      "user_message": "string"
    }
    ```
  - Response:
    ```json
    {
      "session_id": "string",
      "chatbot_response": "string"
    }
    ```

### Health Check

- **GET** `/health` - Check API health status

## CrewAI Workflow

The chatbot uses a sequential multi-agent workflow:

1. **Parse User Input**: Extract intent and entities from user message
2. **Validate Session State**: Check if all required information is available
3. **Collect Missing Information** (Conditional): Ask for missing details if needed
4. **Execute Calendar Action** (Conditional): Perform calendar operations
5. **Format User Response**: Generate friendly response for the user

## Development

### Running Tests

```bash
# Backend tests
pytest

# Run specific test file
pytest tests/test_crew.py
```

### Code Style

The project follows SOLID principles and clean code practices:
- Single Responsibility Principle
- Repository pattern for data access
- Separation of business logic from models
- Test-Driven Development (TDD)

## Configuration

### Agent Configuration

Agents are configured in [src/slotbot/config/agents.yaml](src/slotbot/config/agents.yaml):
- NLP Parser: Gemini 2.5 Flash Lite
- Session Manager: Gemini 2.5 Flash Lite
- Calendar Manager: Handles calendar operations
- Response Agent: Formats user responses

### Task Configuration

Tasks are defined in [src/slotbot/config/tasks.yaml](src/slotbot/config/tasks.yaml):
- User input parsing
- Session state validation
- Information collection
- Calendar action execution
- Response formatting

## Technologies Used

### Backend
- FastAPI - Modern web framework for APIs
- CrewAI - Multi-agent AI orchestration
- Pydantic - Data validation
- Google Calendar API - Calendar integration
- Python-dotenv - Environment configuration

### Frontend
- React 18 - UI library
- TypeScript - Type-safe JavaScript
- Vite - Build tool
- Shadcn/UI - UI component library
- Tailwind CSS - Utility-first CSS
- TanStack Query - Data fetching
- React Router - Routing

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [CrewAI](https://www.crewai.com/) for multi-agent orchestration
- UI components from [Shadcn/UI](https://ui.shadcn.com/)
- Powered by Google Calendar API

## Support

For issues, questions, or contributions, please open an issue in the GitHub repository.

---

**Note**: Make sure to keep your `credentials.json`, `token.json`, and `.env` files secure and never commit them to version control.
