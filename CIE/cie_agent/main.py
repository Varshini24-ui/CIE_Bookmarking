from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from datetime import datetime
import os
import requests
import uuid
import json
import time

# Load environment variables
load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

POST_COLLECTION = "cie_posts"

print("=" * 50)
print("CIE AGENT BACKEND INITIALIZATION")
print("=" * 50)
print("QDRANT_URL:", QDRANT_URL)
print("QDRANT_API_KEY:", QDRANT_API_KEY[:6] + "..." if QDRANT_API_KEY else "MISSING")
print("HUGGINGFACE_API_KEY:", HUGGINGFACE_API_KEY[:6] + "..." if HUGGINGFACE_API_KEY else "MISSING")
print("=" * 50)

# Initialize FastAPI
app = FastAPI(title="CIE Agent Backend", version="2.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Qdrant
try:
    qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    print("✅ Qdrant client initialized")
    
    collections = qdrant.get_collections().collections
    collection_names = [c.name for c in collections]
    
    if POST_COLLECTION not in collection_names:
        qdrant.create_collection(
            collection_name=POST_COLLECTION,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        print(f"✅ Created collection: {POST_COLLECTION}")
    else:
        print(f"✅ Collection exists: {POST_COLLECTION}")
except Exception as e:
    print(f"❌ Qdrant error: {e}")
    qdrant = None

# Initialize embedder
embedder = SentenceTransformer("all-MiniLM-L6-v2")
print("✅ Sentence transformer loaded")

# Pydantic models
class Bookmark(BaseModel):
    text: str
    url: str
    source: str
    tags: Optional[List[str]] = []

class Query(BaseModel):
    text: str
    top_k: Optional[int] = 5

class SearchQuery(BaseModel):
    query: str
    limit: Optional[int] = 10
    source_filter: Optional[str] = None

class SummarizeRequest(BaseModel):
    text: str

# Helper: Call Hugging Face API with retry
def call_huggingface_api(model_id: str, prompt: str, max_retries: int = 3) -> str:
    """Call Hugging Face Inference API with retry logic"""
    if not HUGGINGFACE_API_KEY:
        return None
    
    url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                url,
                headers=headers,
                json={"inputs": prompt, "parameters": {"max_new_tokens": 250, "temperature": 0.7}},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Handle different response formats
                if isinstance(result, list) and len(result) > 0:
                    if isinstance(result[0], dict):
                        return result[0].get("generated_text", result[0].get("summary_text", ""))
                    return str(result[0])
                elif isinstance(result, dict):
                    return result.get("generated_text", result.get("summary_text", ""))
                return str(result)
            
            elif response.status_code == 503:
                # Model loading - wait and retry
                print(f"⏳ Model loading, waiting {5 * (attempt + 1)} seconds...")
                time.sleep(5 * (attempt + 1))
                continue
            
            else:
                print(f"❌ API Error: {response.status_code}")
                return None
        
        except Exception as e:
            print(f"❌ Exception: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            return None
    
    return None

# Generate summary using Hugging Face
def generate_summary_hf(text: str) -> str:
    """Generate summary using Hugging Face"""
    # Try summarization model
    summary = call_huggingface_api(
        "facebook/bart-large-cnn",
        text[:1024]  # BART has 1024 token limit
    )
    
    if summary and len(summary) > 20:
        return summary.strip()
    
    # Fallback: extractive summary
    sentences = text.replace('!', '.').replace('?', '.').split('.')
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    
    if sentences:
        summary = ". ".join(sentences[:3]) + "."
        return summary[:300]
    
    return "Summary unavailable"

# Generate tags using Hugging Face
def generate_tags_hf(text: str) -> List[str]:
    """Generate tags using Hugging Face"""
    prompt = f"Extract 5 technical keywords from this text as comma-separated values:\n\n{text[:500]}\n\nKeywords:"
    
    result = call_huggingface_api("google/flan-t5-base", prompt)
    
    if result:
        tags = [t.strip() for t in result.split(",")]
        tags = [t for t in tags if t and len(t) > 1][:5]
        if tags:
            return tags
    
    # Fallback: keyword extraction
    text_lower = text.lower()
    tech_keywords = {
        "ai": ["artificial intelligence", "ai", "machine learning", "ml", "deep learning"],
        "data": ["data science", "data", "analytics", "big data"],
        "web": ["web", "html", "css", "javascript", "frontend"],
        "mobile": ["mobile", "android", "ios", "app"],
        "cloud": ["cloud", "aws", "azure", "gcp"],
        "python": ["python", "django", "flask"],
        "java": ["java", "spring"],
        "security": ["security", "cybersecurity", "encryption"],
        "blockchain": ["blockchain", "crypto"],
        "api": ["api", "rest", "graphql"]
    }
    
    found_tags = []
    for tag, keywords in tech_keywords.items():
        if any(kw in text_lower for kw in keywords):
            found_tags.append(tag)
            if len(found_tags) >= 5:
                break
    
    return found_tags if found_tags else ["technology", "article"]

# Generate CIE suggestions using Hugging Face
def generate_cie_suggestions_hf(text: str) -> str:
    """Generate CIE concept suggestions using Hugging Face"""
    
    prompt = f"""As an education expert, analyze this content and suggest 3 Computer Science topics for CIE syllabus:

Content: {text[:1000]}

Suggest 3 topics with:
1. Concept name
2. Why it's important
3. Difficulty level

Format as numbered list."""
    
    result = call_huggingface_api("google/flan-t5-large", prompt)
    
    if result and len(result) > 50:
        # Parse and format as JSON
        try:
            suggestions = []
            lines = result.split('\n')
            
            concept_name = ""
            for line in lines[:9]:  # Process first 9 lines (3 topics × 3 lines each)
                line = line.strip()
                if line and not line.startswith(('1.', '2.', '3.', '-')):
                    if len(suggestions) < 3:
                        suggestions.append({
                            "concept": line[:100],
                            "reason": "Bridges gap between CIE syllabus and industry practice",
                            "difficulty": "Intermediate",
                            "related_topics": []
                        })
            
            if suggestions:
                return json.dumps(suggestions, indent=2)
        except:
            pass
    
    # Fallback: rule-based suggestions
    text_lower = text.lower()
    suggestions = []
    
    if any(kw in text_lower for kw in ["ai", "machine learning", "ml", "neural"]):
        suggestions.append({
            "concept": "AI & Machine Learning Fundamentals",
            "reason": "Essential for understanding modern AI systems and automation",
            "difficulty": "Intermediate",
            "related_topics": ["Neural Networks", "Data Science"]
        })
    
    if any(kw in text_lower for kw in ["cloud", "aws", "azure", "serverless"]):
        suggestions.append({
            "concept": "Cloud Computing Architecture",
            "reason": "Critical for scalable applications and modern deployment",
            "difficulty": "Intermediate",
            "related_topics": ["Distributed Systems", "DevOps"]
        })
    
    if any(kw in text_lower for kw in ["api", "rest", "microservices"]):
        suggestions.append({
            "concept": "API Design & Microservices",
            "reason": "Modern software architecture used across industry",
            "difficulty": "Intermediate",
            "related_topics": ["Web Services", "HTTP"]
        })
    
    if not suggestions:
        suggestions.append({
            "concept": "Modern Software Development",
            "reason": "Industry-standard practices for quality software",
            "difficulty": "Intermediate",
            "related_topics": ["Agile", "Testing"]
        })
    
    return json.dumps(suggestions[:3], indent=2)

# Endpoints
@app.get("/")
def root():
    return {
        "message": "CIE Agent Backend v2.0 is running!",
        "status": "healthy",
        "qdrant_connected": qdrant is not None,
        "ai_provider": "Hugging Face",
        "ai_configured": HUGGINGFACE_API_KEY is not None
    }

@app.get("/health")
def health_check():
    health = {
        "status": "healthy",
        "qdrant": "disconnected",
        "embedder": "loaded",
        "ai": "huggingface",
        "ai_configured": "yes" if HUGGINGFACE_API_KEY else "no"
    }
    
    if qdrant:
        try:
            collections = qdrant.get_collections()
            health["qdrant"] = "connected"
            health["collections"] = [c.name for c in collections.collections]
        except:
            health["qdrant"] = "error"
    
    return health

@app.post("/api/bookmark")
def save_bookmark(bookmark: Bookmark):
    """Save bookmark with AI-generated tags and summary"""
    if not qdrant:
        raise HTTPException(status_code=500, detail="Qdrant not initialized")

    try:
        # Generate embedding
        vec = embedder.encode(bookmark.text).tolist()
        point_id = str(uuid.uuid4())
        
        # Auto-generate tags
        print(f"Generating tags for: {bookmark.text[:50]}...")
        tags = bookmark.tags if bookmark.tags else generate_tags_hf(bookmark.text)
        print(f"Generated tags: {tags}")
        
        # Generate summary
        print(f"Generating summary...")
        summary = generate_summary_hf(bookmark.text)
        print(f"Generated summary: {summary[:100]}...")
        
        # Prepare payload
        payload = {
            "text": bookmark.text,
            "url": bookmark.url,
            "source": bookmark.source,
            "tags": tags,
            "summary": summary,
            "created_at": datetime.now().isoformat(),
            "word_count": len(bookmark.text.split())
        }
        
        # Save to Qdrant
        qdrant.upsert(
            collection_name=POST_COLLECTION,
            points=[PointStruct(id=point_id, vector=vec, payload=payload)]
        )
        
        print(f"✅ Saved bookmark: {point_id}")
        
        return {
            "status": "saved",
            "id": point_id,
            "preview": bookmark.text[:100] + "...",
            "tags": tags,
            "summary": summary,
            "word_count": payload["word_count"]
        }

    except Exception as e:
        print(f"❌ Error saving bookmark: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/api/search")
def search_bookmarks(search: SearchQuery):
    """Semantic search through bookmarks"""
    if not qdrant:
        raise HTTPException(status_code=500, detail="Qdrant not initialized")
    
    try:
        print(f"Search query: '{search.query}', Source filter: '{search.source_filter}'")
        
        query_vec = embedder.encode(search.query).tolist()
        
        search_filter = None
        if search.source_filter and search.source_filter.lower() not in ["all", "all sources", ""]:
            try:
                search_filter = Filter(
                    must=[
                        FieldCondition(
                            key="source",
                            match=MatchValue(value=search.source_filter)
                        )
                    ]
                )
                print(f"Using filter for source: {search.source_filter}")
            except Exception as filter_error:
                print(f"Filter error: {filter_error}, searching without filter")
                search_filter = None
        
        results = qdrant.search(
            collection_name=POST_COLLECTION,
            query_vector=query_vec,
            limit=search.limit,
            query_filter=search_filter
        )
        
        print(f"Found {len(results)} results")
        
        bookmarks = []
        for hit in results:
            bookmarks.append({
                "id": hit.id,
                "score": hit.score,
                "text": hit.payload.get("text", "")[:200] + "...",
                "url": hit.payload.get("url", ""),
                "source": hit.payload.get("source", ""),
                "tags": hit.payload.get("tags", []),
                "summary": hit.payload.get("summary", ""),
                "created_at": hit.payload.get("created_at", "")
            })
        
        return {"results": bookmarks, "count": len(bookmarks)}
    
    except Exception as e:
        print(f"❌ Search error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.get("/api/bookmarks")
def get_all_bookmarks(limit: int = 50, offset: int = 0):
    """Get all bookmarks"""
    if not qdrant:
        raise HTTPException(status_code=500, detail="Qdrant not initialized")
    
    try:
        records, next_offset = qdrant.scroll(
            collection_name=POST_COLLECTION,
            limit=limit,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )
        
        bookmarks = []
        for record in records:
            bookmarks.append({
                "id": record.id,
                "text": record.payload.get("text", "")[:200] + "...",
                "full_text": record.payload.get("text", ""),
                "url": record.payload.get("url", ""),
                "source": record.payload.get("source", ""),
                "tags": record.payload.get("tags", []),
                "summary": record.payload.get("summary", ""),
                "created_at": record.payload.get("created_at", ""),
                "word_count": record.payload.get("word_count", 0)
            })
        
        return {
            "bookmarks": bookmarks,
            "count": len(bookmarks),
            "offset": offset,
            "next_offset": next_offset
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.delete("/api/bookmark/{bookmark_id}")
def delete_bookmark(bookmark_id: str):
    """Delete a bookmark"""
    if not qdrant:
        raise HTTPException(status_code=500, detail="Qdrant not initialized")
    
    try:
        qdrant.delete(
            collection_name=POST_COLLECTION,
            points_selector=[bookmark_id]
        )
        return {"status": "deleted", "id": bookmark_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete error: {str(e)}")

@app.get("/api/stats")
def get_statistics():
    """Get statistics"""
    if not qdrant:
        raise HTTPException(status_code=500, detail="Qdrant not initialized")
    
    try:
        collection_info = qdrant.get_collection(POST_COLLECTION)
        
        records, _ = qdrant.scroll(
            collection_name=POST_COLLECTION,
            limit=1000,
            with_payload=True,
            with_vectors=False
        )
        
        sources = {}
        tags_count = {}
        total_words = 0
        
        for record in records:
            source = record.payload.get("source", "Unknown")
            sources[source] = sources.get(source, 0) + 1
            
            for tag in record.payload.get("tags", []):
                tags_count[tag] = tags_count.get(tag, 0) + 1
            
            total_words += record.payload.get("word_count", 0)
        
        top_tags = sorted(tags_count.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_bookmarks": collection_info.points_count,
            "sources": sources,
            "top_tags": dict(top_tags),
            "total_words": total_words,
            "avg_words_per_bookmark": total_words / max(len(records), 1)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")

@app.post("/api/suggest")
def suggest_new_concept(query: Query):
    """Get CIE concept suggestions using Hugging Face"""
    
    try:
        print(f"Generating CIE suggestions for: {query.text[:50]}...")
        suggestions = generate_cie_suggestions_hf(query.text)
        print(f"Generated suggestions")
        
        return {
            "suggestions": suggestions,
            "status": "success"
        }
        
    except Exception as e:
        print(f"❌ Error generating suggestions: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/api/summarize")
def summarize_text(request: SummarizeRequest):
    """Generate summary"""
    summary = generate_summary_hf(request.text)
    return {"summary": summary}

@app.get("/api/export")
def export_bookmarks():
    """Export all bookmarks"""
    if not qdrant:
        raise HTTPException(status_code=500, detail="Qdrant not initialized")
    
    try:
        records, _ = qdrant.scroll(
            collection_name=POST_COLLECTION,
            limit=10000,
            with_payload=True,
            with_vectors=False
        )
        
        bookmarks = []
        for record in records:
            bookmarks.append({
                "id": record.id,
                "text": record.payload.get("text", ""),
                "url": record.payload.get("url", ""),
                "source": record.payload.get("source", ""),
                "tags": record.payload.get("tags", []),
                "summary": record.payload.get("summary", ""),
                "created_at": record.payload.get("created_at", "")
            })
        
        return {"bookmarks": bookmarks, "count": len(bookmarks)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")

# Run server
if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Starting CIE Agent Backend with Hugging Face AI...")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")