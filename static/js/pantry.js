// Global state
const state = {
  items: [],
  activeLocation: 'all',
  activeSubcategory: 'all',
  filteredItems: []
};

// DOM Elements
document.addEventListener('DOMContentLoaded', () => {
  // Initialize the app
  initApp();
  
  // Add event listeners
  document.getElementById('addItemBtn').addEventListener('click', showAddItemModal);
  document.getElementById('addItemForm').addEventListener('submit', handleAddItem);
  document.getElementById('importItemsBtn').addEventListener('click', showImportModal);
  document.getElementById('importForm').addEventListener('submit', handleImportItems);
  document.getElementById('removeItemBtn').addEventListener('click', showRemoveItemModal);
  document.getElementById('removeItemForm').addEventListener('submit', handleRemoveItem);
  
  // Pantry location buttons
  document.querySelectorAll('.pantry-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const target = btn.getAttribute('data-target');
      switchPantryLocation(target);
    });
  });
  
  // Subcategory buttons
  document.querySelectorAll('.subcategory-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const subcategory = btn.getAttribute('data-subcategory');
      switchSubcategory(subcategory);
    });
  });
  
  // Remove item form change event listeners
  document.getElementById('removeLocation').addEventListener('change', updateRemoveItemDropdown);
  document.getElementById('removeSubcategory').addEventListener('change', updateRemoveItemDropdown);
  document.getElementById('removeItem').addEventListener('change', updateCurrentQuantity);
  
  // Close modal when clicking on X or outside the modal
  document.querySelectorAll('.close').forEach(closeBtn => {
    closeBtn.addEventListener('click', closeModals);
  });
  
  window.addEventListener('click', (e) => {
    document.querySelectorAll('.modal').forEach(modal => {
      if (e.target === modal) {
        modal.style.display = 'none';
      }
    });
  });
});

// Initialize the application
async function initApp() {
  try {
    await fetchItems();
    renderItems();
  } catch (error) {
    console.error('Error initializing app:', error);
    showNotification('Error initializing app: ' + error.message, 'error');
  }
}

// Switch between pantry locations
function switchPantryLocation(location) {
  // Update active location
  state.activeLocation = location;
  
  // Update button UI
  document.querySelectorAll('.pantry-btn').forEach(btn => {
    if (btn.getAttribute('data-target') === location) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });
  
  // Re-render items for the selected location
  renderItems();
}

// Switch between subcategories
function switchSubcategory(subcategory) {
  // Update active subcategory
  state.activeSubcategory = subcategory;
  
  // Update button UI
  document.querySelectorAll('.subcategory-btn').forEach(btn => {
    if (btn.getAttribute('data-subcategory') === subcategory) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });
  
  // Re-render items for the selected subcategory
  renderItems();
}

// Fetch items from the API
async function fetchItems() {
  try {
    const response = await fetch('/api/items');
    if (!response.ok) throw new Error('Failed to fetch items');
    state.items = await response.json();
  } catch (error) {
    console.error('Error fetching items:', error);
    showNotification('Error fetching items: ' + error.message, 'error');
    throw error;
  }
}

