# 🚀 MateHub - AI Character Chat Platform

MateHub is a sophisticated AI-powered chat platform that enables users to interact with AI characters through immersive storytelling experiences. Built with FastAPI backend and vanilla JavaScript frontend, it features advanced chat management, character relationships, and smart scrolling capabilities.

## ✨ Key Features

### 🎭 Character & Story Management
- **Multi-Character Support**: Chat with different AI characters
- **Story-based Conversations**: Each character can have multiple storylines
- **Character Images**: Dynamic character image management with offset and bounty system
- **User-Story Matching**: Track user progress and intimacy levels with characters

### 💬 Advanced Chat System
- **Real-time Chat**: Seamless messaging with AI characters
- **Typewriter Effect**: Immersive message display with typing animation
- **Smart Scrolling**: Intelligent scroll behavior that respects user reading position
- **Message History**: Cursor-based pagination for efficient history loading
- **Status Tracking**: Real-time chat status monitoring and error handling

### 🎯 Smart User Experience
- **Auto-load Latest Messages**: Page refresh loads only recent conversations
- **Reading Protection**: Won't interrupt users while reading older messages
- **Infinite Scroll**: Automatic history loading when scrolling to top
- **Responsive Design**: Works seamlessly across different screen sizes

## 🏗️ Architecture

### Backend (FastAPI)
```
backend/
├── app/
│   ├── api/                    # API route handlers
│   │   ├── character/          # Character management endpoints
│   │   ├── story/              # Story management endpoints
│   │   ├── chat/               # Chat functionality endpoints
│   │   ├── profile/            # User profile endpoints
│   │   └── signin/             # Authentication endpoints
│   ├── database/               # Database layer
│   │   ├── models.py           # SQLAlchemy models
│   │   ├── schemas.py          # Pydantic schemas
│   │   ├── services.py         # Business logic services
│   │   └── connection.py       # Database connection
│   ├── llm/                    # LLM integration
│   └── config.py               # Application configuration
├── migrations/                 # Alembic database migrations
└── requirements.txt            # Python dependencies
```

### Frontend (Vanilla JavaScript)
```
frontend/
├── index.html                  # Main chat interface
├── styles.css                  # Styling and responsive design
├── script.js                   # Application initialization
├── chat-client.js              # Core chat functionality
└── api-service.js              # API communication layer
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Poetry (Python dependency management)
- PostgreSQL
- Redis (for caching)
- Celery (for background tasks)

### Poetry Installation
If you don't have Poetry installed:
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Or using pip
pip install poetry

# Verify installation
poetry --version
```

### Backend Setup

1. **Clone the repository**
```bash
git clone git@github.com:okpo65/matehub.git
cd matehub
```

2. **Set up Python environment with Poetry**
```bash
cd backend

# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

3. **Configure environment variables**
```bash
cp ops/.env.example .env
# Edit .env with your database and API configurations
```

4. **Set up database**
```bash
# Create PostgreSQL database
createdb matehub

# Run migrations
poetry run alembic upgrade head
```

5. **Start the backend server**
```bash
# Using Poetry
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or if you're in the poetry shell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. **Navigate to frontend directory**
```bash
cd frontend
```

2. **Serve the frontend** (choose one method)
```bash
# Using Python's built-in server
python -m http.server 3000

# Using Node.js (if you have it installed)
npx serve -p 3000

# Or simply open index.html in your browser
```

3. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## 🎯 Smart Features

### 🔄 Intelligent Chat Loading
- **Initial Load**: Loads only the latest 20 messages for fast startup
- **Cursor-based Pagination**: Efficient loading of older messages
- **No Unnecessary API Calls**: Optimized to prevent redundant requests

### 📍 Smart Scrolling System
```javascript
// Detects user position and scrolls intelligently
isScrolledToBottom() {
    const threshold = 50; // 50px tolerance
    return scrollTop + clientHeight >= scrollHeight - threshold;
}

// Conditional scrolling based on user behavior
if (wasAtBottom || forceScroll) {
    this.scrollToBottom();
}
```

### 🎭 Character Management
- **Dynamic Character Selection**: Switch between different AI characters
- **Story Context**: Each conversation maintains story-specific context
- **Progress Tracking**: Monitor user progress and relationship levels

