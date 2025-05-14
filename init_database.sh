#!/bin/bash

# TukkerLa Database Initialization Script
# --------------------------------------
# This script will:
# 1. Create the PostgreSQL database
# 2. Run Alembic migrations
# 3. Seed the database with initial data

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration - edit these as needed
DB_NAME="tukkerla"
DB_USER="postgres"
DB_PASSWORD="password"  # Change this to your PostgreSQL password
DB_HOST="localhost"
DB_PORT="5432"

# Function to display status messages
function echo_status() {
    echo -e "${GREEN}[+] $1${NC}"
}

# Function to display errors
function echo_error() {
    echo -e "${RED}[!] $1${NC}"
}

# Function to display warnings
function echo_warning() {
    echo -e "${YELLOW}[!] $1${NC}"
}

# Display welcome message
echo_status "Starting TukkerLa database initialization..."
echo "This script will create and set up the database for your TukkerLa application."
echo "Make sure PostgreSQL is running before continuing."
echo ""
echo "Database settings:"
echo "  - Name: $DB_NAME"
echo "  - User: $DB_USER"
echo "  - Host: $DB_HOST:$DB_PORT"
echo ""
read -p "Continue? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo_status "Initialization canceled."
    exit 0
fi

# Check if PostgreSQL is installed and running
echo_status "Checking PostgreSQL connection..."
if ! command -v psql &> /dev/null; then
    echo_error "PostgreSQL client (psql) not found. Please install PostgreSQL."
    exit 1
fi

if ! PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c '\q' &> /dev/null; then
    echo_error "Could not connect to PostgreSQL. Make sure it's running and credentials are correct."
    exit 1
fi

# Check if database already exists
echo_status "Checking if database already exists..."
if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
    echo_warning "Database '$DB_NAME' already exists."
    read -p "Drop and recreate? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo_status "Dropping database '$DB_NAME'..."
        PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "DROP DATABASE $DB_NAME;" postgres
    else
        echo_warning "Continuing with the existing database. This might cause conflicts if schema has changed."
    fi
fi

# Create database if it doesn't exist
if ! PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
    echo_status "Creating database '$DB_NAME'..."
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "CREATE DATABASE $DB_NAME;" postgres
    if [ $? -ne 0 ]; then
        echo_error "Failed to create database. Check PostgreSQL settings and permissions."
        exit 1
    fi
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo_status "Creating .env file with database configuration..."
    cat > .env << EOF
# Database configuration
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}

# Security settings
SECRET_KEY=change_this_to_a_random_secret_key_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Upload directory for images
UPLOAD_DIRECTORY=static/images

# Google OAuth settings (required for Google authentication)
# GOOGLE_CLIENT_ID=your_google_client_id
# GOOGLE_CLIENT_SECRET=your_google_client_secret
EOF
    echo_status ".env file created. Please review and update as needed."
else
    echo_warning ".env file already exists. Make sure it contains the correct database URL."
fi

# Create the upload directory if it doesn't exist
if [ ! -d "static/images" ]; then
    echo_status "Creating image upload directory..."
    mkdir -p static/images
fi

# Set up virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo_status "Setting up Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo_status "Using existing virtual environment..."
    source venv/bin/activate
fi

# Run database migrations
echo_status "Running database migrations..."
python -m alembic upgrade head
if [ $? -ne 0 ]; then
    echo_error "Migration failed. Check the error message above."
    exit 1
fi

# Seed initial data (categories, locations, admin user)
echo_status "Seeding initial data..."

# Generate a random password for the admin user
ADMIN_PASSWORD=$(openssl rand -base64 12)

# Create a Python script for seeding the database
cat > seed_data.py << EOF
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.items import Category, Location
from app.models.users import User
from app.services.auth import get_password_hash
import os

# Get database URL from environment
database_url = os.getenv('DATABASE_URL')
if not database_url:
    print("DATABASE_URL not found in environment")
    exit(1)

# Create database connection
engine = create_engine(database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Seed categories
categories = [
    "Meat", "Poultry", "Seafood", "Vegetables", "Fruits", 
    "Dairy", "Leftovers", "Ready Meals", "Desserts", "Bread",
    "Sauces", "Other"
]

for cat_name in categories:
    if not db.query(Category).filter(Category.name == cat_name).first():
        db.add(Category(name=cat_name))

# Seed locations
locations = [
    "Top Drawer", "Middle Drawer", "Bottom Drawer", 
    "Door Shelf", "Left Side", "Right Side", "Back"
]

for loc_name in locations:
    if not db.query(Location).filter(Location.name == loc_name).first():
        db.add(Location(name=loc_name))

# Create admin user if it doesn't exist
if not db.query(User).filter(User.username == "admin").first():
    admin_pass = "${ADMIN_PASSWORD}"
    hashed_password = get_password_hash(admin_pass)
    db.add(User(
        username="admin",
        email="admin@example.com",
        password_hash=hashed_password,
        is_admin=True,
        auth_provider="local"
    ))
    print(f"Admin user created with password: {admin_pass}")
else:
    print("Admin user already exists")

# Commit changes
db.commit()
db.close()

print("Database seeding completed successfully")
EOF

# Run the seeding script
python seed_data.py
if [ $? -ne 0 ]; then
    echo_error "Data seeding failed. Check the error message above."
    exit 1
fi

# Clean up
rm seed_data.py

echo_status "Database initialization completed successfully!"
echo_status "Your TukkerLa application is now ready to use."
echo ""
echo "To start the application, run:"
echo "  uvicorn app.main:app --reload"
echo ""
echo "Or with Docker:"
echo "  docker-compose up -d"
echo ""
echo "API will be available at: http://localhost:8000"
echo "API documentation at: http://localhost:8000/docs"
echo ""
echo "Admin credentials:"
echo "  Username: admin"
echo "  Password: $ADMIN_PASSWORD"
echo ""
echo_warning "IMPORTANT: Save these credentials and change the password in production!" 