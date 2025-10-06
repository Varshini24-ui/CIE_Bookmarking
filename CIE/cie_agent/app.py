import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import time

# Backend URL
BACKEND_URL = "http://127.0.0.1:8000"

# Page config
st.set_page_config(
    page_title="CIE Agent Pro",
    layout="wide",
    page_icon="📘",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(120deg, #1e3a8a, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #f0f2f6;
        border-radius: 8px 8px 0 0;
        padding: 0 24px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #667eea;
        color: white;
    }
    .tag-badge {
        display: inline-block;
        background: #667eea;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        margin: 0.25rem;
        font-size: 0.875rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'bookmarks_cache' not in st.session_state:
    st.session_state.bookmarks_cache = None
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = None
if 'stats_cache' not in st.session_state:
    st.session_state.stats_cache = None

# Helper functions
def check_backend():
    """Check if backend is online"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=3)
        return response.status_code == 200, response.json()
    except:
        return False, None

def fetch_stats():
    """Fetch statistics from backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/stats", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def fetch_bookmarks(limit=50):
    """Fetch all bookmarks"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/bookmarks?limit={limit}", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

# Header
st.markdown('<p class="main-header">📘 CIE Agent Pro</p>', unsafe_allow_html=True)
st.markdown("*Bridging the gap between CIE syllabus and industry trends with AI*")

# Sidebar
with st.sidebar:
    st.header("🎛️ Control Panel")
    
    # Backend status
    is_online, health_data = check_backend()
    
    if is_online:
        st.success("🟢 **Backend Online**")
        if health_data:
            with st.expander("📊 System Health"):
                st.json(health_data)
    else:
        st.error("🔴 **Backend Offline**")
        st.code("python main.py", language="bash")
        st.stop()
    
    st.markdown("---")
    
    # Quick stats
    st.subheader("📈 Quick Stats")
    if st.button("🔄 Refresh Stats"):
        st.session_state.stats_cache = None
    
    if st.session_state.stats_cache is None:
        with st.spinner("Loading stats..."):
            st.session_state.stats_cache = fetch_stats()
    
    if st.session_state.stats_cache:
        stats = st.session_state.stats_cache
        st.metric("Total Bookmarks", stats.get('total_bookmarks', 0))
        st.metric("Total Words", f"{stats.get('total_words', 0):,}")
        st.metric("Avg Words/Bookmark", f"{stats.get('avg_words_per_bookmark', 0):.0f}")
    
    st.markdown("---")
    
    # Theme info
    st.subheader("ℹ️ About")
    st.markdown("""
    **CIE Agent Pro** helps students identify gaps between Cambridge International Education syllabus and current industry trends.
    
    **Features:**
    - 💾 Smart bookmark saving
    - 🔍 Semantic search
    - 🤖 AI-powered suggestions
    - 📊 Analytics dashboard
    - 🏷️ Auto-tagging
    - 📝 Auto-summarization
    """)
    
    st.markdown("---")
    st.markdown("*Built with FastAPI, Streamlit, Qdrant & Gemini*")

# Main content tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "💾 Save Bookmark",
    "🔍 Search",
    "📚 My Bookmarks",
    "💡 Get Suggestions",
    "📊 Analytics",
    "⚙️ Manage"
])

# ==================== TAB 1: SAVE BOOKMARK ====================
with tab1:
    st.header("💾 Save a New Bookmark")
    st.markdown("Store interesting posts and articles for CIE gap analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("bookmark_form", clear_on_submit=True):
            bookmark_text = st.text_area(
                "📝 Content",
                placeholder="Paste the article, post, or content you want to bookmark...",
                height=200,
                help="The main text content you want to save"
            )
            
            col_a, col_b = st.columns(2)
            with col_a:
                bookmark_url = st.text_input(
                    "🔗 URL",
                    placeholder="https://example.com/article",
                    help="Link to the original content"
                )
            with col_b:
                bookmark_source = st.selectbox(
                    "📱 Source",
                    ["LinkedIn", "Twitter", "Medium", "Blog", "YouTube", "Research Paper", "Other"],
                    help="Where did you find this content?"
                )
            
            tags_input = st.text_input(
                "🏷️ Tags (optional)",
                placeholder="ai, machine-learning, data-science",
                help="Comma-separated tags. Leave empty for auto-generation."
            )
            
            col_submit, col_clear = st.columns([3, 1])
            with col_submit:
                submitted = st.form_submit_button("💾 Save Bookmark", use_container_width=True)
            with col_clear:
                st.form_submit_button("🗑️ Clear", use_container_width=True)
            
            if submitted and bookmark_text and bookmark_url and bookmark_source:
                # Parse tags
                tags = [t.strip() for t in tags_input.split(",")] if tags_input else []
                
                payload = {
                    "text": bookmark_text,
                    "url": bookmark_url,
                    "source": bookmark_source,
                    "tags": tags
                }
                
                with st.spinner("🤖 Saving bookmark, generating tags and summary..."):
                    try:
                        response = requests.post(
                            f"{BACKEND_URL}/api/bookmark",
                            json=payload,
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.success("✅ Bookmark saved successfully!")
                            
                            # Clear cache
                            st.session_state.bookmarks_cache = None
                            st.session_state.stats_cache = None
                            
                            # Display results
                            col_res1, col_res2 = st.columns(2)
                            with col_res1:
                                st.info(f"**ID:** `{result.get('id', 'N/A')}`")
                                st.info(f"**Word Count:** {result.get('word_count', 0)}")
                            with col_res2:
                                tags_display = result.get('tags', [])
                                if tags_display:
                                    st.markdown("**🏷️ Generated Tags:**")
                                    st.markdown(" ".join([f"`{tag}`" for tag in tags_display]))
                            
                            with st.expander("📝 View Summary"):
                                st.write(result.get('summary', 'No summary available'))
                            
                            with st.expander("👁️ Preview"):
                                st.write(result.get('preview', 'No preview'))
                        else:
                            st.error(f"❌ Failed to save: {response.status_code}")
                            st.code(response.text)
                    
                    except requests.exceptions.ConnectionError:
                        st.error("🚨 Backend connection failed")
                    except Exception as e:
                        st.error(f"🚨 Error: {str(e)}")
            
            elif submitted:
                st.warning("⚠️ Please fill in all required fields")
    
    with col2:
        st.info("💡 **Pro Tips**")
        st.markdown("""
        - Paste longer content for better analysis
        - Tags are auto-generated if not provided
        - AI generates summaries automatically
        - Use descriptive URLs
        - Choose accurate sources
        """)

# ==================== TAB 2: SEARCH ====================
with tab2:
    st.header("🔍 Semantic Search")
    st.markdown("Find relevant bookmarks using natural language queries")
    
    search_col1, search_col2 = st.columns([3, 1])
    
    with search_col1:
        search_query = st.text_input(
            "Search Query",
            placeholder="e.g., transformer architecture, edge computing, react hooks...",
            help="Enter natural language search query"
        )
    
    with search_col2:
        search_limit = st.number_input("Results", min_value=1, max_value=50, value=10)
    
    source_filter = st.selectbox(
        "Filter by Source (optional)",
        ["All Sources", "LinkedIn", "Twitter", "Medium", "Blog", "YouTube", "Research Paper", "GitHub", "Stack Overflow", "Reddit", "Other"]
    )
    
    if st.button("🔍 Search", use_container_width=True):
        if search_query:
            # Convert "All Sources" to None
            filter_val = None if source_filter == "All Sources" else source_filter
            
            payload = {
                "query": search_query,
                "limit": search_limit,
                "source_filter": filter_val
            }
            
            with st.spinner("Searching..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/api/search",
                        json=payload,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        results = data.get('results', [])
                        
                        if results:
                            st.success(f"✅ Found {len(results)} results")
                            
                            for i, result in enumerate(results, 1):
                                with st.expander(f"#{i} - Score: {result['score']:.3f} - {result['source']}"):
                                    st.markdown(f"**🔗 URL:** [{result['url']}]({result['url']})")
                                    st.markdown(f"**📝 Summary:** {result['summary']}")
                                    st.markdown(f"**📄 Preview:** {result['text']}")
                                    
                                    if result.get('tags'):
                                        st.markdown("**🏷️ Tags:** " + " ".join([f"`{tag}`" for tag in result['tags']]))
                                    
                                    st.caption(f"Created: {result.get('created_at', 'Unknown')}")
                        else:
                            st.warning("No results found")
                    else:
                        st.error(f"Search failed: {response.status_code}")
                
                except Exception as e:
                    st.error(f"🚨 Error: {str(e)}")
        else:
            st.warning("Please enter a search query")

# ==================== TAB 3: MY BOOKMARKS ====================
with tab3:
    st.header("📚 My Bookmarks Library")
    
    col_refresh, col_limit = st.columns([3, 1])
    with col_refresh:
        if st.button("🔄 Refresh Bookmarks", use_container_width=True):
            st.session_state.bookmarks_cache = None
    with col_limit:
        display_limit = st.number_input("Show", min_value=10, max_value=100, value=50, step=10)
    
    # Fetch bookmarks
    if st.session_state.bookmarks_cache is None:
        with st.spinner("Loading bookmarks..."):
            st.session_state.bookmarks_cache = fetch_bookmarks(display_limit)
            st.session_state.last_refresh = datetime.now()
    
    if st.session_state.bookmarks_cache:
        data = st.session_state.bookmarks_cache
        bookmarks = data.get('bookmarks', [])
        
        if bookmarks:
            st.info(f"📊 Showing {len(bookmarks)} bookmarks | Last refresh: {st.session_state.last_refresh.strftime('%H:%M:%S')}")
            
            # Filter options
            col_filter1, col_filter2 = st.columns(2)
            with col_filter1:
                sources = list(set([b['source'] for b in bookmarks]))
                source_filter = st.multiselect("Filter by Source", sources, default=sources)
            
            with col_filter2:
                all_tags = []
                for b in bookmarks:
                    all_tags.extend(b.get('tags', []))
                unique_tags = list(set(all_tags))
                tag_filter = st.multiselect("Filter by Tags", unique_tags)
            
            # Apply filters
            filtered_bookmarks = bookmarks
            if source_filter:
                filtered_bookmarks = [b for b in filtered_bookmarks if b['source'] in source_filter]
            if tag_filter:
                filtered_bookmarks = [b for b in filtered_bookmarks if any(tag in b.get('tags', []) for tag in tag_filter)]
            
            st.markdown(f"**{len(filtered_bookmarks)} bookmarks** match your filters")
            
            # Display bookmarks
            for i, bookmark in enumerate(filtered_bookmarks, 1):
                with st.container():
                    col_content, col_actions = st.columns([5, 1])
                    
                    with col_content:
                        st.markdown(f"### {i}. {bookmark['source']} Bookmark")
                        st.markdown(f"**🔗 URL:** [{bookmark['url']}]({bookmark['url']})")
                        
                        with st.expander("📝 Summary & Details"):
                            st.markdown(f"**Summary:** {bookmark.get('summary', 'No summary')}")
                            st.markdown(f"**Full Text:** {bookmark.get('full_text', bookmark.get('text', ''))}")
                            st.caption(f"Words: {bookmark.get('word_count', 0)} | Created: {bookmark.get('created_at', 'Unknown')}")
                        
                        if bookmark.get('tags'):
                            st.markdown("**🏷️ Tags:** " + " ".join([f"`{tag}`" for tag in bookmark['tags']]))
                    
                    with col_actions:
                        if st.button("🗑️", key=f"del_{bookmark['id']}", help="Delete this bookmark"):
                            try:
                                response = requests.delete(f"{BACKEND_URL}/api/bookmark/{bookmark['id']}")
                                if response.status_code == 200:
                                    st.success("Deleted!")
                                    st.session_state.bookmarks_cache = None
                                    st.session_state.stats_cache = None
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("Delete failed")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                    
                    st.markdown("---")
        else:
            st.info("📭 No bookmarks yet. Start by saving your first bookmark!")
    else:
        st.error("Failed to load bookmarks")

# ==================== TAB 4: SUGGESTIONS ====================
with tab4:
    st.header("💡 AI-Powered CIE Concept Suggestions")
    st.markdown("Get personalized suggestions for bridging CIE syllabus gaps")
    
    col_input, col_info = st.columns([2, 1])
    
    with col_input:
        suggestion_text = st.text_area(
            "📝 Enter Content for Analysis",
            placeholder="Paste content about industry trends, new technologies, or concepts...",
            height=250,
            help="The AI will analyze this content and suggest relevant CIE concepts"
        )
        
        analysis_depth = st.select_slider(
            "Analysis Depth",
            options=["Quick", "Standard", "Detailed"],
            value="Standard"
        )
        
        if st.button("🤖 Generate Suggestions", use_container_width=True):
            if suggestion_text:
                payload = {"text": suggestion_text}
                
                progress_text = "Analyzing content with AI..."
                progress_bar = st.progress(0, text=progress_text)
                
                try:
                    for i in range(100):
                        time.sleep(0.02)
                        progress_bar.progress(i + 1, text=f"{progress_text} {i+1}%")
                    
                    response = requests.post(
                        f"{BACKEND_URL}/api/suggest",
                        json=payload,
                        timeout=45
                    )
                    
                    progress_bar.empty()
                    
                    if response.status_code == 200:
                        data = response.json()
                        suggestions_text = data.get('suggestions', '')
                        
                        st.success("✅ Suggestions Generated!")
                        
                        st.markdown("### 📚 Recommended CIE Concepts to Add:")
                        
                        # Try to parse as JSON for better display
                        try:
                            # Remove markdown code blocks if present
                            clean_text = suggestions_text.replace('```json', '').replace('```', '').strip()
                            suggestions_list = json.loads(clean_text)
                            
                            for idx, suggestion in enumerate(suggestions_list, 1):
                                with st.expander(f"🎯 Concept {idx}: {suggestion.get('concept', 'Unknown')}"):
                                    st.markdown(f"**📖 Concept:** {suggestion.get('concept', 'N/A')}")
                                    st.markdown(f"**💭 Reason:** {suggestion.get('reason', 'N/A')}")
                                    st.markdown(f"**📊 Difficulty:** `{suggestion.get('difficulty', 'N/A')}`")
                                    
                                    related = suggestion.get('related_topics', [])
                                    if related:
                                        st.markdown("**🔗 Related Topics:** " + ", ".join([f"`{t}`" for t in related]))
                        
                        except json.JSONDecodeError:
                            # Display as markdown if not valid JSON
                            st.markdown(suggestions_text)
                        
                        with st.expander("🔍 View Raw Response"):
                            st.json(data.get('raw_response', {}))
                    
                    else:
                        st.error(f"❌ Failed to generate suggestions: {response.status_code}")
                        st.code(response.text)
                
                except requests.exceptions.Timeout:
                    progress_bar.empty()
                    st.error("🚨 Request timed out. The AI is taking too long to respond.")
                except Exception as e:
                    progress_bar.empty()
                    st.error(f"🚨 Error: {str(e)}")
            
            else:
                st.warning("⚠️ Please enter some content to analyze")
    
    with col_info:
        st.info("💡 **How It Works**")
        st.markdown("""
        1. **Paste Content**: Add any industry-related content
        2. **AI Analysis**: Gemini AI analyzes the content
        3. **Get Suggestions**: Receive specific CIE concepts to learn
        4. **Bridge Gaps**: Stay updated with industry trends
        
        **Best Results:**
        - Technical articles
        - Industry trends
        - New frameworks
        - Research papers
        - Technology blogs
        """)
        
        st.success("🎯 **Example Topics**")
        st.markdown("""
        - Cloud computing patterns
        - Modern web frameworks
        - AI/ML algorithms
        - DevOps practices
        - Microservices architecture
        """)

# ==================== TAB 5: ANALYTICS ====================
with tab5:
    st.header("📊 Analytics Dashboard")
    
    if st.button("🔄 Refresh Analytics"):
        st.session_state.stats_cache = None
    
    if st.session_state.stats_cache is None:
        with st.spinner("Loading analytics..."):
            st.session_state.stats_cache = fetch_stats()
    
    if st.session_state.stats_cache:
        stats = st.session_state.stats_cache
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "📚 Total Bookmarks",
                stats.get('total_bookmarks', 0),
                delta=None
            )
        
        with col2:
            st.metric(
                "📝 Total Words",
                f"{stats.get('total_words', 0):,}",
                delta=None
            )
        
        with col3:
            st.metric(
                "📊 Avg Words",
                f"{stats.get('avg_words_per_bookmark', 0):.0f}",
                delta=None
            )
        
        with col4:
            sources_count = len(stats.get('sources', {}))
            st.metric(
                "📱 Sources Used",
                sources_count,
                delta=None
            )
        
        st.markdown("---")
        
        # Charts
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.subheader("📱 Bookmarks by Source")
            sources = stats.get('sources', {})
            if sources:
                df_sources = pd.DataFrame(list(sources.items()), columns=['Source', 'Count'])
                df_sources = df_sources.sort_values('Count', ascending=False)
                st.bar_chart(df_sources.set_index('Source'))
            else:
                st.info("No source data available")
        
        with col_chart2:
            st.subheader("🏷️ Top Tags")
            top_tags = stats.get('top_tags', {})
            if top_tags:
                df_tags = pd.DataFrame(list(top_tags.items()), columns=['Tag', 'Count'])
                df_tags = df_tags.sort_values('Count', ascending=False).head(10)
                st.bar_chart(df_tags.set_index('Tag'))
            else:
                st.info("No tag data available")
        
        # Detailed breakdown
        st.markdown("---")
        st.subheader("📋 Detailed Breakdown")
        
        col_detail1, col_detail2 = st.columns(2)
        
        with col_detail1:
            st.markdown("**📱 Sources Distribution**")
            if sources:
                for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / stats.get('total_bookmarks', 1)) * 100
                    st.progress(percentage / 100, text=f"{source}: {count} ({percentage:.1f}%)")
        
        with col_detail2:
            st.markdown("**🏷️ Top 10 Tags**")
            if top_tags:
                for tag, count in list(top_tags.items())[:10]:
                    st.markdown(f"- **{tag}**: {count} bookmarks")
    
    else:
        st.error("Failed to load analytics data")

# ==================== TAB 6: MANAGE ====================
with tab6:
    st.header("⚙️ Manage Data")
    
    st.subheader("📤 Export Data")
    st.markdown("Download all your bookmarks as JSON")
    
    if st.button("📥 Export All Bookmarks", use_container_width=True):
        with st.spinner("Exporting..."):
            try:
                response = requests.get(f"{BACKEND_URL}/api/export", timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    bookmarks = data.get('bookmarks', [])
                    
                    # Convert to JSON string
                    json_str = json.dumps(bookmarks, indent=2)
                    
                    st.success(f"✅ Exported {len(bookmarks)} bookmarks")
                    
                    st.download_button(
                        label="💾 Download JSON",
                        data=json_str,
                        file_name=f"cie_bookmarks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        use_container_width=True
                    )
                    
                    with st.expander("👁️ Preview Export"):
                        st.json(bookmarks[:5])  # Show first 5
                else:
                    st.error(f"Export failed: {response.status_code}")
            except Exception as e:
                st.error(f"🚨 Error: {str(e)}")
    
    st.markdown("---")
    
    st.subheader("🧹 Data Management")
    
    col_warn1, col_warn2 = st.columns(2)
    
    with col_warn1:
        st.warning("⚠️ **Clear Cache**")
        st.markdown("Refresh all cached data")
        if st.button("🗑️ Clear Cache", use_container_width=True):
            st.session_state.bookmarks_cache = None
            st.session_state.stats_cache = None
            st.success("Cache cleared!")
            time.sleep(1)
            st.rerun()
    
    with col_warn2:
        st.info("💡 **Tips**")
        st.markdown("""
        - Export regularly for backups
        - Clear cache if data seems outdated
        - Use filters in My Bookmarks for better organization
        """)
    
    st.markdown("---")
    
    st.subheader("🔧 System Information")
    
    with st.expander("📋 Backend Info"):
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=5)
            if response.status_code == 200:
                st.json(response.json())
        except:
            st.error("Could not fetch backend info")
    
    st.markdown("---")
    st.caption("CIE Agent Pro v2.0 | Built with ❤️ using FastAPI, Streamlit, Qdrant & Gemini")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><strong>CIE Agent Pro</strong> - Empowering Students with AI-Driven Learning</p>
    <p>💡 Tips: Use semantic search to find similar content | Let AI auto-generate tags | Export your data regularly</p>
</div>
""", unsafe_allow_html=True)