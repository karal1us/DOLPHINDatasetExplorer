import streamlit as st
import pandas as pd
from database import DatabaseManager
from claude_service import ClaudeService
from utils import filter_datasets, sort_datasets

# Initialize services
db = DatabaseManager()
claude = ClaudeService()

# Page config
st.set_page_config(
    page_title="Dolphin | AI-Powered Data Search",
    page_icon="🐬",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'About': "Dolphin - AI-Powered Dataset Search Engine"
    }
)

# Custom CSS for better styling
st.markdown("""
    <style>
        .block-container {
            max-width: 1000px;
            padding-top: 2rem;
            padding-bottom: 6rem;  /* Increased padding to accommodate footer */
        }
        .main-title {
            text-align: center;
            color: #4FB3E8;
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 1rem;
        }
        .description {
            text-align: center;
            margin-bottom: 3rem;
            color: #FAFAFA;
            font-size: 1.2rem;
        }
        .search-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 1rem;
        }
        .stExpander {
            background-color: #262730;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        .footer {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            text-align: center;
            padding: 1rem;
            background-color: rgba(14, 17, 23, 0.95);  /* Slightly transparent background */
            border-top: 1px solid #262730;
            z-index: 1000;  /* Ensure footer stays on top */
            backdrop-filter: blur(5px);  /* Add blur effect for better visibility */
        }
        .footer a {
            color: #4FB3E8;
            text-decoration: none;
            transition: color 0.3s ease;
            font-weight: 500;  /* Make the link more visible */
            padding: 0.25rem 0.5rem;  /* Add padding for better touch targets */
            border-radius: 4px;
        }
        .footer a:hover {
            color: #2D8BC7;
            background-color: rgba(79, 179, 232, 0.1);  /* Subtle hover effect */
        }
        /* Add margin to last expander to prevent footer overlap */
        .stExpander:last-child {
            margin-bottom: 4rem;
        }
    </style>
""", unsafe_allow_html=True)

# Title and description
st.markdown('<h1 class="main-title">🐬 Dolphin | AI-Powered Data Search</h1>', unsafe_allow_html=True)
st.markdown("""
    <div class="description">
        Find the perfect dataset for your project using our advanced AI-powered search.
        Simply enter your search query and let our system find relevant datasets from across the internet.
    </div>
""", unsafe_allow_html=True)

# Search interface
with st.container():
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    search_query = st.text_input("🔍 Enter your dataset search query", 
                                placeholder="e.g., climate change temperature data")
    st.markdown('</div>', unsafe_allow_html=True)

# Search button and loading state
if search_query:
    with st.spinner("🔄 Searching for datasets..."):
        try:
            # Check cache first
            results = db.get_cached_results(search_query)
            
            if not results:
                # Perform new search with Claude
                results = claude.search_datasets(search_query)
                # Cache the results
                db.cache_results(search_query, results)
            
            # Filters section with better spacing
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Display filters and sorting options
            col1, col2 = st.columns(2)
            
            with col1:
                domains = list(set(d.domain for d in results.datasets))
                selected_domain = st.selectbox(
                    "Filter by Domain",
                    ["All"] + domains
                )
                
            with col2:
                sort_option = st.selectbox(
                    "Sort by",
                    ["Relevance", "Name", "Domain"]
                )
            
            # Apply filters and sorting
            filtered_datasets = filter_datasets(
                results.datasets,
                domain=selected_domain if selected_domain != "All" else None
            )
            
            sorted_datasets = sort_datasets(
                filtered_datasets,
                sort_by=sort_option.lower()
            )
            
            # Display results with improved spacing
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader(f"📑 Found {len(sorted_datasets)} datasets")
            
            for dataset in sorted_datasets:
                with st.expander(f"{dataset.name} ({dataset.domain})"):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.markdown(f"**Description:** {dataset.description}")
                        st.markdown(f"**Source:** [{dataset.url}]({dataset.url})")
                    with col2:
                        st.markdown("**Use Cases:**")
                        for use_case in dataset.use_cases:
                            st.markdown(f"- {use_case}")
                        st.progress(dataset.relevance_score, 
                                text=f"Relevance Score: {dataset.relevance_score:.2f}")
            
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

# Add footer with Twitter attribution
st.markdown("""
    <div class="footer">
        Made with 💙 by <a href="https://twitter.com/GalvosasJ" target="_blank">@GalvosasJ</a>
    </div>
""", unsafe_allow_html=True)
