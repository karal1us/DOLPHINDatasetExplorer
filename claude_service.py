import os
from typing import List
import anthropic
from models import Dataset, SearchResult
from datetime import datetime
import json

CLAUDE_SEARCH_PROMPT = '''You are an expert dataset researcher. For the query "{query}", return datasets in this EXACT format:
[{{"name":"Example Dataset","description":"A clear description of the dataset","url":"https://example.com/data","domain":"Academic","use_cases":["Use case 1","Use case 2"]}}]

CRITICAL: 
- Response MUST start with [ and end with ]
- Use ONLY double quotes, no single quotes
- NO spaces, newlines, or formatting between JSON elements
- NO text before or after the JSON array
- NO explanations or comments
- 3-7 datasets only
- Valid domains: Academic, Government, Research, Commercial'''

class ClaudeService:
    def __init__(self):
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
        self.client = anthropic.Anthropic(api_key=api_key)

    def _parse_json_response(self, response_text: str) -> List[dict]:
        try:
            # Remove all whitespace and normalize quotes
            text = response_text.strip()
            text = ''.join(c for c in text if not c.isspace())
            text = text.replace("'", '"')
            
            # Ensure the text starts with [ and ends with ]
            if not (text.startswith('[') and text.endswith(']')):
                start = text.find('[')
                end = text.rfind(']')
                if start == -1 or end == -1:
                    raise ValueError("No valid JSON array found in response")
                text = text[start:end+1]
            
            # Add commas between objects if missing
            text = text.replace('}{', '},{')
            
            # Attempt to parse
            results = json.loads(text)
            
            if not isinstance(results, list):
                raise ValueError("Response is not a JSON array")
                
            return results
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse Claude response as JSON: {str(e)}")

    def validate_dataset_structure(self, dataset: dict) -> bool:
        """Validate that a dataset has all required fields with correct types"""
        required_fields = {
            'name': (str, "Dataset name must be a string"),
            'description': (str, "Description must be a string"),
            'url': (str, "URL must be a string"),
            'domain': (str, "Domain must be a string"),
            'use_cases': (list, "Use cases must be a list")
        }

        valid_domains = {'Academic', 'Government', 'Research', 'Commercial'}

        for field, (field_type, error_msg) in required_fields.items():
            if field not in dataset:
                raise ValueError(f"Missing required field: {field}")
            if not isinstance(dataset[field], field_type):
                raise ValueError(error_msg)

        # Additional validation
        if len(dataset['description']) < 50 or len(dataset['description']) > 200:
            raise ValueError("Description must be between 50 and 200 characters")
            
        if dataset['domain'] not in valid_domains:
            raise ValueError(f"Invalid domain: {dataset['domain']}. Must be one of: {', '.join(valid_domains)}")
            
        if not isinstance(dataset['use_cases'], list) or not (2 <= len(dataset['use_cases']) <= 5):
            raise ValueError("Use cases must be a list containing 2-5 items")
            
        if not all(isinstance(uc, str) for uc in dataset['use_cases']):
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

            # Parse JSON response
            try:
                results = self._parse_json_response(response_text)
            except ValueError as e:
                raise ValueError(f"Failed to parse Claude response: {str(e)}")

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
                except ValueError as e:
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
