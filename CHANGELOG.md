# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-08-23

### Added
- Smart scrolling system with user position detection
- `isScrolledToBottom()` method for intelligent scroll behavior
- Conditional scrolling to prevent reading interruption
- Enhanced initial page load with latest messages only
- Reading protection during message sending

### Changed
- **BREAKING**: `addMessage()` and `addMessageWithTypewriter()` now accept `forceScroll` parameter
- **BREAKING**: `sendMessage()` no longer makes unnecessary chat/history API calls
- Optimized `loadChatHistory()` to load only latest 20 messages on page refresh
- Improved scroll behavior to respect user reading position
- Enhanced welcome message with smart scrolling feature descriptions

### Fixed
- Removed unnecessary API calls during message sending when user is at bottom
- Fixed scroll interruption while users are reading older messages
- Improved initial page load performance by avoiding full history load

### Technical Details
- Added smart scroll detection with 50px threshold
- Implemented conditional auto-scrolling based on user position
- Optimized database queries to prevent N+1 problems
- Enhanced error handling for SQLAlchemy model relationships

## [1.1.0] - 2025-08-22

### Added
- Comprehensive database schema with proper relationships
- Service layer architecture for better code organization
- Cursor-based pagination for efficient chat history loading
- Character and story management with full CRUD operations
- Typewriter effect for immersive message display

### Changed
- Migrated from raw SQLAlchemy queries to service layer
- Improved API response models with Pydantic schemas
- Enhanced error handling and validation

### Fixed
- SQLAlchemy relationship loading issues
- Import conflicts between models and schemas
- Database connection and session management

## [1.0.0] - 2025-08-18

### Added
- Initial release of MateHub platform
- FastAPI backend with PostgreSQL database
- Vanilla JavaScript frontend with real-time chat
- Character and story management system
- User authentication and profile management
- Basic chat functionality with AI integration
- Database migrations with Alembic
- RESTful API design with comprehensive documentation

### Features
- Multi-character chat support
- Story-based conversations
- Real-time message status tracking
- Responsive web interface
- Configuration management
- Health check endpoints

---

## Development Notes

### Database Schema Evolution
- v1.0.0: Basic schema with core entities
- v1.1.0: Added proper relationships and constraints
- v1.2.0: Optimized queries and added smart loading

### Frontend Evolution
- v1.0.0: Basic chat interface
- v1.1.0: Enhanced UX with typewriter effects
- v1.2.0: Smart scrolling and reading protection

### API Evolution
- v1.0.0: Basic CRUD operations
- v1.1.0: Service layer with optimized queries
- v1.2.0: Reduced unnecessary API calls and improved performance