// Render items to the DOM
function renderItems() {
  // Get the container
  const itemsContainer = document.getElementById('pantry-items-container');
  
  // Check if the container exists
  if (!itemsContainer) {
    console.error('Error: pantry-items-container element not found');
    return;
  }
  
  itemsContainer.innerHTML = '';
  
  // Filter items for the selected pantry location
  let pantryItems = [];
  
  if (state.activeLocation === 'all') {
    // Show all pantry items
    pantryItems = state.items.filter(item => item.location === 'pantry');
  } else {
    // Show items for specific pantry location
    pantryItems = state.items.filter(item => {
      if (item.location !== 'pantry') return false;
      
      // Handle both formats: "kitchen" and "kitchen pantry"
      const pantryLoc = item.pantryLocation ? item.pantryLocation.toLowerCase() : '';
      return pantryLoc === state.activeLocation || 
             pantryLoc === `${state.activeLocation} pantry` ||
             pantryLoc === `${state.activeLocation} storage` ||
             pantryLoc.startsWith(state.activeLocation);
    });
  }
  
  // Filter by subcategory if not "all"
  if (state.activeSubcategory !== 'all') {
    pantryItems = pantryItems.filter(item => {
      if (!item.subcategory) return false;
      
      // Create a mapping of button subcategories to possible database values
      const subcategoryMap = {
        'canned': ['canned', 'can', 'tinned', 'tin', 'preserved'],
        'pasta': ['pasta', 'noodles', 'spaghetti', 'macaroni'],
        'rice': ['rice', 'grain', 'grains'],
        'baking': ['baking', 'flour', 'sugar', 'bake'],
        'snacks': ['snacks', 'snack', 'chips', 'crackers', 'nuts'],
        'breakfast': ['breakfast', 'cereal', 'oats', 'granola'],
        'spices': ['spices', 'spice', 'herb', 'herbs', 'seasoning'],
        'oils': ['oils', 'oil', 'vinegar', 'cooking oil'],
        'sauces': ['sauces', 'sauce', 'condiment', 'condiments'],
        'drinks': ['drinks', 'drink', 'beverage', 'beverages', 'tea', 'coffee']
      };
      
      // Clean and normalize the subcategory from the item
      const itemSubCat = item.subcategory.toLowerCase().trim();
      const activeSubCat = state.activeSubcategory.toLowerCase();
      
      // Check if the item's subcategory is in the mapping for the active subcategory
      if (subcategoryMap[activeSubCat] && subcategoryMap[activeSubCat].includes(itemSubCat)) {
        return true;
      }
      
      // Direct case-insensitive comparison
      if (itemSubCat === activeSubCat) {
        return true;
      }
      
      // Check if the item's subcategory contains the active subcategory
      if (itemSubCat.includes(activeSubCat)) {
        return true;
      }
      
      // Check if the active subcategory contains the item's subcategory
      if (activeSubCat.includes(itemSubCat) && itemSubCat.length > 2) {
        return true;
      }
      
      return false;
    });
  }
  
  if (pantryItems.length === 0) {
    let message = '';
    if (state.activeLocation === 'all' && state.activeSubcategory === 'all') {
      message = 'No items found in any pantry. Add some items!';
    } else if (state.activeLocation === 'all') {
      message = `No ${state.activeSubcategory} items found in any pantry.`;
    } else if (state.activeSubcategory === 'all') {
      const locationName = state.activeLocation === 'kitchen' ? 'the kitchen pantry' : 'basement storage';
      message = `No items found in ${locationName}. Add some items!`;
    } else {
      const locationName = state.activeLocation === 'kitchen' ? 'the kitchen pantry' : 'basement storage';
      message = `No ${state.activeSubcategory} items found in ${locationName}.`;
    }
    itemsContainer.innerHTML = `<p>${message}</p>`;
    return;
  }
  
  const itemsGrid = document.createElement('div');
  itemsGrid.className = 'item-grid';
  
  pantryItems.forEach(item => {
    const itemCard = createItemCard(item);
    itemsGrid.appendChild(itemCard);
  });
  
  itemsContainer.appendChild(itemsGrid);
}

// Create an item card element
function createItemCard(item) {
  const card = document.createElement('div');
  card.className = 'item-card';
  
  // Check if item is expired or expiring soon
  const today = new Date();
  const expiryDate = new Date(item.expiry_date);
  const daysUntilExpiry = Math.ceil((expiryDate - today) / (1000 * 60 * 60 * 24));
  
  if (daysUntilExpiry < 0) {
    card.classList.add('expired');
  } else if (daysUntilExpiry <= 7) {
    card.classList.add('expiring-soon');
  }
  
  // Show subcategory if available
  const subcategoryHtml = item.subcategory ? `
    <div class="item-detail">
      <span class="detail-label">Subcategory:</span>
      <span>${item.subcategory}</span>
    </div>` : '';
  
  card.innerHTML = `
    <div class="item-content">
      <div class="item-header">
        <span class="item-title">${item.name}</span>
        <span class="item-category">${item.quantity}</span>
      </div>
      <div class="item-details">
        <div class="item-detail">
          <span class="detail-label">Location:</span>
          <span>${item.pantryLocation || (item.location === 'pantry' ? 'Pantry' : 'Storage')}</span>
        </div>
        ${subcategoryHtml}
        <div class="item-detail">
          <span class="detail-label">Pack Type:</span>
          <span>${item.packType || item.pack_type || ''}</span>
        </div>
        <div class="item-detail">
          <span class="detail-label">Expiry:</span>
          <span class="${getExpiryClass(daysUntilExpiry)}">${formatDate(item.expiry_date)} ${getExpiryText(daysUntilExpiry)}</span>
        </div>
      </div>
    </div>
    <div class="item-actions">
      <button class="btn btn-small" onclick="editItem(${item.id})">Edit</button>
      <button class="btn btn-small btn-danger" onclick="deleteItem(${item.id})">Delete</button>
    </div>
  `;
  
  return card;
}

