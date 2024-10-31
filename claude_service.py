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

Return ONLY a JSON array in the following exact format, with no additional text:
[
  {{
    "name": "Dataset Name",
    "description": "Short description of the dataset",
    "url": "Direct download/access link",
    "domain": "Source domain (e.g., Academic, Government, Research)",
    "use_cases": ["use case 1", "use case 2"]
  }}
]

Ensure the response is a valid JSON array and each dataset entry contains all required fields.
"""

class ClaudeService:
    def __init__(self):
        # Initialize the Anthropic client with the API key from environment variables
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
        self.client = anthropic.Anthropic(api_key=api_key)

    def validate_dataset_structure(self, dataset: dict) -> bool:
        """Validate that a dataset has all required fields with correct types"""
        required_fields = {
            'name': str,
            'description': str,
            'url': str,
            'domain': str,
            'use_cases': list
        }
        
        for field, field_type in required_fields.items():
            if field not in dataset:
                raise ValueError(f"Missing required field: {field}")
            if not isinstance(dataset[field], field_type):
                raise ValueError(f"Invalid type for field {field}: expected {field_type.__name__}")
            if field == 'use_cases' and not all(isinstance(uc, str) for uc in dataset[field]):
                raise ValueError("All use cases must be strings")
        return True

    def search_datasets(self, query: str) -> SearchResult:
        try:
            # Make API request to Claude
            response = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4096,
                temperature=0.0,
                messages=[{
                    "role": "user",
                    "content": CLAUDE_SEARCH_PROMPT.format(query=query)
                }]
            )
            
            # Get response content
            response_text = response.content[0].text.strip()
            
            # Try to parse JSON response
            try:
                results = json.loads(response_text)
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse Claude response as JSON: {str(e)}")
            
            # Validate response is a list
            if not isinstance(results, list):
                raise ValueError("Claude response is not a JSON array")
            
            datasets = []
            for idx, item in enumerate(results):
                try:
                    # Validate each dataset structure
                    self.validate_dataset_structure(item)
                    
                    dataset = Dataset(
                        name=item['name'],
                        description=item['description'],
                        url=item['url'],
                        domain=item['domain'],
                        use_cases=item['use_cases'],
                        relevance_score=1.0 - (idx * 0.1),  # Decrease relevance for later results
                        timestamp=datetime.now()
                    )
                    datasets.append(dataset)
                except (KeyError, ValueError) as e:
                    print(f"Skipping invalid dataset: {str(e)}")
                    continue
            
            if not datasets:
                raise ValueError("No valid datasets found in the response")
            
            return SearchResult(
                query=query,
                datasets=datasets,
                total_count=len(datasets)
            )
            
        except Exception as e:
            raise Exception(f"Error searching datasets: {str(e)}")
