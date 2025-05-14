# TukkerLa Freezer Tracker

A Python/PostgreSQL-based application to track and manage food items in your freezer.

## Features

- **Item Management**: Track freezer items with detailed information
- **Image Support**: Store multiple images for each item
- **Barcode Scanning**: Scan and catalog barcodes for easy identification
- **Expiry Tracking**: Monitor when items will expire
- **Multi-User**: Designed for household use with multiple users
- **Categories & Locations**: Organize items by type and location in the freezer

## Technology Stack

- **Backend**: Python with FastAPI
- **Database**: PostgreSQL
- **Authentication**: JWT token-based auth
- **Image Processing**: PIL and OpenCV
- **Barcode Scanning**: pyzbar

## Installation

### Prerequisites

1. Python 3.8+
2. PostgreSQL 12+
3. pip and virtualenv

### Setup

1. Clone this repository:
```bash
git clone https://your-repository-url/tukkerla.git
cd tukkerla
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the database:
```bash
# Create PostgreSQL database
createdb tukkerla

# Run database migrations
alembic upgrade head
```

5. Create an `.env` file with configuration (copy from `env.example`):
```bash
cp env.example .env
# Then edit .env to add your settings
```

6. Start the application:
```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000, and the Swagger documentation at http://localhost:8000/docs.

## API Endpoints

The API provides the following functionality:

- **Authentication**
  - `/auth/register` - Register a new user
  - `/auth/token` - Login and get access token
  - `/auth/me` - Get current user info

- **Items**
  - `/items` - CRUD operations for freezer items
  - `/items/{id}` - Get/update/delete specific items
  
- **Images**
  - `/images/{item_id}` - Upload images for items
  - `/images/{image_id}` - Manage existing images
  
- **Barcodes**
  - `/barcodes/scan` - Scan and process barcode images
  - `/barcodes/products` - Manage known barcode products
  
- **Categories & Locations**
  - `/categories` - Manage food categories
  - `/locations` - Manage freezer locations

## Deployment

For production deployment:

1. Use a proper PostgreSQL setup with regular backups
2. Configure HTTPS with a reverse proxy (nginx/apache)
3. Set up proper environment variables
4. Consider using Docker for containerization

## Frontend Development

This repo contains the backend API only. For frontend development:

- Use the Swagger documentation to understand available endpoints
- Consider building a web frontend with React/Vue/Angular
- For mobile, React Native or Flutter are good options with camera support

## License

[Your chosen license] 