// Helper function to capitalize first letter
function capitalizeFirstLetter(string) {
  return string.charAt(0).toUpperCase() + string.slice(1);
}

// Format date for display
function formatDate(dateString) {
  const date = new Date(dateString);
  const day = date.getDate().toString().padStart(2, '0');
  const month = (date.getMonth() + 1).toString().padStart(2, '0');
  const year = date.getFullYear();
  
  return `${day}/${month}/${year}`;
}

// Get expiry class based on days until expiry
function getExpiryClass(days) {
  if (days < 0) return 'expired';
  if (days <= 7) return 'expiring-soon';
  return '';
}

// Get expiry text based on days until expiry
function getExpiryText(days) {
  if (days < 0) return `(Expired ${Math.abs(days)} days ago)`;
  if (days === 0) return '(Expires today)';
  if (days === 1) return '(Expires tomorrow)';
  if (days <= 7) return `(Expires in ${days} days)`;
  return '';
}

// Show add item modal
function showAddItemModal() {
  document.getElementById('addItemModal').style.display = 'block';
  
  // Set default date to today
  const today = new Date();
  const formattedDate = today.toISOString().split('T')[0];
  document.getElementById('itemExpiryDate').value = formattedDate;
}

// Show import modal
function showImportModal() {
  document.getElementById('importModal').style.display = 'block';
}

// Close all modals
function closeModals() {
  document.querySelectorAll('.modal').forEach(modal => {
    modal.style.display = 'none';
  });
}

// Handle add item form submission
async function handleAddItem(e) {
  e.preventDefault();
  
  const name = document.getElementById('itemName').value;
  const subcategory = document.getElementById('itemSubcategory').value;
  const pantryLocation = document.getElementById('pantryLocation').value;
  const packType = document.getElementById('itemPackType').value;
  const quantity = document.getElementById('itemQuantity').value;
  const expiryDate = document.getElementById('itemExpiryDate').value;
  
  // Format the location name based on the selected location
  const formattedLocation = pantryLocation === 'kitchen' ? 
    'Kitchen Pantry' : 'Basement Storage';
  
  const newItem = {
    name,
    subcategory,
    pantryLocation: formattedLocation,
    packType: packType,
    quantity,
    expiry_date: expiryDate,
    location: 'pantry'
  };
  
  try {
    const response = await fetch('/api/items', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(newItem)
    });
    
    if (!response.ok) throw new Error('Failed to add item');
    
    // Reset form and close modal
    document.getElementById('addItemForm').reset();
    closeModals();
    
    // Refresh items
    await fetchItems();
    renderItems();
    
    showNotification('Item added successfully!', 'success');
  } catch (error) {
    console.error('Error adding item:', error);
    showNotification('Error adding item: ' + error.message, 'error');
  }
}

