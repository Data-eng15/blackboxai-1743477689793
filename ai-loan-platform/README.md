# AI Loan Platform

An AI-powered automatic loan approval platform that provides instant loan assessments and connects borrowers with suitable lenders.

## Features

- User registration and authentication
- Multi-step loan application process
- Document verification via DigiLocker and e-Aadhaar eKYC
- AI-powered loan assessment
- Secure document upload and handling
- Payment integration with Razorpay
- Detailed loan assessment reports
- Lender matching system

## Tech Stack

### Backend
- Python 3.9
- Flask
- SQLAlchemy
- JWT Authentication
- PostgreSQL
- Razorpay SDK
- ReportLab
- DigiLocker API
- eKYC Integration

### Frontend
- HTML5
- Tailwind CSS
- JavaScript
- Font Awesome
- Google Fonts

### Infrastructure
- Docker
- Nginx
- Gunicorn
- SSL/TLS

## Project Structure

```
ai-loan-platform/
├── backend/                 # Flask backend application
│   ├── tests/              # Test files
│   ├── app.py             # Main application file
│   ├── models.py          # Database models
│   ├── routes.py          # API routes
│   ├── config.py          # Configuration
│   └── requirements.txt   # Python dependencies
├── frontend/              # Static frontend files
│   ├── assets/           # Static assets
│   ├── index.html        # Landing page
│   └── js/              # JavaScript files
├── nginx/                # Nginx configuration
│   ├── conf.d/          # Server configuration
│   └── ssl/             # SSL certificates
└── docker-compose.yml   # Docker composition
```

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-loan-platform.git
cd ai-loan-platform
```

2. Set up environment variables:
```bash
cp backend/.env.example backend/.env
# Edit .env with your configuration
```

3. Generate SSL certificates (development only):
```bash
cd nginx/ssl
./generate-certs.sh
```

4. Build and run with Docker:
```bash
docker-compose up --build
```

The application will be available at:
- Frontend: https://localhost
- Backend API: https://localhost/api

## Development Setup

### Backend

1. Set up Python environment:
```bash
cd backend
./setup.sh
```

2. Run tests:
```bash
./run_tests.sh
```

3. Start development server:
```bash
python run.py
```

### Frontend

The frontend is static HTML/CSS/JS and can be served directly from the `frontend` directory or through Nginx in the Docker setup.

## API Documentation

### Authentication
- POST `/api/auth/register` - Register new user
- POST `/api/auth/login` - User login

### Loan Application
- POST `/api/loan/apply` - Submit loan application
- GET `/api/loan/application/<id>` - Get application status

### Document Verification
- GET `/api/document/digilocker/auth` - Get DigiLocker auth URL
- GET `/api/document/digilocker/callback` - Handle DigiLocker callback
- POST `/api/document/upload` - Upload documents manually

### Payment
- POST `/api/payment/create-order` - Create payment order
- POST `/api/payment/verify` - Verify payment

## Security Features

- JWT-based authentication
- SSL/TLS encryption
- CORS protection
- Input validation
- File type verification
- Secure session configuration
- Rate limiting
- Error logging

## Testing

The project includes comprehensive tests:
- Unit tests
- Integration tests
- API tests
- Model tests
- Utility function tests

Run tests with coverage reporting:
```bash
cd backend
./run_tests.sh
```

## Deployment

1. Update environment variables for production
2. Generate proper SSL certificates
3. Update Nginx configuration if needed
4. Build and deploy:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Submit pull request

## License

MIT License - see LICENSE file for details

## Support

For support, email support@example.com or create an issue in the repository.