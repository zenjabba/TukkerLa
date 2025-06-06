#!/bin/bash

# TukkerLa Database Initialization Script for Docker
# -------------------------------------------------
# This script will:
# 1. Start the Docker containers if not running
# 2. Create the PostgreSQL database
# 3. Run Alembic migrations
# 4. Seed the database with initial data

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration - edit these as needed
DB_NAME="tukkerla"
DB_USER="postgres"
DB_PASSWORD="password"  # Should match docker-compose.yml
ADMIN_USERNAME="admin"
ADMIN_EMAIL="admin@example.com"

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
echo_status "Starting TukkerLa database initialization using Docker..."
echo "This script will create and set up the database for your TukkerLa application."
echo "Make sure Docker and the Docker Compose plugin are installed before continuing."
echo ""
read -p "Continue? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo_status "Initialization canceled."
    exit 0
fi

# Check if Docker is installed
echo_status "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo_error "Docker not found. Please install Docker."
    exit 1
fi

# Check Docker Compose functionality
if ! docker compose version &> /dev/null; then
    echo_error "Docker Compose functionality not found. Please make sure you have Docker with Compose plugin installed."
    exit 1
fi

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo_error "docker-compose.yml not found. Please make sure you're in the correct directory."
    exit 1
fi

# Ensure version attribute is removed from docker-compose.yml
if grep -q "^version:" docker-compose.yml; then
    echo_warning "Removing obsolete 'version' attribute from docker-compose.yml..."
    # Use a temporary file for sed on macOS or Linux
    sed -i.bak '/^version:/d' docker-compose.yml
    rm -f docker-compose.yml.bak
fi

# Stop any running containers to start fresh
echo_status "Stopping any running containers..."
docker compose down

# Start just the database container first
echo_status "Starting database container..."
docker compose up -d db

# Wait for the database to be ready
echo_status "Waiting for the database service to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0
    
while ! docker compose exec db pg_isready -h localhost -U postgres > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT+1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo_error "Database service not ready after maximum retries. Exiting."
        exit 1
    fi
    echo "Waiting for database to be ready... (Attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done
    
echo_status "Database service is ready."

# Check if database exists in the PostgreSQL container
echo_status "Checking if database already exists..."
if docker compose exec db psql -U $DB_USER -lqt | grep -q $DB_NAME; then
    echo_warning "Database '$DB_NAME' already exists."
    read -p "Drop and recreate? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo_status "Dropping database '$DB_NAME'..."
        docker compose exec db psql -U $DB_USER -c "DROP DATABASE $DB_NAME;" postgres
    else
        echo_warning "Continuing with the existing database. This might cause conflicts if schema has changed."
    fi
fi

# Create database if it doesn't exist
if ! docker compose exec db psql -U $DB_USER -lqt | grep -q $DB_NAME; then
    echo_status "Creating database '$DB_NAME'..."
    docker compose exec db psql -U $DB_USER -c "CREATE DATABASE $DB_NAME;" postgres
    if [ $? -ne 0 ]; then
        echo_error "Failed to create database. Check PostgreSQL settings and permissions."
        exit 1
    fi
fi

# Make sure the static directory exists with proper permissions
if [ ! -d "static/images" ]; then
    echo_status "Creating image upload directory..."
    mkdir -p static/images
    # Set proper permissions
    chmod -R 777 static/images
fi

# Run database migrations using a temporary container
echo_status "Running database migrations..."
docker compose run --rm api python -m alembic upgrade head
if [ $? -ne 0 ]; then
    echo_error "Migration failed. Check the error message above."
    exit 1
fi

# Generate a random password for admin user
ADMIN_PASSWORD=$(openssl rand -base64 12)

# Seed initial data (categories, locations, admin user)
echo_status "Seeding initial data..."

# Create a Python script for database seeding
cat > seed_script.py << EOF
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.items import Category, Location
from app.models.users import User
from app.services.auth import get_password_hash
import contextlib

# Categories to seed
categories = [
    "Meat", "Poultry", "Seafood", "Vegetables", "Fruits", 
    "Dairy", "Leftovers", "Ready Meals", "Desserts", "Bread",
    "Sauces", "Other"
]

# Locations to seed
locations = [
    "Top Drawer", "Middle Drawer", "Bottom Drawer", 
    "Door Shelf", "Left Side", "Right Side", "Back"
]

# Get database session
with contextlib.closing(next(get_db())) as db:
    # Add categories
    for cat_name in categories:
        if not db.query(Category).filter(Category.name == cat_name).first():
            db.add(Category(name=cat_name))
            print(f"Added category: {cat_name}")
    
    # Add locations
    for loc_name in locations:
        if not db.query(Location).filter(Location.name == loc_name).first():
            db.add(Location(name=loc_name))
            print(f"Added location: {loc_name}")
    
    # Add admin user if it doesn't exist
    if not db.query(User).filter(User.username == "${ADMIN_USERNAME}").first():
        password = "${ADMIN_PASSWORD}"
        admin_user = User(
            username="${ADMIN_USERNAME}",
            email="${ADMIN_EMAIL}",
            password_hash=get_password_hash(password),
            is_admin=True,
            auth_provider="local"
        )
        db.add(admin_user)
        print(f"Admin user created with password: {password}")
    else:
        print("Admin user already exists")
    
    # Commit all changes
    db.commit()
    print("Database seeding completed successfully")
EOF

# Run the seeding script with a temporary container
echo_status "Running database seeding script..."
docker compose run --rm -v $(pwd)/seed_script.py:/app/seed_script.py api python /app/seed_script.py
if [ $? -ne 0 ]; then
    echo_error "Data seeding failed. Check the error message above."
    exit 1
fi

# Clean up the seeding script
rm -f seed_script.py

# Now start the API container
echo_status "Starting the API container..."
docker compose up -d api
echo_status "Waiting for API to be ready..."
sleep 5

# Check if API container is running properly
if ! docker compose ps api | grep -q "Up"; then
    echo_error "API container failed to start. Checking logs..."
    docker compose logs api
    exit 1
fi

echo_status "Database initialization completed successfully!"
echo_status "Your TukkerLa application is now running in Docker."
echo ""
echo "API is available at: http://localhost:8000"
echo "API documentation at: http://localhost:8000/docs"
echo ""
echo "Admin credentials:"
echo "  Username: $ADMIN_USERNAME"
echo "  Password: $ADMIN_PASSWORD"
echo ""
echo_warning "IMPORTANT: Save these credentials and change the password in production!" 