// Handle import items form submission
async function handleImportItems(e) {
  e.preventDefault();
  
  const fileInput = document.getElementById('fileInput');
  const pantryLocation = document.getElementById('importPantryLocation').value;
  
  if (!fileInput.files || fileInput.files.length === 0) {
    showNotification('Please select a file to import', 'error');
    return;
  }
  
  // Format the location name based on the selected location
  const formattedLocation = pantryLocation === 'kitchen' ? 
    'Kitchen Pantry' : 'Basement Storage';
  
  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append('file', file);
  formData.append('location', 'pantry');
  formData.append('specificLocation', formattedLocation);
  
  try {
    const response = await fetch('/api/import', {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to import items');
    }
    
    const result = await response.json();
    
    // Reset form and close modal
    document.getElementById('importForm').reset();
    closeModals();
    
    // Refresh items
    await fetchItems();
    renderItems();
    
    showNotification(result.message || 'Items imported successfully!', 'success');
  } catch (error) {
    console.error('Error importing items:', error);
    showNotification('Error importing items: ' + error.message, 'error');
  }
}

// Show the remove item modal
function showRemoveItemModal() {
  const modal = document.getElementById('removeItemModal');
  if (!modal) {
    console.error('Error: removeItemModal element not found');
    return;
  }
  
  modal.style.display = 'block';
  
  const form = document.getElementById('removeItemForm');
  if (form) {
    form.reset();
  }
  
  // Set default location to current selection (if not "all")
  const removeLocationSelect = document.getElementById('removeLocation');
  if (removeLocationSelect && state.activeLocation !== 'all') {
    removeLocationSelect.value = state.activeLocation;
  }
  
  // Set default subcategory to current selection (if not "all")
  const removeSubcategorySelect = document.getElementById('removeSubcategory');
  if (removeSubcategorySelect && state.activeSubcategory !== 'all') {
    removeSubcategorySelect.value = state.activeSubcategory;
  }
  
  // Update the items dropdown
  updateRemoveItemDropdown();
}

// Update the items dropdown in the remove item modal
function updateRemoveItemDropdown() {
  const locationSelect = document.getElementById('removeLocation');
  const subcategorySelect = document.getElementById('removeSubcategory');
  const itemSelect = document.getElementById('removeItem');
  
  if (!locationSelect || !subcategorySelect || !itemSelect) {
    console.error('Error: Form elements not found');
    return;
  }
  
  const selectedLocation = locationSelect.value;
  const selectedSubcategory = subcategorySelect.value;
  
  // Filter items based on selected location and subcategory
  let filteredItems = state.items.filter(item => item.location === 'pantry');
  
  // Filter by location if not "all"
  if (selectedLocation !== 'all') {
    filteredItems = filteredItems.filter(item => {
      const pantryLoc = item.pantryLocation ? item.pantryLocation.toLowerCase() : '';
      return pantryLoc === selectedLocation || 
             pantryLoc === `${selectedLocation} pantry` ||
             pantryLoc === `${selectedLocation} storage` ||
             pantryLoc.startsWith(selectedLocation);
    });
  }
  
  // Filter by subcategory if not "all"
  if (selectedSubcategory !== 'all') {
    filteredItems = filteredItems.filter(item => {
      if (!item.subcategory) return false;
      
      // Create a mapping of button subcategories to possible database values
      const subcategoryMap = {
        'canned': ['canned', 'can', 'tinned', 'tin', 'preserved'],
        'pasta': ['pasta', 'noodles', 'spaghetti', 'macaroni'],
        'rice': ['rice', 'grain', 'grains'],
        'baking': ['baking', 'flour', 'sugar', 'bake'],
        'snacks': ['snacks', 'snack', 'chips', 'crackers', 'nuts'],
        'breakfast': ['breakfast', 'cereal', 'oats', 'granola'],
        'spices': ['spices', 'spice', 'herb', 'herbs', 'seasoning'],
        'oils': ['oils', 'oil', 'vinegar', 'cooking oil'],
        'sauces': ['sauces', 'sauce', 'condiment', 'condiments'],
        'drinks': ['drinks', 'drink', 'beverage', 'beverages', 'tea', 'coffee']
      };
      
      // Clean and normalize the subcategory from the item
      const itemSubCat = item.subcategory.toLowerCase().trim();
      const activeSubCat = selectedSubcategory.toLowerCase();
      
      // Check if the item's subcategory is in the mapping for the active subcategory
      if (subcategoryMap[activeSubCat] && subcategoryMap[activeSubCat].includes(itemSubCat)) {
        return true;
      }
      
      // Direct case-insensitive comparison
      if (itemSubCat === activeSubCat) {
        return true;
      }
      
      // Check if the item's subcategory contains the active subcategory
      if (itemSubCat.includes(activeSubCat)) {
        return true;
      }
      
      // Check if the active subcategory contains the item's subcategory
      if (activeSubCat.includes(itemSubCat) && itemSubCat.length > 2) {
        return true;
      }
      
      return false;
    });
  }
  
  // Save filtered items to state for later use
  state.filteredItems = filteredItems;
  
  // Clear existing options
  itemSelect.innerHTML = '<option value="">-- Select an item --</option>';
  
  // Add filtered items to the dropdown
  filteredItems.forEach(item => {
    const option = document.createElement('option');
    option.value = item.id;
    option.textContent = `${item.name} (${item.quantity})`;
    itemSelect.appendChild(option);
  });
  
  // Clear current quantity field
  document.getElementById('currentQuantity').value = '';
  document.getElementById('quantityToRemove').value = '';
  document.getElementById('packType').value = '';
}

// Update the current quantity field when an item is selected
function updateCurrentQuantity() {
  const itemSelect = document.getElementById('removeItem');
  const currentQuantityInput = document.getElementById('currentQuantity');
  const removeItemIdInput = document.getElementById('removeItemId');
  const packTypeInput = document.getElementById('packType');
  
  if (!itemSelect || !currentQuantityInput || !removeItemIdInput || !packTypeInput) {
    console.error('Error: Form elements not found');
    return;
  }
  
  const selectedItemId = parseInt(itemSelect.value);
  if (!selectedItemId) {
    currentQuantityInput.value = '';
    removeItemIdInput.value = '';
    packTypeInput.value = '';
    return;
  }
  
  // Find the selected item
  const selectedItem = state.filteredItems.find(item => item.id === selectedItemId);
  if (selectedItem) {
    currentQuantityInput.value = selectedItem.quantity;
    removeItemIdInput.value = selectedItemId;
    
    // Set pack type from the correct property
    packTypeInput.value = selectedItem.packType || selectedItem.pack_type || '';
    
    // Set default quantity to remove as the full amount
    document.getElementById('quantityToRemove').value = extractQuantityNumber(selectedItem.quantity);
  }
}

// Extract the numeric part of a quantity string
function extractQuantityNumber(quantityStr) {
  const match = quantityStr.match(/^([\d.]+)/);
  return match ? match[1] : '';
}

// Handle remove item form submission
async function handleRemoveItem(e) {
  e.preventDefault();
  
  const itemIdInput = document.getElementById('removeItemId');
  const quantityToRemoveInput = document.getElementById('quantityToRemove');
  
  if (!itemIdInput || !quantityToRemoveInput) {
    showNotification('Error: Form fields not found', 'error');
    return;
  }
  
  const itemId = parseInt(itemIdInput.value);
  const quantityToRemove = quantityToRemoveInput.value;
  
  if (!itemId) {
    showNotification('Please select an item', 'error');
    return;
  }
  
  if (!quantityToRemove || isNaN(parseFloat(quantityToRemove))) {
    showNotification('Please enter a valid quantity to remove', 'error');
    return;
  }
  
  try {
    const response = await fetch(`/api/items/${itemId}/update-quantity`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ quantity_to_remove: quantityToRemove })
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to update item quantity');
    }
    
    const result = await response.json();
    
    // If the item was completely removed, filter it out
    if (result.message === "Item fully consumed and removed") {
      state.items = state.items.filter(item => item.id !== itemId);
    } else {
      // Otherwise update the item in the state
      const itemIndex = state.items.findIndex(item => item.id === itemId);
      if (itemIndex !== -1) {
        state.items[itemIndex] = result.item;
      }
    }
    
    renderItems();
    closeModals();
    showNotification(result.message, 'success');
  } catch (error) {
    console.error('Error updating item quantity:', error);
    showNotification('Error updating item quantity: ' + error.message, 'error');
  }
}

// Delete an item
async function deleteItem(id) {
  // Show the remove item modal instead of directly deleting
  showRemoveItemModal();
  
  // Pre-select the item in the dropdown
  const itemSelect = document.getElementById('removeItem');
  if (itemSelect) {
    // Update the dropdown first
    updateRemoveItemDropdown();
    
    // Set timeout to allow the dropdown to populate
    setTimeout(() => {
      itemSelect.value = id;
      updateCurrentQuantity();
    }, 100);
  }
}

// Edit an item
function editItem(id) {
  // Redirect to edit page or show edit modal
  window.location.href = `/edit-item.html?id=${id}`;
}

// Show notification
function showNotification(message, type) {
  // Create notification element
  const notification = document.createElement('div');
  notification.className = `notification ${type}`;
  notification.textContent = message;
  
  // Add to document
  document.body.appendChild(notification);
  
  // Remove after delay
  setTimeout(() => {
    notification.classList.add('hide');
    setTimeout(() => {
      document.body.removeChild(notification);
    }, 500);
  }, 3000);
} 