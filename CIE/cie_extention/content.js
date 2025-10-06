// CIE Agent - Universal Content Script (Works on ALL websites)
const BACKEND_URL = 'http://127.0.0.1:8000';

console.log('🚀 CIE Agent Universal Extension Loading...');

// Detect website type and extract content accordingly
class ContentExtractor {
  constructor() {
    this.url = window.location.href;
    this.hostname = window.location.hostname;
  }

  // Detect website type
  detectSource() {
    const hostname = this.hostname.toLowerCase();
    
    if (hostname.includes('linkedin.com')) return 'LinkedIn';
    if (hostname.includes('medium.com')) return 'Medium';
    if (hostname.includes('twitter.com') || hostname.includes('x.com')) return 'Twitter';
    if (hostname.includes('arxiv.org')) return 'ArXiv';
    if (hostname.includes('scholar.google')) return 'Google Scholar';
    if (hostname.includes('researchgate.net')) return 'ResearchGate';
    if (hostname.includes('github.com')) return 'GitHub';
    if (hostname.includes('stackoverflow.com')) return 'Stack Overflow';
    if (hostname.includes('dev.to')) return 'Dev.to';
    if (hostname.includes('hackernoon.com')) return 'HackerNoon';
    if (hostname.includes('towardsdatascience.com')) return 'Towards Data Science';
    if (hostname.includes('youtube.com')) return 'YouTube';
    if (hostname.includes('reddit.com')) return 'Reddit';
    
    return 'Web Article';
  }

  // Extract content from LinkedIn
  extractLinkedIn() {
    const selectors = [
      '.feed-shared-update-v2__description',
      '.feed-shared-text',
      '[class*="update-components-text"]'
    ];
    
    for (const selector of selectors) {
      const element = document.querySelector(selector);
      if (element && element.innerText.trim()) {
        return element.innerText.trim();
      }
    }
    return null;
  }

  // Extract content from Medium
  extractMedium() {
    const article = document.querySelector('article');
    if (article) {
      const paragraphs = article.querySelectorAll('p');
      return Array.from(paragraphs).map(p => p.innerText).join('\n\n').substring(0, 3000);
    }
    return null;
  }

  // Extract content from Twitter
  extractTwitter() {
    const tweet = document.querySelector('[data-testid="tweetText"]');
    if (tweet) return tweet.innerText.trim();
    return null;
  }

  // Extract content from ArXiv (Research Papers)
  extractArXiv() {
    const abstract = document.querySelector('.abstract');
    if (abstract) {
      return `Title: ${document.querySelector('.title')?.innerText || ''}\n\nAbstract: ${abstract.innerText.trim()}`;
    }
    return null;
  }

  // Extract content from GitHub
  extractGitHub() {
    const readme = document.querySelector('.markdown-body');
    if (readme) {
      return readme.innerText.substring(0, 3000);
    }
    return null;
  }

  // Extract content from Stack Overflow
  extractStackOverflow() {
    const question = document.querySelector('.js-post-body');
    if (question) {
      return question.innerText.substring(0, 2000);
    }
    return null;
  }

  // Extract content from YouTube
  extractYouTube() {
    const title = document.querySelector('h1.ytd-watch-metadata');
    const description = document.querySelector('#description-inline-expander');
    
    if (title && description) {
      return `Video: ${title.innerText}\n\nDescription: ${description.innerText.substring(0, 2000)}`;
    }
    return null;
  }

  // Extract content from Reddit
  extractReddit() {
    const post = document.querySelector('[data-test-id="post-content"]');
    if (post) {
      return post.innerText.substring(0, 2000);
    }
    return null;
  }

