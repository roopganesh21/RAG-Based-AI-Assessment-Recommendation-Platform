# app.py - SHL Assessment Consultant
import streamlit as st
import requests
import json

# --- CONFIGURATION ---
API_URL = "http://127.0.0.1:8000/strategy"

# Page Configuration
st.set_page_config(
    page_title="SHL Talent Strategy",
    page_icon="blob:https://shl.com/favicon.ico", # Placeholder or emoji
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    /* Main Layout Tweaks */
    .main .block-container {
        padding-top: 2rem;
        max-width: 1200px;
    }
    
    /* Assessment Cards */
    .assessment-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        transition: box-shadow 0.2s;
    }
    .assessment-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border-color: #0EA5E9;
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 0.25em 0.6em;
        font-size: 0.75rem;
        font-weight: 600;
        line-height: 1;
        text-align: center;
        white-space: nowrap;
        vertical-align: baseline;
        border-radius: 0.25rem;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .badge-tech { background-color: #e0f2fe; color: #0369a1; } /* Blue */
    .badge-behav { background-color: #f3e8ff; color: #7e22ce; } /* Purple */
    
    /* Strategy Box */
    .strategy-box {
        background-color: #f8fafc;
        border-left: 5px solid #0f172a;
        padding: 2rem;
        border-radius: 4px;
        color: #334155;
        line-height: 1.6;
    }
    
    /* Headers */
    h1, h2, h3 { color: #0f172a; font-family: 'Helvetica Neue', sans-serif; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Google_%22G%22_logo.svg/768px-Google_%22G%22_logo.svg.png", width=40)
    st.title("Talent Architect")
    st.markdown("Powered by **Gemini 1.5**")
    
    st.divider()
    
    st.subheader("⚙️ Configuration")
    
    # 1. Detail Level Control (Address the 'short response' issue)
    detail_level = st.select_slider(
        "Response Detail Level",
        options=["Executive Summary", "Standard", "Deep Dive"],
        value="Standard",
        help="Controls the depth of the AI's strategic analysis."
    )
    
    num_matches = st.slider("Max Assessments to Find", 3, 15, 8)
    
    st.divider()
    
    with st.expander("ℹ️ How to use"):
        st.markdown("""
        1. **Define Role:** Enter the job title and key tech stack.
        2. **Generate:** AI retrieves SHL tests and builds a strategy.
        3. **Review:** Check the 'Strategy' tab for the plan and 'Catalog' for specific test links.
        """)

# --- MAIN HEADER ---
st.title("SHL Assessment Consultant")
st.markdown("""
<p style='font-size: 1.2rem; color: #64748b; margin-bottom: 2rem;'>
    Design data-driven hiring processes. Enter a job requirement below to generate a validated assessment strategy combining technical skills and behavioral traits.
</p>
""", unsafe_allow_html=True)

# --- INPUT SECTION ---
with st.container():
    col1, col2 = st.columns([5, 1])
    with col1:
        query = st.text_input(
            "Job Role / Competency Requirement", 
            placeholder="e.g. Senior Data Scientist with Python, SQL and Leadership skills",
            label_visibility="collapsed"
        )
    with col2:
        generate_btn = st.button("Build Strategy", type="primary", use_container_width=True)

# --- LOGIC & DISPLAY ---
if generate_btn and query:
    # Progress UI
    progress_text = "Consulting SHL Database..."
    my_bar = st.progress(0, text=progress_text)

    try:
        # Prepare payload
        payload = {
            "query": query, 
            "top_k": num_matches,
            "detail_level": detail_level # Pass this to backend if supported
        }
        
        # API Call
        my_bar.progress(30, text="Analyzing Context with Gemini...")
        response = requests.post(API_URL, json=payload, timeout=45)
        my_bar.progress(80, text="Finalizing Recommendations...")
        
        if response.status_code == 200:
            data = response.json()
            my_bar.progress(100, text="Complete!")
            my_bar.empty()
            
            # --- RESULTS LAYOUT ---
            tab1, tab2, tab3 = st.tabs(["📄 Strategic Plan", "🔍 Assessment Catalog", "📊 JSON Data"])
            
            # TAB 1: The AI Strategy
            with tab1:
                st.subheader(f"Assessment Strategy for: {query}")
                
                ai_text = data.get("ai_response", "")
                
                if ai_text:
                    st.markdown(f'<div class="strategy-box">{ai_text}</div>', unsafe_allow_html=True)
                else:
                    st.warning("Strategy generation was empty. Please check backend logs.")

                st.caption("💡 Tip: Use the 'Deep Dive' setting in the sidebar for more comprehensive analysis.")

            # TAB 2: The Evidence (SHL Tests)
            with tab2:
                st.subheader(f"Relevant Assessments Found ({len(data.get('raw_results', []))})")
                
                results = data.get("raw_results", [])
                
                if results:
                    # Grid Layout for cards
                    for item in results:
                        # Determine badge type
                        t_type = item.get('test_type', [])
                        badges_html = ""
                        for t in t_type:
                            css_class = "badge-behav" if t in ['P', 'B', 'C'] else "badge-tech"
                            badges_html += f'<span class="badge {css_class}">{t}</span>'
                            
                        # Card HTML
                        st.markdown(f"""
                        <div class="assessment-card">
                            <div style="display:flex; justify-content:space-between; align-items:start;">
                                <div>
                                    <h4 style="margin:0 0 0.5rem 0; color:#1e293b;">{item.get('name', 'Unknown Test')}</h4>
                                    <div>{badges_html}</div>
                                </div>
                                <a href="{item.get('url', '#')}" target="_blank" 
                                   style="text-decoration:none; color:#0EA5E9; font-weight:bold; border:1px solid #0EA5E9; padding:0.4rem 0.8rem; border-radius:6px;">
                                   View ↗
                                </a>
                            </div>
                            <p style="color:#475569; margin-top:0.5rem; font-size:0.95rem;">
                                {item.get('description', 'No description provided.')}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No specific assessments found matching these criteria.")

            # TAB 3: Debug Data
            with tab3:
                st.json(data)

        else:
            my_bar.empty()
            st.error(f"Server Error: {response.status_code}")
            st.error(response.text)

    except requests.exceptions.ConnectionError:
        my_bar.empty()
        st.error("🔌 Connection Failed")
        st.markdown("Ensure your backend is running on `http://127.0.0.1:8000`")
    except Exception as e:
        my_bar.empty()
        st.error(f"An error occurred: {e}")
