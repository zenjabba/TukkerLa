from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
import os
import json
from typing import List, Optional
import csv
from io import StringIO, BytesIO
import datetime
import pandas as pd
import re

# Initialize FastAPI app
app = FastAPI(
    title="TukkerLa Freezer Tracker",
    description="Simple test application",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create static directory if it doesn't exist
os.makedirs("static", exist_ok=True)

# Sample data
items = [
    {
        "id": 1,
        "name": "Chicken Breast",
        "subcategory": "Poultry",
        "packType": "Vacuum Sealed",
        "quantity": "500g",
        "location": "freezer",
        "freezerLocation": "kitchen",
        "expiry_date": "2023-12-31",
        "added_date": "2023-06-15"
    },
    {
        "id": 2,
        "name": "Mixed Vegetables",
        "subcategory": "Vegetables",
        "packType": "Bag",
        "quantity": "750g",
        "location": "freezer",
        "freezerLocation": "garage",
        "expiry_date": "2023-10-15",
        "added_date": "2023-05-20"
    },
    {
        "id": 3,
        "name": "Ice Cream",
        "subcategory": "Desserts",
        "packType": "Tub",
        "quantity": "1L",
        "location": "freezer",
        "freezerLocation": "kitchen",
        "expiry_date": "2023-09-30",
        "added_date": "2023-06-01"
    }
]

# Mount static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=RedirectResponse)
def read_root():
    """Redirect to the static HTML page."""
    return "/static/index.html"

@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

@app.get("/api/items")
def get_items():
    """Return all freezer items."""
    return items

@app.post("/api/items")
async def add_item(item: dict):
    """Add a new freezer item."""
    # Generate a new ID
    new_id = max([i["id"] for i in items], default=0) + 1
    
    # Create the new item with the generated ID
    new_item = {
        "id": new_id,
        "name": item["name"],
        "subcategory": item.get("subcategory", ""),
        "packType": item["packType"],
        "quantity": item["quantity"],
        "location": item.get("location", "freezer"),
        "freezerLocation": item.get("freezerLocation", "kitchen"),
        "expiry_date": item["expiry_date"],
        "added_date": datetime.date.today().isoformat()  # Use current date as added date
    }
    
    # Add to the items list
    items.append(new_item)
    
    return new_item

@app.delete("/api/items/{item_id}")
async def delete_item(item_id: int):
    """Delete a freezer item by ID."""
    global items
    original_length = len(items)
    items = [item for item in items if item["id"] != item_id]
    
    if len(items) == original_length:
        raise HTTPException(status_code=404, detail=f"Item with ID {item_id} not found")
    
    return {"message": "Item deleted successfully"}

@app.post("/api/import")
async def import_items(
    file: UploadFile = File(...),
    location: Optional[str] = Form(None),
    freezerLocation: Optional[str] = Form(None)
):
    """Import items from a CSV or Excel file."""
    global items
    
    # Debug information
    print(f"Import request received - File: {file.filename}, Location: {location}, Freezer Location: {freezerLocation}")
    
    # Check file extension
    file_ext = os.path.splitext(file.filename.lower())[1]
    print(f"File extension: {file_ext}")
    
    try:
        # Read the file content
        content = await file.read()
        print(f"File content read, size: {len(content)} bytes")
        
        imported_items = []
        
        # Process based on file type
        if file_ext in ['.csv']:
            # Process CSV file
            text = content.decode('utf-8')
            print(f"CSV content sample: {text[:100]}...")
            df = pd.read_csv(StringIO(text))
            print(f"CSV parsed successfully, rows: {len(df)}, columns: {list(df.columns)}")
        elif file_ext in ['.xls', '.xlsx']:
            # Process Excel file
            df = pd.read_excel(BytesIO(content))
            print(f"Excel parsed successfully, rows: {len(df)}, columns: {list(df.columns)}")
        else:
            error_msg = f"Unsupported file type: {file_ext}"
            print(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Standardize column names
        df.columns = [col.strip() for col in df.columns]
        print(f"Standardized columns: {list(df.columns)}")
        
        # Map common column names
        column_mapping = {
            'name': ['Name', 'Item Name', 'Item', 'Product', 'Product Name'],
            'subcategory': ['Subcategory', 'Sub Category', 'Sub-category', 'Category', 'Type', 'Item Type'],
            'location': ['Location', 'Storage Location', 'Storage'],
            'packType': ['Pack Type', 'Package Type', 'Packaging', 'Pack'],
            'quantity': ['Quantity', 'Qty', 'Amount', 'Weight'],
            'expiry_date': ['Expiry Date', 'Expiry', 'Exp Date', 'Expiration Date', 'Expiration'],
            'freezerLocation': ['Freezer Location', 'Freezer', 'Freezer Name', 'Kitchen', 'Garage', 'Basement']
        }
        
        # Find the actual column names in the file
        actual_columns = {}
        for key, possible_names in column_mapping.items():
            for name in possible_names:
                if name in df.columns:
                    actual_columns[key] = name
                    break
            if key not in actual_columns:
                # Use the first possible name if not found
                actual_columns[key] = possible_names[0]
        
        print(f"Column mapping: {actual_columns}")
        
        # Process each row
        for _, row in df.iterrows():
            # Create a new item
            try:
                # Get values using the actual column names if they exist
                name = str(row.get(actual_columns['name'], '')).strip()
                subcategory = str(row.get(actual_columns.get('subcategory', ''), '')).strip()
                pack_type = str(row.get(actual_columns['packType'], '')).strip()
                quantity = str(row.get(actual_columns['quantity'], '')).strip()
                expiry_date = row.get(actual_columns['expiry_date'], '')
                
                # Get freezer location from the CSV if available
                csv_freezer_location = None
                if 'location' in actual_columns and actual_columns['location'] in row:
                    csv_freezer_location = str(row.get(actual_columns['location'], '')).strip().lower()
                
                print(f"Processing row: name={name}, subcategory={subcategory}, pack_type={pack_type}, quantity={quantity}, expiry_date={expiry_date}, csv_location={csv_freezer_location}")
                
                # Skip empty rows or rows with 'nan' values
                if not name or name.lower() == 'nan':
                    print(f"Skipping row with empty name: {name}")
                    continue
                
                # Skip if subcategory is 'nan'
                if subcategory.lower() == 'nan':
                    subcategory = ''
                
                # Skip if pack_type is 'nan'
                if pack_type.lower() == 'nan':
                    pack_type = ''
                
                # Skip if quantity is 'nan'
                if quantity.lower() == 'nan':
                    quantity = '1'
                
                # Check if this item already exists in imported_items
                found_match = False
                for existing_item in imported_items:
                    if (existing_item["name"].lower() == name.lower() and 
                        existing_item["subcategory"].lower() == subcategory.lower() and
                        existing_item["packType"].lower() == pack_type.lower() and
                        existing_item["freezerLocation"] == (csv_freezer_location or freezerLocation or "kitchen")):
                        
                        # Extract numeric part and unit from existing quantity
                        existing_quantity_match = re.match(r'([\d.]+)\s*([a-zA-Z]*)', existing_item["quantity"])
                        if existing_quantity_match:
                            existing_quantity = float(existing_quantity_match.group(1))
                            existing_unit = existing_quantity_match.group(2)
                        else:
                            existing_quantity = float(existing_item["quantity"]) if existing_item["quantity"].replace('.', '', 1).isdigit() else 1
                            existing_unit = ""
                        
                        # Extract numeric part and unit from new quantity
                        new_quantity_match = re.match(r'([\d.]+)\s*([a-zA-Z]*)', quantity)
                        if new_quantity_match:
                            new_quantity = float(new_quantity_match.group(1))
                            new_unit = new_quantity_match.group(2)
                        else:
                            new_quantity = float(quantity) if quantity.replace('.', '', 1).isdigit() else 1
                            new_unit = ""
                        
                        # Use the existing unit if new one is empty
                        unit_to_use = new_unit if new_unit else existing_unit
                        
                        # Combine quantities
                        total_quantity = existing_quantity + new_quantity
                        existing_item["quantity"] = f"{total_quantity}{unit_to_use}"
                        
                        # Use the later expiry date
                        try:
                            existing_date = datetime.date.fromisoformat(existing_item["expiry_date"])
                            new_date = datetime.date.fromisoformat(validate_date(expiry_date))
                            if new_date > existing_date:
                                existing_item["expiry_date"] = new_date.isoformat()
                        except:
                            pass
                        
                        found_match = True
                        print(f"Found matching item, updated quantity to: {existing_item['quantity']}")
                        break
                
                if found_match:
                    continue
                
                # Generate a new ID for each item, taking into account both existing items and newly imported items
                new_id = max([i["id"] for i in items] + [i.get("id", 0) for i in imported_items], default=0) + 1
                
                new_item = {
                    "id": new_id,
                    "name": name,
                    "subcategory": subcategory,
                    "packType": pack_type,
                    "quantity": quantity,
                    "location": location or "freezer",
                    "freezerLocation": csv_freezer_location or freezerLocation or "kitchen",
                    "expiry_date": validate_date(expiry_date),
                    "added_date": datetime.date.today().isoformat()  # Use current date as added date
                }
                
                # Add to the list
                imported_items.append(new_item)
                print(f"Added new item: {new_item}")
                
            except Exception as e:
                # Skip invalid rows
                print(f"Error processing row: {str(e)}")
                continue
        
        # Add all valid items to the main list
        items.extend(imported_items)
        
        print(f"Import complete: {len(imported_items)} items imported")
        
        return {
            "message": f"Successfully imported {len(imported_items)} items",
            "items": items
        }
        
    except Exception as e:
        print(f"Import failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

@app.post("/api/inventory_update")
async def inventory_update(
    file: UploadFile = File(...),
    location: str = Form(...),
    sublocation: str = Form(...),
    update_all: str = Form(...)
):
    """Update inventory based on a CSV or Excel file. 
    If update_all is 'true', it will update existing items in the specified sublocation.
    If update_all is 'false', it will add to the existing inventory without removing items."""
    global items
    
    # Check file extension
    file_ext = os.path.splitext(file.filename.lower())[1]
    
    # Read the file content
    content = await file.read()
    
    try:
        # Process based on file type
        if file_ext in ['.csv']:
            # Process CSV file
            text = content.decode('utf-8')
            df = pd.read_csv(StringIO(text))
            print(f"CSV file loaded with {len(df)} rows")
            print(f"CSV columns: {list(df.columns)}")
            if len(df) > 0:
                print(f"First row sample: {df.iloc[0].to_dict()}")
        elif file_ext in ['.xls', '.xlsx']:
            # Process Excel file
            df = pd.read_excel(BytesIO(content))
            print(f"Excel file loaded with {len(df)} rows")
            print(f"Excel columns: {list(df.columns)}")
            if len(df) > 0:
                print(f"First row sample: {df.iloc[0].to_dict()}")
        else:
            raise HTTPException(status_code=400, detail="Only CSV or Excel files are supported")
        
        # Standardize column names - convert to lowercase for case-insensitive matching
        df.columns = [col.strip().lower() for col in df.columns]
        print(f"Standardized columns: {list(df.columns)}")
        
        # Map common column names (all lowercase for case-insensitive matching)
        column_mapping = {
            'name': ['name', 'item name', 'item', 'product', 'product name'],
            'subcategory': ['subcategory', 'sub category', 'sub-category', 'category', 'type', 'item type'],
            'location': ['location', 'storage location', 'storage', 'freezer location', 'fridge location', 'pantry location'],
            'packType': ['pack type', 'package type', 'packaging', 'pack'],
            'quantity': ['quantity', 'qty', 'amount', 'weight'],
            'expiry_date': ['expiry date', 'expiry', 'exp date', 'expiration date', 'expiration'],
        }
        
        # Find the actual column names in the file
        actual_columns = {}
        for key, possible_names in column_mapping.items():
            found = False
            for name in possible_names:
                if name in df.columns:
                    actual_columns[key] = name
                    found = True
                    break
            if not found:
                # Try partial matching if exact match not found
                for col in df.columns:
                    for name in possible_names:
                        if name in col:
                            actual_columns[key] = col
                            found = True
                            break
                    if found:
                        break
        
        print(f"Mapped columns: {actual_columns}")
        
        # Check if required columns are present
        missing_columns = []
        required_columns = ['name', 'packType', 'quantity']
        for col in required_columns:
            if col not in actual_columns:
                missing_columns.append(col)
        
        if missing_columns:
            error_msg = f"Required columns missing: {', '.join(missing_columns)}. Please check your CSV format."
            print(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Process the inventory update
        if update_all.lower() == 'true':
            # If updating all items in a specific sublocation, first remove existing items from that sublocation
            if sublocation != 'all':
                # Keep items that are not in the specified location/sublocation
                original_count = len(items)
                items = [item for item in items if not (
                    item["location"] == location and 
                    (location == 'freezer' and item.get("freezerLocation") == sublocation or
                     location == 'fridge' and item.get("fridgeLocation") == sublocation or
                     location == 'pantry' and item.get("pantryLocation") == sublocation)
                )]
                print(f"Removed {original_count - len(items)} items from {location}/{sublocation}")
            else:
                # Keep items that are not in the specified main location
                original_count = len(items)
                items = [item for item in items if item["location"] != location]
                print(f"Removed {original_count - len(items)} items from {location}")
                
        # Process each row in the uploaded file
        imported_items = []
        skipped_rows = 0
        error_rows = 0
        
        for index, row in df.iterrows():
            # Create a new item
            try:
                # Get values using the actual column names if they exist
                name = str(row.get(actual_columns.get('name', ''), '')).strip()
                subcategory = str(row.get(actual_columns.get('subcategory', ''), '')).strip()
                pack_type = str(row.get(actual_columns.get('packType', ''), '')).strip()
                quantity = str(row.get(actual_columns.get('quantity', ''), '')).strip()
                expiry_date = row.get(actual_columns.get('expiry_date', ''), '')
                
                # Get location from the CSV if available
                csv_location = None
                if 'location' in actual_columns:
                    csv_location = str(row.get(actual_columns['location'], '')).strip().lower()
                
                # Debug info
                print(f"Processing row {index}: name='{name}', subcategory='{subcategory}', pack_type='{pack_type}', quantity='{quantity}', location='{csv_location}'")
                
                # Skip empty rows or rows with 'nan' values
                if not name or name.lower() == 'nan':
                    print(f"Skipping row {index}: Empty name or 'nan'")
                    skipped_rows += 1
                    continue
                
                # Skip if subcategory is 'nan'
                if subcategory.lower() == 'nan':
                    subcategory = ''
                
                # Skip if pack_type is 'nan'
                if pack_type.lower() == 'nan' or not pack_type:
                    pack_type = 'Unknown'
                    print(f"Row {index}: Using default pack type 'Unknown'")
                
                # Skip if quantity is 'nan'
                if quantity.lower() == 'nan' or not quantity:
                    quantity = '1'
                    print(f"Row {index}: Using default quantity '1'")
                
                # Determine the correct location field based on the storage location
                location_field = ""
                if location == 'freezer':
                    location_field = "freezerLocation"
                elif location == 'fridge':
                    location_field = "fridgeLocation"
                elif location == 'pantry':
                    location_field = "pantryLocation"
                
                # Map CSV location to sublocation if available
                if csv_location:
                    # Convert common location names to our standard format
                    if csv_location in ['kitchen', 'kitchen freezer', 'kitchen fridge', 'kitchen pantry']:
                        csv_location = 'kitchen'
                    elif csv_location in ['garage', 'garage freezer', 'garage fridge', 'garage pantry']:
                        csv_location = 'garage'
                    elif csv_location in ['basement', 'basement freezer', 'basement fridge', 'basement pantry']:
                        csv_location = 'basement'
                
                # Use the specified sublocation if no location in the CSV
                final_sublocation = csv_location or sublocation
                
                # Check if this item already exists in the main items list or imported_items
                found_match = False
                
                # First check in imported_items
                for existing_item in imported_items:
                    if (existing_item["name"].lower() == name.lower() and 
                        existing_item["subcategory"].lower() == subcategory.lower() and
                        existing_item["packType"].lower() == pack_type.lower() and
                        existing_item["location"] == location and
                        existing_item.get(location_field) == final_sublocation):
                        
                        # Update quantities and expiry date
                        existing_quantity_match = re.match(r'([\d.]+)\s*([a-zA-Z]*)', existing_item["quantity"])
                        if existing_quantity_match:
                            existing_quantity = float(existing_quantity_match.group(1))
                            existing_unit = existing_quantity_match.group(2)
                        else:
                            existing_quantity = float(existing_item["quantity"]) if existing_item["quantity"].replace('.', '', 1).isdigit() else 1
                            existing_unit = ""
                        
                        new_quantity_match = re.match(r'([\d.]+)\s*([a-zA-Z]*)', quantity)
                        if new_quantity_match:
                            new_quantity = float(new_quantity_match.group(1))
                            new_unit = new_quantity_match.group(2)
                        else:
                            new_quantity = float(quantity) if quantity.replace('.', '', 1).isdigit() else 1
                            new_unit = ""
                        
                        unit_to_use = new_unit if new_unit else existing_unit
                        
                        total_quantity = existing_quantity + new_quantity
                        existing_item["quantity"] = f"{total_quantity}{unit_to_use}"
                        
                        try:
                            existing_date = datetime.date.fromisoformat(existing_item["expiry_date"])
                            new_date = datetime.date.fromisoformat(validate_date(expiry_date))
                            if new_date > existing_date:
                                existing_item["expiry_date"] = new_date.isoformat()
                        except:
                            pass
                        
                        found_match = True
                        print(f"Updated existing item in imported_items: {existing_item['name']}")
                        break
                
                # If not found in imported_items and not updating all, check in the main items list
                if not found_match and update_all.lower() != 'true':
                    for existing_item in items:
                        if (existing_item["name"].lower() == name.lower() and 
                            existing_item["subcategory"].lower() == subcategory.lower() and
                            existing_item["packType"].lower() == pack_type.lower() and
                            existing_item["location"] == location and
                            existing_item.get(location_field) == final_sublocation):
                            
                            # Update quantities and expiry date
                            existing_quantity_match = re.match(r'([\d.]+)\s*([a-zA-Z]*)', existing_item["quantity"])
                            if existing_quantity_match:
                                existing_quantity = float(existing_quantity_match.group(1))
                                existing_unit = existing_quantity_match.group(2)
                            else:
                                existing_quantity = float(existing_item["quantity"]) if existing_item["quantity"].replace('.', '', 1).isdigit() else 1
                                existing_unit = ""
                            
                            new_quantity_match = re.match(r'([\d.]+)\s*([a-zA-Z]*)', quantity)
                            if new_quantity_match:
                                new_quantity = float(new_quantity_match.group(1))
                                new_unit = new_quantity_match.group(2)
                            else:
                                new_quantity = float(quantity) if quantity.replace('.', '', 1).isdigit() else 1
                                new_unit = ""
                            
                            unit_to_use = new_unit if new_unit else existing_unit
                            
                            total_quantity = existing_quantity + new_quantity
                            existing_item["quantity"] = f"{total_quantity}{unit_to_use}"
                            
                            try:
                                existing_date = datetime.date.fromisoformat(existing_item["expiry_date"])
                                new_date = datetime.date.fromisoformat(validate_date(expiry_date))
                                if new_date > existing_date:
                                    existing_item["expiry_date"] = new_date.isoformat()
                            except:
                                pass
                            
                            found_match = True
                            print(f"Updated existing item in items list: {existing_item['name']}")
                            break
                
                if found_match:
                    continue
                
                # If no match found, create a new item
                new_id = max([i["id"] for i in items] + [i.get("id", 0) for i in imported_items], default=0) + 1
                
                # Create the new item with the appropriate location field
                new_item = {
                    "id": new_id,
                    "name": name,
                    "subcategory": subcategory,
                    "packType": pack_type,
                    "quantity": quantity,
                    "location": location,
                    "expiry_date": validate_date(expiry_date),
                    "added_date": datetime.date.today().isoformat()  # Use current date as added date
                }
                
                # Add the specific location field based on the storage type
                if location == 'freezer':
                    new_item["freezerLocation"] = final_sublocation
                elif location == 'fridge':
                    new_item["fridgeLocation"] = final_sublocation
                elif location == 'pantry':
                    new_item["pantryLocation"] = final_sublocation
                
                # Add to the list
                imported_items.append(new_item)
                print(f"Created new item: {new_item['name']}")
                
            except Exception as e:
                print(f"Error processing row {index}: {str(e)}")
                error_rows += 1
                continue
        
        # Add all valid new items to the main list
        items.extend(imported_items)
        
        print(f"Summary: {len(imported_items)} items imported, {skipped_rows} rows skipped, {error_rows} rows with errors")
        
        if update_all.lower() == 'true':
            message = f"Successfully updated inventory with {len(imported_items)} items"
        else:
            message = f"Successfully added {len(imported_items)} items to inventory"
            
        return {
            "message": message,
            "items": items
        }
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

@app.post("/api/items/{item_id}/update-quantity")
async def update_item_quantity(item_id: int, update_data: dict):
    """Update the quantity of an item by ID."""
    global items
    
    # Find the item
    item_index = None
    for i, item in enumerate(items):
        if item["id"] == item_id:
            item_index = i
            break
    
    if item_index is None:
        raise HTTPException(status_code=404, detail=f"Item with ID {item_id} not found")
    
    # Get the current quantity and the quantity to remove
    current_item = items[item_index]
    current_quantity_str = current_item["quantity"]
    quantity_to_remove = update_data.get("quantity_to_remove", 0)
    
    # Parse the current quantity
    try:
        # Extract numeric part and unit
        quantity_match = re.match(r'([\d.]+)\s*([a-zA-Z]*)', current_quantity_str)
        if quantity_match:
            current_quantity = float(quantity_match.group(1))
            unit = quantity_match.group(2)
        else:
            # If no match, assume it's just a number
            current_quantity = float(current_quantity_str)
            unit = ""
        
        # Calculate the new quantity
        new_quantity = current_quantity - float(quantity_to_remove)
        
        # If the new quantity is zero or negative, delete the item
        if new_quantity <= 0:
            items.pop(item_index)
            return {"message": "Item fully consumed and removed"}
        
        # Update the item quantity
        items[item_index]["quantity"] = f"{new_quantity}{unit}"
        
        return {
            "message": "Quantity updated successfully",
            "item": items[item_index]
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error updating quantity: {str(e)}")

def validate_date(date_str):
    """Validate and format a date string."""
    if not date_str or pd.isna(date_str):
        # Use today's date if not provided
        return datetime.date.today().isoformat()
    
    try:
        # If it's already a date object (from pandas)
        if isinstance(date_str, (datetime.date, datetime.datetime)):
            return date_str.date().isoformat()
        
        # Try to parse the date
        # First try ISO format (YYYY-MM-DD)
        try:
            datetime.date.fromisoformat(str(date_str))
            return str(date_str)
        except ValueError:
            pass
        
        # Try other common formats
        for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%m-%d-%Y", "%d-%m-%Y"):
            try:
                date_obj = datetime.datetime.strptime(str(date_str), fmt).date()
                return date_obj.isoformat()
            except ValueError:
                continue
        
        # If we get here, no format worked
        return datetime.date.today().isoformat()
    except:
        # Default to today if any error occurs
        return datetime.date.today().isoformat()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 