# AI Loan Platform Backend

This is the backend service for the AI-powered loan approval platform. It provides RESTful APIs for user authentication, loan application processing, document verification, and payment processing.

## Features

- User authentication and authorization using JWT
- Multi-step loan application processing
- AI-powered loan assessment
- Document verification via DigiLocker and eKYC
- Payment processing with Razorpay
- Detailed loan assessment report generation
- Secure file upload and handling
- Comprehensive error handling and logging

## Tech Stack

- Python 3.8+
- Flask
- SQLAlchemy
- JWT Authentication
- Razorpay SDK
- ReportLab
- DigiLocker API
- eKYC Integration

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration values
```

4. Initialize the database:
```bash
flask db upgrade
```

5. Run the development server:
```bash
python run.py
```

## Project Structure

```
backend/
├── __init__.py          # Application factory
├── app.py              # Main application setup
├── config.py           # Configuration classes
├── models.py           # Database models
├── routes.py           # API routes
├── error_handlers.py   # Error handling
├── utils.py            # Utility functions
├── requirements.txt    # Dependencies
└── modules/
    ├── loan_assessment.py       # Loan assessment logic
    ├── document_verification.py # Document verification
    ├── payment_gateway.py      # Payment processing
    └── report_generator.py     # Report generation
```

## API Endpoints

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

## Environment Variables

Required environment variables:

- `FLASK_ENV` - Application environment (development/production)
- `SECRET_KEY` - Flask secret key
- `DATABASE_URL` - Database connection URL
- `JWT_SECRET_KEY` - JWT encryption key
- `DIGILOCKER_CLIENT_ID` - DigiLocker API client ID
- `DIGILOCKER_CLIENT_SECRET` - DigiLocker API client secret
- `RAZORPAY_KEY_ID` - Razorpay API key ID
- `RAZORPAY_KEY_SECRET` - Razorpay API secret key

See `.env.example` for all available configuration options.

## Security

- JWT-based authentication
- Password hashing with bcrypt
- CORS protection
- Input validation
- File type verification
- Secure session configuration
- Rate limiting
- Error logging

## Development

1. Create a new branch for features:
```bash
git checkout -b feature/your-feature-name
```

2. Run tests:
```bash
python -m pytest
```

3. Check code style:
```bash
flake8 .
```

4. Submit pull request

## Production Deployment

1. Set environment variables for production
2. Configure production database
3. Set up logging
4. Configure web server (e.g., Gunicorn)
5. Set up SSL certificate
6. Configure reverse proxy (e.g., Nginx)

## Error Handling

The application includes comprehensive error handling:

- Custom error classes for different scenarios
- Detailed error logging
- User-friendly error responses
- Production/development error differentiation

## Logging

Logs are stored in the `logs` directory:

- Application logs: `logs/app.log`
- Error logs: `logs/error.log`
- Access logs: `logs/access.log`

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Submit pull request

## License

MIT License - see LICENSE file for details