## 📊 Database Schema

### Core Models
- **User**: User accounts and profiles
- **Character**: AI character definitions and settings
- **Story**: Storylines associated with characters
- **CharacterImage**: Character visual assets with positioning
- **StoryUserMatch**: User progress tracking per story
- **StoryChatHistory**: Complete chat message history
- **Chat**: Chat session management

### Relationships
```sql
User 1:N Profile
User 1:N StoryUserMatch
Character 1:N Story
Character 1:N CharacterImage
Story 1:N StoryUserMatch
Story 1:N StoryChatHistory
```

## 🔧 API Endpoints

### Character Management
- `GET /characters/` - List all characters with stories
- `GET /characters/{id}` - Get character details
- `GET /characters/{id}/photos` - Get character images
- `GET /characters/popular` - Get popular characters

### Story Management
- `GET /stories/character/{id}` - Get stories by character
- `GET /stories/{id}` - Get story details
- `POST /stories/user-match` - Create user-story match
- `PUT /stories/user-match/{id}/progress` - Update progress

### Chat System
- `POST /chat/send` - Send chat message
- `GET /chat/history` - Get chat history with pagination
- `GET /chat_history/{id}` - Get specific chat message
- `GET /chat_history_status/{id}` - Check message processing status

## 🎨 Frontend Features

### Smart Chat Client
```javascript
class ChatClient {
    // Intelligent message loading
    async loadChatHistory() {
        // Loads latest messages without cursor
        const response = await this.apiService.getLatestChatHistory(
            this.config.userId, 
            this.config.storyId, 
            20 // Latest 20 messages only
        );
    }
    
    // Smart scrolling behavior
    async sendMessage() {
        const isAtBottom = this.isScrolledToBottom();
        // Only auto-scroll if user was at bottom
        this.addMessageWithTypewriter(response, 'received', false, null, isAtBottom);
    }
}
```

### Configuration Management
- **Persistent Settings**: User preferences saved in localStorage
- **Dynamic Updates**: Real-time configuration changes
- **ID Management**: Easy switching between users, characters, and stories

## 🔧 Development

### Poetry Commands
```bash
# Install dependencies
poetry install

# Add new dependency
poetry add package-name

# Add development dependency
poetry add --group dev package-name

# Update dependencies
poetry update

# Show dependency tree
poetry show --tree

# Export requirements.txt (if needed)
poetry export -f requirements.txt --output requirements.txt
```

### Environment Management
```bash
# Activate virtual environment
poetry shell

# Run commands in virtual environment
poetry run python script.py
poetry run uvicorn app.main:app --reload

# Deactivate (when in shell)
exit
```

## 🧪 Testing

### Backend Testing
```bash
cd backend
poetry run pytest tests/ -v
```

### Frontend Testing
- Open browser developer tools
- Check console for debug messages
- Test scroll behavior and message loading
- Verify API communication

## 🚀 Deployment

### Backend Deployment
1. Set up production database
2. Configure environment variables
3. Install dependencies with Poetry: `poetry install --only=main`
4. Run database migrations: `poetry run alembic upgrade head`
5. Deploy with gunicorn: `poetry run gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker`

### Frontend Deployment
1. Build static assets (if using build tools)
2. Deploy to CDN or static hosting service
3. Configure API endpoints for production

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 Recent Updates

### v1.2.0 - Smart Scrolling System
- ✅ Implemented intelligent scroll behavior
- ✅ Added reading position protection
- ✅ Optimized initial message loading
- ✅ Removed unnecessary API calls during message sending

### v1.1.0 - Enhanced Chat Features
- ✅ Added cursor-based pagination
- ✅ Implemented typewriter effect
- ✅ Added message status tracking
- ✅ Enhanced error handling

### v1.0.0 - Initial Release
- ✅ Core chat functionality
- ✅ Character and story management
- ✅ Database schema and migrations
- ✅ RESTful API design

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with FastAPI for high-performance backend
- Uses PostgreSQL for reliable data storage
- Vanilla JavaScript for lightweight frontend
- Alembic for database migration management

---

**MateHub** - Where AI characters come to life through intelligent conversations! 🎭✨
