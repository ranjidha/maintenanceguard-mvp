# MaintenanceGuard MVP

A proof-of-concept vehicle maintenance tracking and upsell detection system.

## Features

- 🚗 Vehicle profile management (Year/Make/Model)
- 📄 Invoice upload with OCR extraction
- 🤖 AI-powered invoice parsing using Claude
- 📊 Maintenance timeline and history
- 💡 Evidence-based recommendations with OEM schedule grounding
- 🚨 Upsell detection and flagging

## Tech Stack

- **Backend**: Python 3.11, FastAPI
- **Frontend**: React 18, Tailwind CSS, Vite
- **Database**: PostgreSQL 15 with pgvector
- **LLM**: Anthropic Claude API
- **OCR**: Tesseract OCR
- **Container**: Docker & Docker Compose

## Prerequisites

- Docker Desktop installed ([Download](https://www.docker.com/products/docker-desktop))
- Anthropic API Key ([Get one](https://console.anthropic.com/))
- Git

## Quick Start

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd maintenanceguard-mvp
```

### 2. Set Up Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your Anthropic API key
nano .env
```

Required environment variables:
```
ANTHROPIC_API_KEY=your_api_key_here
DATABASE_URL=postgresql://postgres:postgres@db:5432/maintenanceguard
```

### 3. Start the Application

```bash
# Build and start all services
docker compose up --build

# Or run in detached mode
docker compose up -d
```

The application will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 4. Initialize the Database

```bash
# Run migrations (first time only)
docker compose exec backend python -m app.utils.init_db
```

## Development

### Backend Development

```bash
# View backend logs
docker compose logs -f backend

# Run tests
docker compose exec backend pytest

# Access backend shell
docker compose exec backend bash
```

### Frontend Development

```bash
# View frontend logs
docker compose logs -f frontend

# Access frontend shell
docker compose exec frontend sh

# Install new npm packages
docker compose exec frontend npm install <package-name>
```

### Database Access

```bash
# Access PostgreSQL CLI
docker compose exec db psql -U postgres -d maintenanceguard

# Run SQL file
docker compose exec db psql -U postgres -d maintenanceguard -f /path/to/file.sql
```

## Project Structure

```
maintenanceguard-mvp/
├── backend/
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── models/       # SQLAlchemy models
│   │   ├── services/     # Business logic
│   │   └── utils/        # Utilities
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── services/     # API clients
│   │   └── utils/        # Utilities
│   ├── package.json
│   └── Dockerfile
├── database/
│   ├── migrations/       # SQL migrations
│   └── seeds/           # Sample data
├── docker-compose.yml
└── README.md
```

## API Documentation

Once running, visit http://localhost:8000/docs for interactive API documentation.

### Key Endpoints

- `POST /api/vehicles` - Create vehicle profile
- `GET /api/vehicles/{id}` - Get vehicle details
- `POST /api/invoices/upload` - Upload invoice
- `GET /api/invoices/{id}` - Get invoice details
- `POST /api/recommendations` - Get maintenance recommendations
- `GET /api/timeline/{vehicle_id}` - Get maintenance timeline

## Usage Guide

### 1. Create a Vehicle Profile

1. Navigate to the dashboard
2. Click "Add Vehicle"
3. Enter Year, Make, Model (e.g., 2020, Toyota, Camry)
4. Click "Save"

### 2. Upload Invoice

1. Select your vehicle
2. Click "Upload Invoice"
3. Choose PDF/JPG file
4. Wait for OCR processing
5. Review extracted data
6. Confirm and save

### 3. View Recommendations

1. Click "Get Recommendations" on vehicle card
2. Review categorized recommendations:
   - ✅ Recommended Now
   - ⏰ Due Soon
   - 💎 Optional Enhancement
   - ⚠️ Not Typically Required (potential upsell)

## Configuration

### OEM Schedule Data

Sample OEM schedules are included for:
- Toyota Camry 2018-2023
- Honda Accord 2018-2023
- Ford F-150 2018-2023

To add more vehicles, add JSON files to `database/seeds/oem_schedules/`.

### LLM Configuration

Edit `backend/app/services/llm_service.py` to adjust:
- Model selection (claude-3-5-sonnet-20241022)
- Temperature
- Max tokens
- System prompts

## Troubleshooting

### "Connection refused" errors

```bash
# Restart services
docker compose restart

# Check service status
docker compose ps
```

### OCR not working

```bash
# Rebuild backend with Tesseract
docker compose build backend
docker compose up -d
```

### Database connection errors

```bash
# Reset database
docker compose down -v
docker compose up -d db
# Wait 10 seconds for DB to initialize
docker compose up -d
```

### Clear all data and restart

```bash
docker compose down -v
docker compose up --build
```

## Using with Claude Code

If you want to use Claude Code (Anthropic's CLI agent) for development:

```bash
# Install Claude Code (if not already installed)
npm install -g @anthropic-ai/claude-code

# Run Claude Code in project directory
claude-code

# Example: Ask Claude Code to add a feature
> "Add email notification when invoice processing completes"
```

## Testing

### Run All Tests

```bash
docker compose exec backend pytest
```

### Run Specific Test File

```bash
docker compose exec backend pytest tests/test_invoice_service.py -v
```

### Test Coverage

```bash
docker compose exec backend pytest --cov=app tests/
```

## Deployment

### Production Checklist

- [ ] Set strong database password
- [ ] Enable HTTPS
- [ ] Set up proper authentication
- [ ] Configure CORS properly
- [ ] Set up monitoring (logs, metrics)
- [ ] Configure backups
- [ ] Set rate limiting
- [ ] Review security headers

### Deploy to Cloud

See `docs/DEPLOYMENT.md` for deployment guides for:
- AWS ECS/Fargate
- Google Cloud Run
- Railway
- DigitalOcean

## Contributing

This is a proof-of-concept project. For improvements:

1. Fork the repository
2. Create feature branch
3. Make changes
4. Submit pull request

## License

MIT License - See LICENSE file

## Support

For issues, please create a GitHub issue with:
- Error message
- Steps to reproduce
- Docker logs (`docker compose logs`)

## Roadmap

- [ ] Add user authentication
- [ ] Multi-vehicle support per user
- [ ] Email/SMS reminders
- [ ] Mobile app (React Native)
- [ ] VIN decoder integration
- [ ] More OEM schedule coverage
- [ ] Cost estimation for services
- [ ] Service provider directory

## Notes

This is an MVP/PoC focusing on core functionality. Production deployment requires:
- Proper authentication/authorization
- Rate limiting
- Input validation
- Security hardening
- Error handling
- Monitoring
- Backups
