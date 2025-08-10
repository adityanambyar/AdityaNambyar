# MeetNotes India 🇮🇳

A privacy-focused, India-first meeting transcription and summarization platform built with FastAPI, React, and Whisper AI.

## 🌟 Features

- **Audio Upload**: Support for M4A, MP3, WAV files up to 200MB
- **AI Transcription**: Powered by OpenAI Whisper with language detection
- **India-First Localization**: Preserves Tamil/Hindi text with English glosses
- **Smart Summaries**: Extracts decisions, action items, and open questions
- **WhatsApp Integration**: Generates shareable summaries (≤900 chars)
- **PDF Minutes**: Professional meeting minutes with timestamps
- **Privacy Focus**: Auto-deletion after 24 hours with manual override
- **Robust Architecture**: Exponential backoff, comprehensive error handling

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend│    │  FastAPI Backend│    │  PostgreSQL DB  │
│   (Vite + TS)   │◄──►│  (Python 3.11) │◄──►│  (Data Storage)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │    │   MinIO Storage │    │   Redis Cache   │
│  (Static + API) │    │ (S3-Compatible) │    │  (Optional)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd meetnotes-india
```

### 2. Environment Configuration

```bash
# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit backend/.env with your configuration
DATABASE_URL=postgresql://meetnotes_user:meetnotes_password@localhost:5432/meetnotes
REDIS_URL=redis://localhost:6379
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin123
S3_BUCKET=meetnotes-audio
SECRET_KEY=your-secret-key-here
```

### 3. Start Services

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f backend
```

### 4. Access Applications

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin123)
- **PostgreSQL**: localhost:5432

## 🧪 Testing

### Backend Tests

```bash
# Run all tests
cd backend
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m e2e           # End-to-end tests only
pytest -m "not slow"    # Exclude slow tests

# Run end-to-end test specifically
pytest tests/test_e2e.py::TestEndToEnd::test_full_workflow_15s_sample -v
```

### Frontend Tests

```bash
# Run all tests
cd frontend
npm test

# Run with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch
```

### Test Coverage Requirements

- **Backend**: Minimum 80% coverage
- **Frontend**: Minimum 70% coverage
- **End-to-End**: Upload 15s sample → transcript+summary present, PDF bytes > 0

## 🔧 Development

### Backend Development

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run database migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Database Management

```bash
# Access PostgreSQL
docker-compose exec postgres psql -U meetnotes_user -d meetnotes

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

## 📊 API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/upload/` | Upload audio file (≤200MB) |
| `POST` | `/api/v1/transcribe/{id}` | Transcribe audio with Whisper |
| `POST` | `/api/v1/summarize/{id}` | Generate meeting summary |
| `GET` | `/api/v1/transcript/{id}` | Retrieve transcript |
| `GET` | `/api/v1/summary/{id}` | Retrieve summary |
| `GET` | `/api/v1/minutes/{id}/pdf` | Download PDF minutes |
| `DELETE` | `/api/v1/delete/{id}` | Delete audio file |

### File Support

- **Formats**: M4A, MP3, WAV
- **Max Size**: 200MB
- **Languages**: Auto-detection (English, Tamil, Hindi, etc.)

## 🌍 India-First Features

### Language Support

- **Tamil**: Full text preservation with English glosses
- **Hindi**: Native script support
- **English**: Primary interface language
- **Mixed**: Seamless code-switching support

### WhatsApp Integration

- **Character Limit**: ≤900 characters
- **Language Headers**: Tamil/Hindi/English as appropriate
- **Structured Format**: Decisions, Actions, Questions
- **Share Ready**: One-click sharing

## 🔒 Privacy & Security

### Data Retention

- **Audio Files**: Auto-deleted after 24 hours
- **Transcripts**: Stored until audio deletion
- **Summaries**: Preserved for reference
- **Manual Override**: Immediate deletion option

### Security Features

- **File Validation**: MIME type and size checks
- **Filename Sanitization**: Prevents path traversal
- **Rate Limiting**: API abuse prevention
- **Input Validation**: Comprehensive sanitization

## 🚀 Deployment

### Docker Deployment

```bash
# Build and push images
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml push

# Deploy to production
docker-compose -f docker-compose.prod.yml up -d
```

### Cloud Deployment

#### Render

1. Connect GitHub repository
2. Set environment variables
3. Deploy backend service
4. Deploy frontend static site

#### Fly.io

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Deploy backend
cd backend
fly launch
fly deploy

# Deploy frontend
cd frontend
fly launch
fly deploy
```

### Environment Variables

#### Backend (Production)

```bash
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://host:6379
S3_ENDPOINT=https://s3.amazonaws.com
S3_ACCESS_KEY=your_access_key
S3_SECRET_KEY=your_secret_key
S3_BUCKET=meetnotes-audio
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

#### Frontend (Production)

```bash
VITE_API_URL=https://api.yourdomain.com/api/v1
```

## 📈 Monitoring & Logging

### Health Checks

- **Backend**: `/health` endpoint
- **Frontend**: Built-in error boundaries
- **Database**: Connection pool monitoring
- **Storage**: S3/MinIO availability

### Logging

- **Structured Logging**: JSON format
- **Log Levels**: DEBUG, INFO, WARNING, ERROR
- **Request Tracing**: Correlation IDs
- **Performance Metrics**: Response times, throughput

## 🤝 Contributing

### Development Workflow

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes and add tests
4. Ensure all tests pass: `pytest && npm test`
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push to branch: `git push origin feature/amazing-feature`
7. Open Pull Request

### Code Standards

- **Python**: Black, isort, flake8
- **TypeScript**: ESLint, Prettier
- **Tests**: pytest, React Testing Library
- **Coverage**: Minimum thresholds enforced

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI Whisper**: Speech recognition technology
- **FastAPI**: Modern Python web framework
- **React**: Frontend framework
- **Tailwind CSS**: Utility-first CSS framework
- **India Open Source**: Community support

## 📞 Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Documentation**: [Wiki](wiki-link)
- **Email**: support@meetnotes.india

---

**Made with ❤️ in India** 🇮🇳