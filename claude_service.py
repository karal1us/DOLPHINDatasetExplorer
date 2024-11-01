import os
from typing import List
import anthropic
from models import Dataset, SearchResult
from datetime import datetime
import json

CLAUDE_SEARCH_PROMPT = '''You are an expert dataset researcher. Search for relevant datasets matching this query: "{query}"

Return ONLY a JSON array containing 3-7 datasets. Format each dataset exactly like this, with no extra whitespace or newlines:
[{"name":"Dataset Name","description":"Clear description","url":"https://direct.link/to/dataset","domain":"Academic|Government|Research|Commercial","use_cases":["Use case 1","Use case 2"]}]

Critical formatting rules:
- Start response with [ and end with ]
- No text before or after the JSON array
- No comments or explanations
- No newlines or extra spaces between fields
- Use double quotes for all strings
- Valid domains are: Academic, Government, Research, Commercial'''

class ClaudeService:
    def __init__(self):
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
        self.client = anthropic.Anthropic(api_key=api_key)

    def _parse_json_response(self, response_text: str) -> List[dict]:
        try:
            # Aggressively clean the response text
            cleaned_text = response_text.strip()
            cleaned_text = ''.join(cleaned_text.split())  # Remove ALL whitespace
            
            # Find the JSON array bounds
            json_start = cleaned_text.find('[')
            json_end = cleaned_text.rfind(']') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("Response does not contain a JSON array")
            
            # Extract just the JSON array
            json_content = cleaned_text[json_start:json_end]
            
            # Add some formatting back for valid JSON
            formatted_json = json_content.replace('}{', '},{')
            
            # Parse the JSON
            results = json.loads(formatted_json)
            
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
