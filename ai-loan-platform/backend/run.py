import os
from dotenv import load_dotenv
from backend import create_app

# Load environment variables
load_dotenv()

# Create Flask application
app = create_app()

if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.getenv('PORT', 5000))
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=port,
        debug=app.config['DEBUG']
    )