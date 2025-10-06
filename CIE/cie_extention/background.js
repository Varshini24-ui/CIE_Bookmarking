// Background service worker for CIE Agent Universal Extension

console.log('🚀 CIE Agent background service worker started');

// Create context menu on installation
chrome.runtime.onInstalled.addListener(() => {
  console.log('📦 Extension installed/updated');
  
  // Initialize storage
  chrome.storage.local.set({
    savedToday: 0,
    savedTotal: 0,
    lastDate: new Date().toDateString()
  });

  // Remove existing context menu items first
  chrome.contextMenus.removeAll(() => {
    // Create new context menu item
    chrome.contextMenus.create({
      id: 'save-to-cie',
      title: '📘 Save to CIE Agent',
      contexts: ['page', 'selection', 'link', 'image', 'video', 'audio']
    }, () => {
      if (chrome.runtime.lastError) {
        console.error('Context menu error:', chrome.runtime.lastError);
      } else {
        console.log('✅ Context menu created successfully');
      }
    });
  });
});

// Also create on startup
chrome.runtime.onStartup.addListener(() => {
  console.log('🔄 Extension started');
  chrome.contextMenus.removeAll(() => {
    chrome.contextMenus.create({
      id: 'save-to-cie',
      title: '📘 Save to CIE Agent',
      contexts: ['page', 'selection', 'link', 'image', 'video', 'audio']
    });
  });
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
  console.log('Context menu clicked:', info.menuItemId);
  
  if (info.menuItemId === 'save-to-cie') {
    console.log('Saving from context menu for tab:', tab.id);
    
    // Send message to content script to save page
    chrome.tabs.sendMessage(tab.id, { action: 'saveCurrentPage' }, (response) => {
      if (chrome.runtime.lastError) {
        console.error('Error sending message:', chrome.runtime.lastError.message);
        // Try injecting the content script if it's not loaded
        chrome.scripting.executeScript({
          target: { tabId: tab.id },
          files: ['content.js']
        }).then(() => {
          // Try again after injection
          chrome.tabs.sendMessage(tab.id, { action: 'saveCurrentPage' });
        }).catch(err => {
          console.error('Failed to inject script:', err);
        });
      } else {
        console.log('Save initiated:', response);
      }
    });
  }
});

// Track saved posts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'postSaved') {
    const today = new Date().toDateString();
    
    chrome.storage.local.get(['savedToday', 'savedTotal', 'lastDate'], (result) => {
      let savedToday = 0;
      let savedTotal = result.savedTotal || 0;
      
      if (result.lastDate === today) {
        savedToday = (result.savedToday || 0) + 1;
      } else {
        savedToday = 1;
      }
      
      savedTotal += 1;
      
      chrome.storage.local.set({
        savedToday: savedToday,
        savedTotal: savedTotal,
        lastDate: today
      });
      
      console.log(`✅ Stats updated: ${savedToday} today, ${savedTotal} total`);
    });
    
    sendResponse({ success: true });
  }
  return true;
});