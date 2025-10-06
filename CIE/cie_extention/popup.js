const BACKEND_URL = 'http://127.0.0.1:8000';
const APP_URL = 'http://localhost:8501';

// Check backend status
async function checkBackendStatus() {
  const statusElement = document.getElementById('status');
  const statusText = document.getElementById('status-text');
  const backendStatus = document.getElementById('backend-status');
  
  try {
    const response = await fetch(`${BACKEND_URL}/health`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });
    
    if (response.ok) {
      const data = await response.json();
      statusElement.classList.remove('offline');
      statusElement.classList.add('online');
      statusText.textContent = '✅ Backend Online & Ready';
      backendStatus.textContent = '🟢';
      
      // Fetch stats
      fetchStats();
    } else {
      throw new Error('Backend offline');
    }
  } catch (error) {
    statusElement.classList.remove('online');
    statusElement.classList.add('offline');
    statusText.textContent = '❌ Backend Offline - Run: python main.py';
    backendStatus.textContent = '🔴';
  }
}

// Fetch statistics
async function fetchStats() {
  try {
    // Get from local storage
    chrome.storage.local.get(['savedToday', 'savedTotal', 'lastDate'], (result) => {
      const today = new Date().toDateString();
      let savedToday = 0;
      let savedTotal = result.savedTotal || 0;
      
      if (result.lastDate === today) {
        savedToday = result.savedToday || 0;
      }
      
      document.getElementById('saved-today').textContent = savedToday;
      document.getElementById('saved-total').textContent = savedTotal;
    });
  } catch (error) {
    console.error('Failed to fetch stats:', error);
  }
}

// Save current page
document.getElementById('save-current').addEventListener('click', async () => {
  const button = document.getElementById('save-current');
  const originalText = button.innerHTML;
  
  button.innerHTML = '⏳ Saving...';
  button.disabled = true;
  
  try {
    // Get current active tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    // Send message to content script
    chrome.tabs.sendMessage(tab.id, { action: 'saveCurrentPage' }, (response) => {
      if (chrome.runtime.lastError) {
        console.error('Error:', chrome.runtime.lastError);
        button.innerHTML = '❌ Failed';
        setTimeout(() => {
          button.innerHTML = originalText;
          button.disabled = false;
        }, 2000);
      } else {
        button.innerHTML = '✅ Saved!';
        setTimeout(() => {
          button.innerHTML = originalText;
          button.disabled = false;
          fetchStats(); // Refresh stats
        }, 2000);
      }
    });
  } catch (error) {
    console.error('Error:', error);
    button.innerHTML = '❌ Error';
    setTimeout(() => {
      button.innerHTML = originalText;
      button.disabled = false;
    }, 2000);
  }
});

// Open CIE Agent app
document.getElementById('open-app').addEventListener('click', () => {
  chrome.tabs.create({ url: APP_URL });
});

// Initialize
checkBackendStatus();
fetchStats();

// Refresh status every 10 seconds
setInterval(checkBackendStatus, 10000);