  // Generic extraction for blogs and articles
  extractGeneric() {
    // Try article tag first
    let article = document.querySelector('article');
    if (article) {
      const paragraphs = article.querySelectorAll('p');
      if (paragraphs.length > 0) {
        return Array.from(paragraphs)
          .map(p => p.innerText)
          .filter(text => text.length > 50)
          .join('\n\n')
          .substring(0, 3000);
      }
    }

    // Try main content area
    const mainSelectors = [
      'main',
      '[role="main"]',
      '.post-content',
      '.article-content',
      '.entry-content',
      '.content',
      '.post-body',
      '.article-body'
    ];

    for (const selector of mainSelectors) {
      const element = document.querySelector(selector);
      if (element) {
        const paragraphs = element.querySelectorAll('p');
        if (paragraphs.length > 0) {
          return Array.from(paragraphs)
            .map(p => p.innerText)
            .filter(text => text.length > 50)
            .join('\n\n')
            .substring(0, 3000);
        }
      }
    }

    // Fallback: get all paragraphs
    const allParagraphs = document.querySelectorAll('p');
    if (allParagraphs.length > 0) {
      return Array.from(allParagraphs)
        .map(p => p.innerText)
        .filter(text => text.length > 50)
        .slice(0, 10)
        .join('\n\n')
        .substring(0, 3000);
    }

    return null;
  }

  // Main extraction method
  extract() {
    const source = this.detectSource();
    let content = null;

    // Try specific extractors first
    switch (source) {
      case 'LinkedIn':
        content = this.extractLinkedIn();
        break;
      case 'Medium':
        content = this.extractMedium();
        break;
      case 'Twitter':
        content = this.extractTwitter();
        break;
      case 'ArXiv':
        content = this.extractArXiv();
        break;
      case 'GitHub':
        content = this.extractGitHub();
        break;
      case 'Stack Overflow':
        content = this.extractStackOverflow();
        break;
      case 'YouTube':
        content = this.extractYouTube();
        break;
      case 'Reddit':
        content = this.extractReddit();
        break;
      default:
        content = this.extractGeneric();
    }

    // Fallback to page title + meta description
    if (!content || content.length < 100) {
      const title = document.querySelector('h1')?.innerText || document.title;
      const metaDesc = document.querySelector('meta[name="description"]')?.content || '';
      content = `${title}\n\n${metaDesc}\n\n${this.extractGeneric() || 'Content could not be extracted'}`;
    }

    return {
      text: content.trim(),
      url: this.url,
      source: source,
      title: document.title
    };
  }
}

// Create floating save button
function createFloatingButton() {
  // Check if button already exists
  if (document.getElementById('cie-floating-btn')) {
    console.log('Button already exists');
    return;
  }

  console.log('Creating floating button...');

  const button = document.createElement('div');
  button.id = 'cie-floating-btn';
  button.innerHTML = '📘';
  button.title = 'Save to CIE Agent (Click Me!)';
  button.style.cssText = `
    position: fixed !important;
    bottom: 30px !important;
    right: 30px !important;
    width: 65px !important;
    height: 65px !important;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    border-radius: 50% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 32px !important;
    cursor: pointer !important;
    box-shadow: 0 4px 20px rgba(102, 126, 234, 0.6) !important;
    z-index: 2147483647 !important;
    transition: all 0.3s ease !important;
    user-select: none !important;
    border: 3px solid white !important;
  `;

  // Hover effects
  button.addEventListener('mouseenter', () => {
    button.style.transform = 'scale(1.15)';
    button.style.boxShadow = '0 6px 30px rgba(102, 126, 234, 0.8)';
  });

  button.addEventListener('mouseleave', () => {
    button.style.transform = 'scale(1)';
    button.style.boxShadow = '0 4px 20px rgba(102, 126, 234, 0.6)';
  });

  // Click handler
  button.addEventListener('click', async (e) => {
    e.preventDefault();
    e.stopPropagation();
    await saveCurrentPage(button);
  });

  // Make sure it's added to body
  if (document.body) {
    document.body.appendChild(button);
    console.log('✅ Floating button added successfully!');
  } else {
    // Wait for body to be available
    setTimeout(() => {
      if (document.body) {
        document.body.appendChild(button);
        console.log('✅ Floating button added successfully (delayed)!');
      }
    }, 1000);
  }
}

