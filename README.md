CIE Agent 
AI-Powered Universal Bookmark System - Save content from ANY website, get AI summaries & tags, bridge CIE syllabus gaps

Integrated Components:

1.  Universal Chrome Extension
   - Works on ALL websites (LinkedIn, Medium, Twitter, ArXiv, GitHub, Blogs, Papers, etc.)
   - Floating save button on every page
   - Right-click context menu
   - Auto-extracts content intelligently

2.  FastAPI Backend
   - RESTful API
   - AI-powered auto-tagging (google/flan-t5-base)
   - Auto-summarization (facebook/bart-large-cnn)
   - Vector embeddings (Sentence Transformers)
   - Semantic search (Qdrant)

3.  Streamlit Web App
   - dashboard
   - Semantic search
   - Analytics & statistics
   - AI concept suggestions
   - Export capabilities

---


1. Install Backend

```bash
# Clone/create project folder
mkdir cie-agent-pro
cd cie-agent-pro

# Install dependencies
pip install -r requirements.txt

# Create .env file with your API keys
echo "QDRANT_URL=your_url" > .env
echo "QDRANT_API_KEY=your_key" >> .env
echo "GEMINI_API_KEY=your_key" >> .env

# Start backend
python main.py
```

 2. Install Frontend

```bash
# In same folder (new terminal)
streamlit run app.py
```

3. Install Extension

```bash
# Create extension folder
mkdir cie-agent-extension
cd cie-agent-extension

# Copy all extension files (manifest.json, content.js, etc.)
# Create icons folder with 3 PNG files

# In Chrome:
# 1. Go to chrome://extensions/
# 2. Enable "Developer mode"
# 3. Click "Load unpacked"
# 4. Select cie-agent-extension folder
```


 Save Content from Anywhere

```
1. Browse ANY website:
    LinkedIn post
    Medium article  
    Twitter thread
    ArXiv paper
    GitHub README
    Blog post
    YouTube video
    Stack Overflow answer
   
2. Click floating 📘 button (bottom-right)
   OR right-click → "Save to CIE Agent"
   OR click extension icon → "Save Current Page"

3. Extension extracts content

4. Backend processes (2-3 seconds):
    Generates embeddings
    Auto-generates tags
    Creates summary
    Saves to database

5. Success notification appears!
```

Search Your Bookmarks

```
1. Open Streamlit app (localhost:8501)
2. Go to "🔍 Search" tab
3. Enter natural language query:
   "machine learning algorithms"
4. Get ranked results with scores
```

Get AI Suggestions

```
1. Go to "💡 Suggestions" tab
2. Paste industry content
3. Click "Generate Suggestions"
4. Get CIE concept recommendations
```

View Analytics

```
1. Go to "📊 Analytics" tab
2. See:
   - Total bookmarks
   - Source distribution
   - Top tags
   - Word count stats
3. Interactive charts
```

---

 Key Features

Universal Extension
- Works Everywhere: LinkedIn, Medium, Twitter, ArXiv, GitHub, Blogs, Papers
- Smart Extraction: Intelligent content detection for each site
- Multiple Methods: Floating button, context menu, popup, keyboard
- Real-time Feedback: Loading states, success/error notifications
- Statistics: Track saves per day, total saves

🤖 AI-Powered Backend
- Auto-Tagging
- Auto-Summary
- Semantic Search: Find similar content using vector similarity
- REST API: Full CRUD operations
