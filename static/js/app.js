// Global state
const state = {
  items: []
};

// DOM Elements
document.addEventListener('DOMContentLoaded', () => {
  // Initialize the app
  initApp();
  
  // Add event listeners
  document.getElementById('addItemBtn').addEventListener('click', showAddItemModal);
  document.getElementById('addItemForm').addEventListener('submit', handleAddItem);
  document.getElementById('importItemsBtn')?.addEventListener('click', showImportModal);
  document.getElementById('importForm')?.addEventListener('submit', handleImportItems);
  document.getElementById('removeItemBtn')?.addEventListener('click', showRemoveItemModal);
  document.getElementById('removeItemForm')?.addEventListener('submit', handleRemoveItem);
  document.getElementById('updateItemBtn')?.addEventListener('click', showUpdateItemModal);
  document.getElementById('updateItemForm')?.addEventListener('submit', handleUpdateItem);
  document.getElementById('inventoryImportBtn')?.addEventListener('click', showInventoryImportModal);
  document.getElementById('inventoryImportForm')?.addEventListener('submit', handleInventoryImportSubmit);
  document.getElementById('confirmYesBtn')?.addEventListener('click', confirmInventoryUpdate);
  document.getElementById('confirmNoBtn')?.addEventListener('click', cancelInventoryUpdate);
  
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
  const itemsContainer = document.getElementById('itemsContainer');
  
  // Check if the container exists
  if (!itemsContainer) {
    console.error('Error: itemsContainer element not found');
    return;
  }
  
  itemsContainer.innerHTML = '';
  
  if (state.items.length === 0) {
    itemsContainer.innerHTML = '<div class="card"><p>No items found. Add some items to your freezer!</p></div>';
    return;
  }
  
  const itemsGrid = document.createElement('div');
  itemsGrid.className = 'item-grid';
  
  state.items.forEach(item => {
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
  
  card.innerHTML = `
    <div class="item-content">
      <div class="item-header">
        <span class="item-title">${item.name}</span>
        <span class="item-category">${item.quantity}</span>
      </div>
      <div class="item-details">
        <div class="item-detail">
          <span class="detail-label">Pack Type:</span>
          <span>${item.packType}</span>
        </div>
        <div class="item-detail">
          <span class="detail-label">Added:</span>
          <span>${formatDate(item.added_date)}</span>
        </div>
        <div class="item-detail">
          <span class="detail-label">Expires:</span>
          <span>${formatDate(item.expiry_date)} ${getExpiryText(daysUntilExpiry)}</span>
        </div>
      </div>
      <div class="item-actions">
        <button class="btn btn-danger" onclick="deleteItem(${item.id})">Delete</button>
        <button class="btn" onclick="editItem(${item.id})">Edit</button>
      </div>
    </div>
  `;
  
  return card;
}

// Format a date string
function formatDate(dateString) {
  if (!dateString) return 'N/A';
  
  try {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
  } catch (error) {
    console.error('Error formatting date:', error);
    return dateString;
  }
}

// Get expiry text based on days until expiry
function getExpiryText(days) {
  if (days < 0) {
    return `<span style="color: var(--danger-color);">(Expired ${Math.abs(days)} days ago)</span>`;
  } else if (days === 0) {
    return `<span style="color: var(--warning-color);">(Expires today)</span>`;
  } else if (days <= 7) {
    return `<span style="color: var(--warning-color);">(Expires in ${days} days)</span>`;
  }
  return '';
}

// Show the add item modal
function showAddItemModal() {
  const modal = document.getElementById('addItemModal');
  if (!modal) {
    console.error('Error: addItemModal element not found');
    return;
  }
  
  modal.style.display = 'block';
  
  const form = document.getElementById('addItemForm');
  if (form) {
    form.reset();
  }
  
  // Set default expiry date to 3 months from now
  const expiryDateInput = document.getElementById('itemExpiryDate');
  if (expiryDateInput) {
    const defaultExpiry = new Date();
    defaultExpiry.setMonth(defaultExpiry.getMonth() + 3);
    expiryDateInput.valueAsDate = defaultExpiry;
  }
}

// Show the import modal
function showImportModal() {
  const modal = document.getElementById('importModal');
  if (!modal) {
    console.error('Error: importModal element not found');
    return;
  }
  
  modal.style.display = 'block';
  
  const form = document.getElementById('importForm');
  if (form) {
    form.reset();
  }
}

// Show the inventory import modal
function showInventoryImportModal() {
  const modal = document.getElementById('inventoryImportModal');
  if (!modal) {
    console.error('Error: inventoryImportModal element not found');
    return;
  }
  
  modal.style.display = 'block';
  
  const form = document.getElementById('inventoryImportForm');
  if (form) {
    form.reset();
  }
  
  // Set up the sublocation dropdown based on the selected location
  const locationSelect = document.getElementById('inventoryLocation');
  const sublocationSelect = document.getElementById('inventorySublocation');
  
  if (locationSelect && sublocationSelect) {
    // Initial population of sublocations
    updateInventorySublocations();
    
    // Add event listener to update sublocations when location changes
    locationSelect.addEventListener('change', updateInventorySublocations);
  }
}

// Update sublocations in the inventory import modal based on selected location
function updateInventorySublocations() {
  const locationSelect = document.getElementById('inventoryLocation');
  const sublocationSelect = document.getElementById('inventorySublocation');
  
  if (!locationSelect || !sublocationSelect) return;
  
  const selectedLocation = locationSelect.value;
  
  // Clear current options except the first one
  sublocationSelect.innerHTML = '<option value="all">All Locations</option>';
  
  // Add sublocations based on the selected location
  if (selectedLocation === 'freezer') {
    sublocationSelect.innerHTML += `
      <option value="kitchen">Kitchen Freezer</option>
      <option value="garage">Garage Freezer</option>
      <option value="basement">Basement Freezer</option>
    `;
  } else if (selectedLocation === 'fridge') {
    sublocationSelect.innerHTML += `
      <option value="kitchen">Kitchen Fridge</option>
      <option value="garage">Garage Fridge</option>
      <option value="basement">Basement Fridge</option>
    `;
  } else if (selectedLocation === 'pantry') {
    sublocationSelect.innerHTML += `
      <option value="kitchen">Kitchen Pantry</option>
      <option value="garage">Garage Pantry</option>
      <option value="basement">Basement Pantry</option>
    `;
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
  
  // Get the location select element
  const locationSelect = document.getElementById('removeItemLocation');
  const subcategorySelect = document.getElementById('removeItemSubcategory');
  const itemSelect = document.getElementById('removeItemSelect');
  
  // Reset selects
  subcategorySelect.innerHTML = '<option value="">-- Select a subcategory --</option>';
  itemSelect.innerHTML = '<option value="">-- Select an item --</option>';
  
  // Add event listener to location select
  locationSelect.addEventListener('change', updateSubcategories);
  
  // Add event listener to subcategory select
  subcategorySelect.addEventListener('change', updateItems);
  
  // Add event listener to item select
  itemSelect.addEventListener('change', updateItemDetails);
  
  // Initial population of subcategories based on selected location
  updateSubcategories();
}

// Update subcategories based on selected location
function updateSubcategories() {
  const locationSelect = document.getElementById('removeItemLocation');
  const subcategorySelect = document.getElementById('removeItemSubcategory');
  const selectedLocation = locationSelect.value;
  
  // Clear current options
  subcategorySelect.innerHTML = '<option value="">-- Select a subcategory --</option>';
  
  // Get unique subcategories for the selected location
  const subcategories = new Set();
  state.items.forEach(item => {
    if (item.location === selectedLocation && item.subcategory) {
      subcategories.add(item.subcategory);
    }
  });
  
  // Sort subcategories alphabetically
  const sortedSubcategories = Array.from(subcategories).sort();
  
  // Add "All" option
  const allOption = document.createElement('option');
  allOption.value = "all";
  allOption.textContent = "All Categories";
  subcategorySelect.appendChild(allOption);
  
  // Add subcategories to select
  sortedSubcategories.forEach(subcategory => {
    const option = document.createElement('option');
    option.value = subcategory;
    option.textContent = subcategory;
    subcategorySelect.appendChild(option);
  });
  
  // Update items based on selected location
  updateItems();
}

// Update items based on selected location and subcategory
function updateItems() {
  const locationSelect = document.getElementById('removeItemLocation');
  const subcategorySelect = document.getElementById('removeItemSubcategory');
  const itemSelect = document.getElementById('removeItemSelect');
  
  const selectedLocation = locationSelect.value;
  const selectedSubcategory = subcategorySelect.value;
  
  // Clear current options
  itemSelect.innerHTML = '<option value="">-- Select an item --</option>';
  
  // Filter items by location and subcategory
  let filteredItems = state.items.filter(item => item.location === selectedLocation);
  
  // Filter by subcategory if one is selected (and not "all")
  if (selectedSubcategory && selectedSubcategory !== 'all') {
    filteredItems = filteredItems.filter(item => 
      item.subcategory && item.subcategory.toLowerCase() === selectedSubcategory.toLowerCase()
    );
  }
  
  // Sort items alphabetically by name
  filteredItems.sort((a, b) => a.name.localeCompare(b.name));
  
  // Add items to select
  filteredItems.forEach(item => {
    const option = document.createElement('option');
    option.value = item.id;
    option.textContent = item.name;
    option.dataset.quantity = item.quantity;
    option.dataset.packType = item.packType;
    itemSelect.appendChild(option);
  });
}

// Update item details when an item is selected
function updateItemDetails() {
  const itemSelect = document.getElementById('removeItemSelect');
  const packTypeInput = document.getElementById('packType');
  const quantityToRemoveInput = document.getElementById('quantityToRemove');
  
  if (itemSelect.value) {
    // Get the selected option
    const selectedOption = itemSelect.options[itemSelect.selectedIndex];
    
    // Update pack type input field
    if (packTypeInput) {
      packTypeInput.value = selectedOption.dataset.packType;
    }
    
    // Extract numeric part of quantity for validation
    const quantityMatch = selectedOption.dataset.quantity.match(/^[\d.]+/);
    if (quantityMatch) {
      const maxQuantity = parseFloat(quantityMatch[0]);
      quantityToRemoveInput.max = maxQuantity;
      quantityToRemoveInput.value = "1";
    }
  } else {
    // Clear the pack type input field
    if (packTypeInput) {
      packTypeInput.value = '';
    }
  }
}

// Handle remove item form submission
async function handleRemoveItem(e) {
  e.preventDefault();
  
  const itemSelect = document.getElementById('removeItemSelect');
  const quantityToRemoveInput = document.getElementById('quantityToRemove');
  
  if (!itemSelect || !quantityToRemoveInput) {
    showNotification('Error: Form fields not found', 'error');
    return;
  }
  
  const itemId = parseInt(itemSelect.value);
  const quantityToRemove = parseFloat(quantityToRemoveInput.value);
  
  if (!itemId) {
    showNotification('Please select an item to remove', 'error');
    return;
  }
  
  if (isNaN(quantityToRemove) || quantityToRemove <= 0) {
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
    
    // Update state based on the response
    if (result.message === "Item fully consumed and removed") {
      // Remove the item from the state
      state.items = state.items.filter(item => item.id !== itemId);
    } else if (result.item) {
      // Update the item in the state
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

// Show the update item modal
function showUpdateItemModal() {
  // Implementation would go here
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
  
  const nameInput = document.getElementById('itemName');
  const packTypeInput = document.getElementById('itemPackType');
  const quantityInput = document.getElementById('itemQuantity');
  const expiryDateInput = document.getElementById('itemExpiryDate');
  
  if (!nameInput || !packTypeInput || !quantityInput || !expiryDateInput) {
    showNotification('Error: Form fields not found', 'error');
    return;
  }
  
  const newItem = {
    name: nameInput.value,
    packType: packTypeInput.value,
    quantity: quantityInput.value,
    expiry_date: expiryDateInput.value
  };
  
  try {
    const response = await fetch('/api/items', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newItem)
    });
    
    if (!response.ok) throw new Error('Failed to add item');
    
    const addedItem = await response.json();
    state.items.push(addedItem);
    renderItems();
    closeModals();
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
  if (!fileInput) {
    showNotification('Error: File input not found', 'error');
    return;
  }
  
  const file = fileInput.files[0];
  
  if (!file) {
    showNotification('Please select a file to import', 'error');
    return;
  }
  
  try {
    console.log('Starting file import process...');
    console.log('File details:', file.name, file.type, file.size);
    
    // Check file type
    const fileType = file.name.split('.').pop().toLowerCase();
    if (!['csv', 'xlsx', 'xls'].includes(fileType)) {
      showNotification('Please upload a CSV or Excel file', 'error');
      return;
    }
    
    // Create form data and send to server
    const formData = new FormData();
    formData.append('file', file);
    
    console.log('Sending request to server...');
    
    const response = await fetch('/api/import', {
      method: 'POST',
      body: formData
    }).catch(error => {
      console.error('Network error during fetch:', error);
      throw new Error('Network error: ' + (error.message || 'Failed to connect to server'));
    });
    
    console.log('Server response received, status:', response.status);
    
    if (!response.ok) {
      console.error('Server returned error status:', response.status);
      try {
        const errorData = await response.json();
        console.error('Error details:', errorData);
        throw new Error(errorData.detail || `Server error: ${response.status}`);
      } catch (jsonError) {
        console.error('Failed to parse error response:', jsonError);
        throw new Error(`Server error: ${response.status}`);
      }
    }
    
    try {
      const result = await response.json();
      console.log('Response parsed successfully:', result);
      state.items = result.items;
      
      renderItems();
      closeModals();
      showNotification(result.message || 'Items imported successfully!', 'success');
    } catch (jsonError) {
      console.error('Failed to parse success response:', jsonError);
      throw new Error('Failed to parse server response');
    }
  } catch (error) {
    console.error('Error importing items:', error);
    showNotification('Error importing items: ' + error.message, 'error');
  }
}

// Handle inventory import form submission
async function handleInventoryImportSubmit(e) {
  e.preventDefault();
  
  const fileInput = document.getElementById('inventoryFileInput');
  const locationSelect = document.getElementById('inventoryLocation');
  const sublocationSelect = document.getElementById('inventorySublocation');
  
  if (!fileInput || !locationSelect || !sublocationSelect) {
    showNotification('Error: Form fields not found', 'error');
    return;
  }
  
  const file = fileInput.files[0];
  const location = locationSelect.value;
  const sublocation = sublocationSelect.value;
  
  if (!file) {
    showNotification('Please select a file to import', 'error');
    return;
  }
  
  // Store the form data in session storage for later use
  const fileData = {
    name: file.name,
    type: file.type,
    size: file.size,
    lastModified: file.lastModified
  };
  
  sessionStorage.setItem('inventoryFileData', JSON.stringify(fileData));
  sessionStorage.setItem('inventoryLocation', location);
  sessionStorage.setItem('inventorySublocation', sublocation);
  
  // Show confirmation modal
  closeModals();
  const confirmModal = document.getElementById('confirmationModal');
  if (confirmModal) {
    confirmModal.style.display = 'block';
  }
}

// Handle inventory update confirmation
async function confirmInventoryUpdate() {
  const fileInput = document.getElementById('inventoryFileInput');
  const locationSelect = document.getElementById('inventoryLocation');
  const sublocationSelect = document.getElementById('inventorySublocation');
  
  if (!fileInput || !locationSelect || !sublocationSelect) {
    showNotification('Error: Form fields not found', 'error');
    closeModals();
    return;
  }
  
  const file = fileInput.files[0];
  const location = locationSelect.value;
  const sublocation = sublocationSelect.value;
  
  try {
    console.log('Starting inventory update process...');
    console.log('File details:', file.name, file.type, file.size);
    console.log('Location:', location, 'Sublocation:', sublocation);
    
    // Check file type
    const fileType = file.name.split('.').pop().toLowerCase();
    if (!['csv', 'xlsx', 'xls'].includes(fileType)) {
      showNotification('Please upload a CSV or Excel file', 'error');
      closeModals();
      return;
    }
    
    // Create form data and send to server
    const formData = new FormData();
    formData.append('file', file);
    formData.append('location', location);
    formData.append('sublocation', sublocation);
    formData.append('update_all', 'true'); // Flag to indicate full inventory update
    
    console.log('Sending inventory update request to server...');
    
    const response = await fetch('/api/inventory_update', {
      method: 'POST',
      body: formData
    }).catch(error => {
      console.error('Network error during fetch:', error);
      throw new Error('Network error: ' + (error.message || 'Failed to connect to server'));
    });
    
    console.log('Server response received, status:', response.status);
    
    if (!response.ok) {
      console.error('Server returned error status:', response.status);
      try {
        const errorData = await response.json();
        console.error('Error details:', errorData);
        throw new Error(errorData.detail || `Server error: ${response.status}`);
      } catch (jsonError) {
        console.error('Failed to parse error response:', jsonError);
        throw new Error(`Server error: ${response.status}`);
      }
    }
    
    try {
      const result = await response.json();
      console.log('Response parsed successfully:', result);
      state.items = result.items;
      
      renderItems();
      closeModals();
      showNotification(result.message || 'Inventory updated successfully!', 'success');
    } catch (jsonError) {
      console.error('Failed to parse success response:', jsonError);
      throw new Error('Failed to parse server response');
    }
  } catch (error) {
    console.error('Error updating inventory:', error);
    showNotification('Error updating inventory: ' + error.message, 'error');
    closeModals();
  }
}

// Cancel inventory update (add new items without overwriting)
async function cancelInventoryUpdate() {
  const fileInput = document.getElementById('inventoryFileInput');
  const locationSelect = document.getElementById('inventoryLocation');
  const sublocationSelect = document.getElementById('inventorySublocation');
  
  if (!fileInput || !locationSelect || !sublocationSelect) {
    showNotification('Error: Form fields not found', 'error');
    closeModals();
    return;
  }
  
  const file = fileInput.files[0];
  const location = locationSelect.value;
  const sublocation = sublocationSelect.value;
  
  try {
    console.log('Starting inventory add process...');
    console.log('File details:', file.name, file.type, file.size);
    console.log('Location:', location, 'Sublocation:', sublocation);
    
    // Check file type
    const fileType = file.name.split('.').pop().toLowerCase();
    if (!['csv', 'xlsx', 'xls'].includes(fileType)) {
      showNotification('Please upload a CSV or Excel file', 'error');
      closeModals();
      return;
    }
    
    // Create form data and send to server
    const formData = new FormData();
    formData.append('file', file);
    formData.append('location', location);
    formData.append('sublocation', sublocation);
    formData.append('update_all', 'false'); // Flag to indicate adding items without full update
    
    console.log('Sending inventory add request to server...');
    
    const response = await fetch('/api/inventory_update', {
      method: 'POST',
      body: formData
    }).catch(error => {
      console.error('Network error during fetch:', error);
      throw new Error('Network error: ' + (error.message || 'Failed to connect to server'));
    });
    
    console.log('Server response received, status:', response.status);
    
    if (!response.ok) {
      console.error('Server returned error status:', response.status);
      try {
        const errorData = await response.json();
        console.error('Error details:', errorData);
        throw new Error(errorData.detail || `Server error: ${response.status}`);
      } catch (jsonError) {
        console.error('Failed to parse error response:', jsonError);
        throw new Error(`Server error: ${response.status}`);
      }
    }
    
    try {
      const result = await response.json();
      console.log('Response parsed successfully:', result);
      state.items = result.items;
      
      renderItems();
      closeModals();
      showNotification(result.message || 'Items added to inventory successfully!', 'success');
    } catch (jsonError) {
      console.error('Failed to parse success response:', jsonError);
      throw new Error('Failed to parse server response');
    }
  } catch (error) {
    console.error('Error adding items to inventory:', error);
    showNotification('Error adding items: ' + error.message, 'error');
    closeModals();
  }
}

// Handle update item form submission
async function handleUpdateItem(e) {
  // Implementation would go here
}

// Delete an item
async function deleteItem(id) {
  if (!confirm('Are you sure you want to delete this item?')) return;
  
  try {
    const response = await fetch(`/api/items/${id}`, {
      method: 'DELETE'
    });
    
    if (!response.ok) throw new Error('Failed to delete item');
    
    state.items = state.items.filter(item => item.id !== id);
    renderItems();
    showNotification('Item deleted successfully!', 'success');
  } catch (error) {
    console.error('Error deleting item:', error);
    showNotification('Error deleting item: ' + error.message, 'error');
  }
}

// Edit an item
function editItem(id) {
  // This would be implemented in a real app
  alert('Edit functionality would be implemented here');
}

// Show a notification
function showNotification(message, type) {
  try {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Make the notification visible
    setTimeout(() => {
      notification.classList.add('show');
    }, 10);
    
    // Remove the notification after 3 seconds
    setTimeout(() => {
      notification.classList.remove('show');
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 300);
    }, 3000);
  } catch (error) {
    console.error('Error showing notification:', error);
  }
} 