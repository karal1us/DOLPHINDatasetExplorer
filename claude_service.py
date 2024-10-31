import os
from typing import List
import anthropic
from models import Dataset, SearchResult
from datetime import datetime
import json

CLAUDE_SEARCH_PROMPT = """
You are an expert dataset researcher. For the query "{query}":

1. Generate a comprehensive list of high-quality, relevant datasets
2. Prioritize datasets based on:
   - Relevance to search query
   - Data recency
   - Credibility of source
   - Accessibility

Guidelines for dataset selection:
- Prefer open-source and publicly available datasets
- Include diverse sources (academic, government, research institutions)
- Provide direct, working download links
- Avoid paywalled or restricted access resources

For each dataset, provide:
- Dataset Name
- Short Description
- Direct Download/Access Link
- Source Domain
- Potential Use Cases

Return results as a structured JSON array with these fields.
"""

class ClaudeService:
    def __init__(self):
        # Initialize the Anthropic client with the API key from environment variables
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
        self.client = anthropic.Anthropic(api_key=api_key)

    def search_datasets(self, query: str) -> SearchResult:
        try:
            response = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4096,
                temperature=0.0,
                messages=[{
                    "role": "user",
                    "content": CLAUDE_SEARCH_PROMPT.format(query=query)
                }]
            )
            
            # Parse the JSON response
            results = json.loads(response.content[0].text)
            datasets = []
            
            for item in results:
                dataset = Dataset(
                    name=item['name'],
                    description=item['description'],
                    url=item['url'],
                    domain=item['domain'],
                    use_cases=item['use_cases'],
                    relevance_score=1.0,
                    timestamp=datetime.now()
                )
                datasets.append(dataset)
            
            return SearchResult(
                query=query,
                datasets=datasets,
                total_count=len(datasets)
            )
            
        except Exception as e:
            raise Exception(f"Error searching datasets: {str(e)}")