// Save current page
async function saveCurrentPage(button) {
  const originalText = button.innerHTML;
  button.innerHTML = '⏳';
  button.style.background = '#f59e0b';

  try {
    console.log('Extracting content...');
    const extractor = new ContentExtractor();
    const data = extractor.extract();

    console.log('Extracted data:', {
      source: data.source,
      textLength: data.text.length,
      url: data.url
    });

    if (!data.text || data.text.length < 50) {
      throw new Error('Could not extract enough content from this page');
    }

    // Prepare payload
    const payload = {
      text: data.text,
      url: data.url,
      source: data.source,
      tags: []
    };

    console.log('Sending to backend...');

    // Send to backend
    const response = await fetch(`${BACKEND_URL}/api/bookmark`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Server error: ${response.status}`);
    }

    const result = await response.json();
    console.log('✅ Save successful:', result);

    // Success state
    button.innerHTML = '✅';
    button.style.background = '#10b981';

    // Show success notification
    showNotification(
      '✅ Saved Successfully!',
      `Source: ${data.source}\n\nTags: ${result.tags.join(', ')}\n\nSummary: ${result.summary.substring(0, 150)}...`,
      'success'
    );

    // Send stats to background
    chrome.runtime.sendMessage({ action: 'postSaved' });

    // Reset button
    setTimeout(() => {
      button.innerHTML = originalText;
      button.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
    }, 3000);

  } catch (error) {
    console.error('❌ Error:', error);

    // Error state
    button.innerHTML = '❌';
    button.style.background = '#ef4444';

    let errorMessage = 'Failed to save content.';
    if (error.message.includes('fetch')) {
      errorMessage += '\n\n⚠️ Backend not running!\nRun: python main.py';
    } else {
      errorMessage += `\n\nError: ${error.message}`;
    }

    showNotification('❌ Save Failed', errorMessage, 'error');

    // Reset button
    setTimeout(() => {
      button.innerHTML = originalText;
      button.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
    }, 3000);
  }
}

// Show notification
function showNotification(title, message, type) {
  // Remove existing notifications
  document.querySelectorAll('.cie-notification').forEach(n => n.remove());

  const notification = document.createElement('div');
  notification.className = 'cie-notification';
  notification.style.cssText = `
    position: fixed;
    top: 80px;
    right: 20px;
    min-width: 350px;
    max-width: 450px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
    z-index: 999999;
    animation: slideIn 0.3s ease-out;
    overflow: hidden;
    border-left: 5px solid ${type === 'success' ? '#10b981' : '#ef4444'};
  `;

  notification.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 16px; background: ${type === 'success' ? '#d1fae5' : '#fee2e2'};">
      <strong style="font-size: 16px; color: ${type === 'success' ? '#065f46' : '#991b1b'};">${title}</strong>
      <button class="cie-close" style="background: none; border: none; font-size: 28px; color: #6b7280; cursor: pointer; line-height: 1;">×</button>
    </div>
    <div style="padding: 16px; font-size: 14px; color: #374151; line-height: 1.6; white-space: pre-line;">${message}</div>
  `;

  document.body.appendChild(notification);

  // Close button
  notification.querySelector('.cie-close').addEventListener('click', () => {
    notification.remove();
  });

  // Auto remove after 8 seconds
  setTimeout(() => {
    if (notification.parentElement) {
      notification.remove();
    }
  }, 8000);
}

// Add CSS animation
const style = document.createElement('style');
style.textContent = `
  @keyframes slideIn {
    from {
      transform: translateX(500px);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
`;
document.head.appendChild(style);

// Initialize
function init() {
  console.log('🎯 Initializing CIE Agent Universal Extension...');
  console.log('📍 Current site:', window.location.hostname);

  // Create floating button
  createFloatingButton();

  console.log('✅ CIE Agent extension ready!');
}

// Start when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'saveCurrentPage') {
    const button = document.getElementById('cie-floating-btn');
    if (button) {
      saveCurrentPage(button);
    }
    sendResponse({ success: true });
  }
  return true;
});