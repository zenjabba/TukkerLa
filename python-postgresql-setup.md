# TuckerLa Freezer Tracker: Python + PostgreSQL Implementation

## Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌────────────────┐
│ Web Frontend │────▶│ Python API  │────▶│ PostgreSQL DB  │
│ (React/Vue)  │◀────│ (FastAPI)   │◀────│                │
└─────────────┘     └─────────────┘     └────────────────┘
       │                                         
       │                                         
┌─────────────┐                                  
│ Mobile App  │                                  
│ (React      │                                  
│  Native)    │                                  
└─────────────┘                                  
```

## 1. Database Setup

### PostgreSQL Installation & Configuration

```bash
# Install PostgreSQL on Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# Install on macOS with Homebrew
brew install postgresql

# Start PostgreSQL service
sudo service postgresql start  # Linux
brew services start postgresql # macOS
```

### Database Schema

```sql
-- Create the database
CREATE DATABASE tuckerla;

-- Connect to the database
\c tuckerla

-- Create users table
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(100) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create categories table
CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

-- Create locations table (freezer locations)
CREATE TABLE locations (
    location_id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

-- Create items table
CREATE TABLE items (
    item_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    barcode VARCHAR(50),
    category_id INTEGER REFERENCES categories(category_id),
    location_id INTEGER REFERENCES locations(location_id),
    quantity INTEGER DEFAULT 1,
    stored_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expiry_date TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    added_by INTEGER REFERENCES users(user_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create images table
CREATE TABLE images (
    image_id SERIAL PRIMARY KEY,
    item_id INTEGER REFERENCES items(item_id) ON DELETE CASCADE,
    image_path TEXT NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create usage_history table
CREATE TABLE usage_history (
    usage_id SERIAL PRIMARY KEY,
    item_id INTEGER REFERENCES items(item_id) ON DELETE SET NULL,
    quantity INTEGER NOT NULL,
    used_by INTEGER REFERENCES users(user_id),
    usage_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- Create barcode_products table for storing known products
CREATE TABLE barcode_products (
    barcode_id SERIAL PRIMARY KEY,
    barcode VARCHAR(50) UNIQUE NOT NULL,
    product_name VARCHAR(100) NOT NULL,
    default_category_id INTEGER REFERENCES categories(category_id),
    default_expiry_days INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_items_barcode ON items(barcode);
CREATE INDEX idx_items_category ON items(category_id);
CREATE INDEX idx_items_expiry ON items(expiry_date);
CREATE INDEX idx_barcode_products_barcode ON barcode_products(barcode);
```

### Initial Data

```sql
-- Insert common categories
INSERT INTO categories (name) VALUES 
('Meat'), ('Vegetables'), ('Fruits'), ('Ready Meals'), ('Leftovers'), 
('Seafood'), ('Bread'), ('Dessert'), ('Other');

-- Insert common freezer locations
INSERT INTO locations (name) VALUES 
('Top Drawer'), ('Middle Drawer'), ('Bottom Drawer'), ('Door Shelf'), ('Main Compartment');

-- Create admin user (change password in production)
INSERT INTO users (username, email, password_hash, is_admin) 
VALUES ('admin', 'admin@example.com', 'change_this_to_hashed_password', TRUE);
```

## 2. Backend API with FastAPI

### Project Setup

```bash
# Create virtual environment
mkdir tuckerla
cd tuckerla
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-multipart python-jose[cryptography] passlib[bcrypt] python-dotenv pillow opencv-python-headless pyzbar
```

### Project Structure

```
tuckerla/
├── venv/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── users.py
│   │   ├── items.py
│   │   └── ...
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── users.py
│   │   ├── items.py
│   │   └── ...
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── users.py
│   │   ├── items.py
│   │   ├── images.py
│   │   ├── barcodes.py
│   │   └── ...
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── barcode.py
│   │   ├── image.py
│   │   └── ...
│   └── utils/
│       ├── __init__.py
│       ├── security.py
│       └── ...
├── static/
│   └── images/
├── .env
└── requirements.txt
```

### Configuration (.env file)

```
# Database
DATABASE_URL=postgresql://postgres:password@localhost/tuckerla

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Image Storage
UPLOAD_DIRECTORY=static/images

# Optional: External Barcode API
BARCODE_API_KEY=your-api-key
BARCODE_API_URL=https://api.example.com/lookup
```

### FastAPI Setup (main.py)

```python
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.routers import users, items, images, barcodes
from app.database import engine
import app.models.base as models

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="TuckerLa Freezer Tracker")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend URLs in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directory for images
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(users.router)
app.include_router(items.router)
app.include_router(images.router)
app.include_router(barcodes.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to TuckerLa Freezer Tracker API"}
```

### Database Connection (database.py)

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## 3. Key API Endpoints Implementation

### Items Router

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.schemas import items as schemas
from app.models import items as models
from app.services import auth

router = APIRouter(prefix="/items", tags=["items"])

@router.post("/", response_model=schemas.Item)
def create_item(
    item: schemas.ItemCreate,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    # Convert item schema to model
    db_item = models.Item(
        name=item.name,
        barcode=item.barcode,
        category_id=item.category_id,
        location_id=item.location_id,
        quantity=item.quantity,
        stored_date=item.stored_date or datetime.now(),
        expiry_date=item.expiry_date,
        notes=item.notes,
        added_by=current_user.user_id
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.get("/", response_model=List[schemas.Item])
def get_items(
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None,
    location_id: Optional[int] = None,
    expiring_soon: bool = False,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    query = db.query(models.Item)
    
    # Apply filters
    if category_id:
        query = query.filter(models.Item.category_id == category_id)
    if location_id:
        query = query.filter(models.Item.location_id == location_id)
    if expiring_soon:
        soon = datetime.now() + timedelta(days=7)
        query = query.filter(models.Item.expiry_date <= soon)
    if search:
        query = query.filter(models.Item.name.ilike(f"%{search}%"))
    
    return query.offset(skip).limit(limit).all()

# Add endpoints for get_item, update_item, delete_item, etc.
```

### Barcode Router

```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import cv2
import numpy as np
from pyzbar.pyzbar import decode
import requests
from typing import Optional

from app.database import get_db
from app.schemas import barcodes as schemas
from app.models import barcode_products as models
from app.services import auth
from app.config import settings

router = APIRouter(prefix="/barcodes", tags=["barcodes"])

@router.post("/scan", response_model=schemas.BarcodeResult)
async def scan_barcode(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    # Read and decode the uploaded image
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    
    decoded_objects = decode(img)
    if not decoded_objects:
        raise HTTPException(status_code=400, detail="No barcode found in image")
    
    # Get the first barcode found
    barcode = decoded_objects[0].data.decode("utf-8")
    barcode_type = decoded_objects[0].type
    
    # Check if barcode exists in our database
    db_product = db.query(models.BarcodeProduct).filter(
        models.BarcodeProduct.barcode == barcode
    ).first()
    
    if db_product:
        return {
            "barcode": barcode,
            "barcode_type": barcode_type,
            "product_name": db_product.product_name,
            "default_category_id": db_product.default_category_id,
            "default_expiry_days": db_product.default_expiry_days,
            "source": "database"
        }
    
    # If not in database, try to fetch from external API
    product_info = await lookup_barcode_external(barcode)
    if product_info:
        # Save to database for future
        new_product = models.BarcodeProduct(
            barcode=barcode,
            product_name=product_info["product_name"],
            default_category_id=product_info.get("default_category_id"),
            default_expiry_days=product_info.get("default_expiry_days", 90)  # Default 90 days
        )
        db.add(new_product)
        db.commit()
        
        return {
            "barcode": barcode,
            "barcode_type": barcode_type,
            "product_name": product_info["product_name"],
            "default_category_id": product_info.get("default_category_id"),
            "default_expiry_days": product_info.get("default_expiry_days"),
            "source": "external"
        }
    
    # If not found anywhere
    return {
        "barcode": barcode,
        "barcode_type": barcode_type,
        "product_name": None,
        "source": "unknown"
    }

async def lookup_barcode_external(barcode: str) -> Optional[dict]:
    """Look up barcode in external API if configured"""
    if not settings.BARCODE_API_URL or not settings.BARCODE_API_KEY:
        return None
        
    try:
        response = requests.get(
            f"{settings.BARCODE_API_URL}/{barcode}",
            headers={"Authorization": f"Bearer {settings.BARCODE_API_KEY}"}
        )
        if response.status_code == 200:
            data = response.json()
            return {
                "product_name": data.get("name"),
                "default_expiry_days": data.get("shelf_life_days"),
                # Map external category to our category_id if possible
            }
    except Exception as e:
        print(f"Error looking up barcode: {e}")
    
    return None
```

### Images Router

```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import os
import uuid
from typing import List

from app.database import get_db
from app.schemas import images as schemas
from app.models import images as models
from app.services import auth
from app.config import settings

router = APIRouter(prefix="/images", tags=["images"])

@router.post("/{item_id}", response_model=schemas.Image)
async def upload_image(
    item_id: int,
    file: UploadFile = File(...),
    is_primary: bool = False,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    # Ensure item exists
    from app.models.items import Item
    item = db.query(Item).filter(Item.item_id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{file_extension}"
    
    # Create upload directory if it doesn't exist
    os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)
    
    # Save file
    file_path = os.path.join(settings.UPLOAD_DIRECTORY, filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # Create relative path for storage in DB
    relative_path = os.path.join("images", filename)
    
    # If setting as primary, clear other primary flags
    if is_primary:
        db.query(models.Image).filter(
            models.Image.item_id == item_id,
            models.Image.is_primary == True
        ).update({"is_primary": False})
    
    # Save image record to database
    db_image = models.Image(
        item_id=item_id,
        image_path=relative_path,
        is_primary=is_primary
    )
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    
    return db_image

@router.get("/{item_id}", response_model=List[schemas.Image])
def get_item_images(
    item_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user)
):
    return db.query(models.Image).filter(models.Image.item_id == item_id).all()
```

## 4. Frontend Options

### React Web App

For the web version, React with TypeScript provides a good foundation:

```bash
# Create React app
npx create-react-app tuckerla-web --template typescript
cd tuckerla-web

# Install dependencies
npm install axios react-router-dom @mui/material @emotion/react @emotion/styled react-webcam react-barcode-reader date-fns
```

### React Native Mobile App

For the mobile app with camera support:

```bash
# Create React Native app
npx react-native init TuckerLaMobile --template react-native-template-typescript
cd TuckerLaMobile

# Install dependencies
npm install @react-navigation/native @react-navigation/stack axios react-native-camera react-native-vision-camera react-native-permissions react-native-fs moment
```

## 5. Implementing Camera and Barcode Scanning

### Web Implementation (React)

```tsx
// src/components/BarcodeScanner.tsx
import React, { useRef, useState } from 'react';
import Webcam from 'react-webcam';
import axios from 'axios';

interface BarcodeScannerProps {
  onBarcodeDetected: (barcodeData: any) => void;
}

const BarcodeScanner: React.FC<BarcodeScannerProps> = ({ onBarcodeDetected }) => {
  const webcamRef = useRef<Webcam>(null);
  const [isCapturing, setIsCapturing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const captureImage = async () => {
    setIsCapturing(true);
    setError(null);
    
    if (webcamRef.current) {
      const imageSrc = webcamRef.current.getScreenshot();
      if (!imageSrc) {
        setError('Failed to capture image');
        setIsCapturing(false);
        return;
      }
      
      // Convert base64 to blob
      const byteString = atob(imageSrc.split(',')[1]);
      const mimeString = imageSrc.split(',')[0].split(':')[1].split(';')[0];
      const ab = new ArrayBuffer(byteString.length);
      const ia = new Uint8Array(ab);
      
      for (let i = 0; i < byteString.length; i++) {
        ia[i] = byteString.charCodeAt(i);
      }
      
      const blob = new Blob([ab], { type: mimeString });
      const file = new File([blob], 'barcode.jpg', { type: mimeString });
      
      // Upload to server for processing
      const formData = new FormData();
      formData.append('file', file);
      
      try {
        const response = await axios.post('/api/barcodes/scan', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        
        onBarcodeDetected(response.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to process barcode');
      } finally {
        setIsCapturing(false);
      }
    }
  };

  return (
    <div className="barcode-scanner">
      <Webcam
        audio={false}
        ref={webcamRef}
        screenshotFormat="image/jpeg"
        width="100%"
        videoConstraints={{
          facingMode: 'environment',
        }}
      />
      
      <button 
        onClick={captureImage} 
        disabled={isCapturing}
      >
        {isCapturing ? 'Processing...' : 'Scan Barcode'}
      </button>
      
      {error && <div className="error-message">{error}</div>}
    </div>
  );
};

export default BarcodeScanner;
```

### Mobile Implementation (React Native)

```tsx
// src/components/MobileScanner.tsx
import React, { useState, useRef } from 'react';
import { StyleSheet, View, TouchableOpacity, Text, Alert } from 'react-native';
import { Camera, useCameraDevices } from 'react-native-vision-camera';
import { useScanBarcodes, BarcodeFormat } from 'vision-camera-code-scanner';
import axios from 'axios';
import RNFS from 'react-native-fs';

interface MobileScannerProps {
  onBarcodeDetected: (barcodeData: any) => void;
  onImageCaptured: (imageUri: string) => void;
}

const MobileScanner: React.FC<MobileScannerProps> = ({ 
  onBarcodeDetected, 
  onImageCaptured 
}) => {
  const [hasPermission, setHasPermission] = useState(false);
  const [scanning, setScanning] = useState(true);
  const camera = useRef<Camera>(null);
  const devices = useCameraDevices();
  const device = devices.back;
  
  const [frameProcessor, barcodes] = useScanBarcodes([
    BarcodeFormat.EAN_13,
    BarcodeFormat.EAN_8,
    BarcodeFormat.UPC_A,
    BarcodeFormat.UPC_E,
    BarcodeFormat.QR_CODE,
  ]);

  React.useEffect(() => {
    (async () => {
      const cameraPermission = await Camera.requestCameraPermission();
      setHasPermission(cameraPermission === 'authorized');
    })();
  }, []);

  React.useEffect(() => {
    if (barcodes.length > 0 && scanning) {
      setScanning(false);
      onBarcodeDetected({
        barcode: barcodes[0].displayValue,
        barcode_type: barcodes[0].format,
      });
    }
  }, [barcodes]);

  const takePicture = async () => {
    if (camera.current) {
      try {
        const photo = await camera.current.takePhoto({
          flash: 'auto',
        });
        
        onImageCaptured(`file://${photo.path}`);
        
        // Optional: Upload to server
        await uploadImage(photo.path);
      } catch (e) {
        Alert.alert('Error', 'Failed to take picture');
      }
    }
  };

  const uploadImage = async (imagePath: string) => {
    try {
      const formData = new FormData();
      formData.append('file', {
        name: 'image.jpg',
        type: 'image/jpeg',
        uri: `file://${imagePath}`,
      } as any);
      
      await axios.post('https://your-api-url/api/images/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
    } catch (error) {
      console.error('Upload failed', error);
    }
  };

  if (!hasPermission) {
    return <Text>No access to camera</Text>;
  }

  if (!device) {
    return <Text>Loading...</Text>;
  }

  return (
    <View style={styles.container}>
      <Camera
        ref={camera}
        style={styles.camera}
        device={device}
        isActive={true}
        frameProcessor={frameProcessor}
        frameProcessorFps={5}
      />
      
      <View style={styles.buttonContainer}>
        <TouchableOpacity 
          style={styles.captureButton}
          onPress={takePicture}
        >
          <Text style={styles.buttonText}>Capture</Text>
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={styles.scanButton}
          onPress={() => setScanning(true)}
        >
          <Text style={styles.buttonText}>
            {scanning ? 'Scanning...' : 'Scan Barcode'}
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  camera: {
    flex: 1,
  },
  buttonContainer: {
    position: 'absolute',
    bottom: 20,
    flexDirection: 'row',
    justifyContent: 'space-around',
    width: '100%',
  },
  captureButton: {
    backgroundColor: 'white',
    padding: 15,
    borderRadius: 50,
    width: 100,
    alignItems: 'center',
  },
  scanButton: {
    backgroundColor: '#4CAF50',
    padding: 15,
    borderRadius: 50,
    width: 150,
    alignItems: 'center',
  },
  buttonText: {
    color: 'black',
    fontWeight: 'bold',
  },
});

export default MobileScanner;
```

## 6. Deployment

### Backend Deployment (Python FastAPI)

#### Option 1: Docker

```dockerfile
FROM python:3.9

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Option 2: VPS/Cloud Hosting

Deploy to a Virtual Private Server:

```bash
# Install dependencies
sudo apt update
sudo apt install python3-pip python3-venv nginx postgresql

# Set up PostgreSQL
sudo -u postgres createuser tuckerla_user
sudo -u postgres createdb tuckerla
sudo -u postgres psql -c "ALTER USER tuckerla_user WITH ENCRYPTED PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE tuckerla TO tuckerla_user;"

# Clone and set up application
git clone https://your-repo/tuckerla.git
cd tuckerla
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set up environment variables
nano .env  # Add your environment variables

# Set up systemd service
sudo nano /etc/systemd/system/tuckerla.service
# [Unit]
# Description=TuckerLa API
# After=network.target
# 
# [Service]
# User=www-data
# Group=www-data
# WorkingDirectory=/path/to/tuckerla
# Environment="PATH=/path/to/tuckerla/venv/bin"
# EnvironmentFile=/path/to/tuckerla/.env
# ExecStart=/path/to/tuckerla/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
# 
# [Install]
# WantedBy=multi-user.target

# Start and enable service
sudo systemctl start tuckerla
sudo systemctl enable tuckerla

# Configure Nginx as reverse proxy
sudo nano /etc/nginx/sites-available/tuckerla
# server {
#     listen 80;
#     server_name your-domain.com;
#     
#     location / {
#         proxy_pass http://localhost:8000;
#         proxy_set_header Host $host;
#         proxy_set_header X-Real-IP $remote_addr;
#     }
#     
#     location /static {
#         alias /path/to/tuckerla/static;
#     }
# }

sudo ln -s /etc/nginx/sites-available/tuckerla /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

## 7. Additional Considerations

### Backup Strategy

1. Set up automated PostgreSQL backups:

```bash
# Create backup script
sudo nano /usr/local/bin/backup_tuckerla.sh
# #!/bin/bash
# TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
# BACKUP_DIR="/var/backups/tuckerla"
# mkdir -p $BACKUP_DIR
# 
# # Database backup
# pg_dump tuckerla | gzip > $BACKUP_DIR/tuckerla_db_$TIMESTAMP.sql.gz
# 
# # Image files backup
# tar -czf $BACKUP_DIR/tuckerla_images_$TIMESTAMP.tar.gz /path/to/tuckerla/static/images
# 
# # Cleanup old backups (keep the last 7 days)
# find $BACKUP_DIR -name "tuckerla_db_*.sql.gz" -mtime +7 -delete
# find $BACKUP_DIR -name "tuckerla_images_*.tar.gz" -mtime +7 -delete

# Make executable
sudo chmod +x /usr/local/bin/backup_tuckerla.sh

# Set up cron job
sudo crontab -e
# Add: 0 3 * * * /usr/local/bin/backup_tuckerla.sh
```

### Security Considerations

1. Use HTTPS with proper SSL/TLS certificates
2. Implement rate limiting on API endpoints
3. Set up proper user authentication and authorization
4. Use secure password hashing with bcrypt
5. Apply input validation and sanitization
6. Configure proper PostgreSQL roles and permissions
7. Keep all dependencies updated

### Performance Optimization

1. Add database indexes for commonly queried fields
2. Implement caching for frequently accessed data
3. Optimize image sizes before storage
4. Use pagination for list endpoints
5. Consider read replicas for PostgreSQL for heavy load
6. Set up proper monitoring and logging

## 8. Next Steps and Future Enhancements

1. Implement a notification system for expiring items
2. Add data visualization and reporting
3. Create a recommendation system based on usage patterns
4. Add meal planning functionality
5. Implement shopping list generation based on low inventory
6. Integrate with smart home systems or voice assistants
7. Add sharing capabilities for family/household members
8. Implement batch operations for adding multiple items 