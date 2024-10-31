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
    page_title="Dataset Search",
    page_icon="🔍",
    layout="wide"
)

# Title and description
st.title("📊 AI-Powered Dataset Search")
st.markdown("""
    Find the perfect dataset for your project using our advanced AI-powered search.
    Simply enter your search query and let our system find relevant datasets from across the internet.
""")

# Search interface
search_query = st.text_input("🔍 Enter your dataset search query", 
                            placeholder="e.g., climate change temperature data")

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
            
            # Display results
            st.subheader(f"📑 Found {len(sorted_datasets)} datasets")
            
            for dataset in sorted_datasets:
                with st.expander(f"{dataset.name} ({dataset.domain})"):
                    st.markdown(f"**Description:** {dataset.description}")
                    st.markdown(f"**Source:** [{dataset.url}]({dataset.url})")
                    st.markdown("**Use Cases:**")
                    for use_case in dataset.use_cases:
                        st.markdown(f"- {use_case}")
                    
                    st.progress(dataset.relevance_score, 
                              text=f"Relevance Score: {dataset.relevance_score:.2f}")
            
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            
# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center'>
        Powered by Claude AI | Made with ❤️ using Streamlit
    </div>
""", unsafe_allow_html=True)
