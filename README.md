# MeetingIQ Pro Backend

## Overview

This is the backend service for MeetingIQ Pro, providing media analysis capabilities including:
- Video/Audio file processing
- AI-powered transcription using Groq Whisper
- Meeting analysis using OpenAI GPT-4
- Chapter extraction with thumbnail generation
- Non-blocking asynchronous processing pipeline

## System Requirements

- Python 3.9 or higher
- FFmpeg (for video processing)
- PostgreSQL 12+ (or Supabase)

## Installation

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

**For Production:**
```bash
pip install -r requirements-prod.txt
```

**For Development:**
```bash
pip install -r requirements-dev.txt
```

**Full Dependencies (includes testing/dev tools):**
```bash
pip install -r requirements.txt
```

### 3. Install FFmpeg

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
Download from [FFmpeg official website](https://ffmpeg.org/download.html)

### 4. Environment Configuration

Create a `.env` file in the backend directory:

```env
# Database
DATABASE_URL=postgresql://username:password@localhost/meetingiq_db

# Supabase (if using)
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key

# AI Services
OPENAI_API_KEY=your_openai_api_key
GROQ_API_KEY=your_groq_api_key

# Server
DEBUG=True
HOST=0.0.0.0
PORT=8000

# Security
SECRET_KEY=your_secret_key_here
```

## Running the Application

### Development Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### Media Analysis
- `POST /media/{media_id}/analyze` - Start analysis (non-blocking)
- `GET /media/{media_id}/analysis/status` - Check analysis status
- `GET /media/{media_id}/analysis` - Get analysis results

### Media Management
- `GET /generate-presigned-url` - Get upload URL
- `POST /update-media-status` - Update media metadata
- `GET /get-user-media` - List user's media files

## Dependencies Breakdown

### Core Framework
- **FastAPI**: Modern async web framework
- **uvicorn**: ASGI server for production
- **pydantic**: Data validation and serialization

### Database
- **SQLAlchemy**: Async ORM for database operations
- **asyncpg**: PostgreSQL async driver
- **alembic**: Database migrations

### Storage & External Services
- **supabase**: Backend-as-a-Service integration
- **aiohttp**: Async HTTP client
- **openai**: OpenAI API client (async)
- **groq**: Groq API for transcription

### Media Processing
- **opencv-python**: Video frame extraction
- **ffmpeg-python**: Video-to-audio conversion (wrapper)

### Security & Authentication
- **python-jose**: JWT token handling
- **passlib**: Password hashing
- **cryptography**: Encryption utilities

### Development Tools
- **pytest**: Testing framework
- **black**: Code formatting
- **flake8**: Linting
- **mypy**: Type checking

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_analysis.py
```

## Performance Optimizations

This backend implements several optimizations for handling media processing:

1. **Non-blocking API responses** - Immediate response while processing in background
2. **Async processing pipeline** - All I/O operations are non-blocking
3. **Thread pool execution** - CPU-intensive tasks run in separate threads
4. **Independent database sessions** - Background tasks use separate DB sessions
5. **Resource cleanup** - Proper disposal of temporary files and connections

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI       │────│  Background      │────│  External APIs  │
│   Controllers   │    │  Tasks           │    │  (OpenAI, Groq) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   SQLAlchemy    │    │  Media Analysis  │    │  Supabase       │
│   Database      │    │  Service         │    │  Storage        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Monitoring & Logging

The application includes structured logging and error handling:
- All analysis operations are logged with timestamps
- Failed analyses update status appropriately
- Background task errors don't crash the main application

## Deployment

### Docker (Recommended)

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements-prod.txt .
RUN pip install -r requirements-prod.txt

COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables for Production

Ensure these are set in production:
- `DATABASE_URL`: PostgreSQL connection string
- `OPENAI_API_KEY`: Your OpenAI API key
- `GROQ_API_KEY`: Your Groq API key
- `SUPABASE_URL` & `SUPABASE_KEY`: Supabase credentials
- `SECRET_KEY`: Secure random key for JWT

## Contributing

1. Install development dependencies: `pip install -r requirements-dev.txt`
2. Run tests: `pytest`
3. Format code: `black app/`
4. Check types: `mypy app/`
5. Lint: `flake8 app/`

## License

[Your License Here] 