from dataclasses import dataclass, asdict
from typing import List, Optional
from datetime import datetime
import json

@dataclass
class Dataset:
    name: str
    description: str
    url: str
    domain: str
    use_cases: List[str]
    relevance_score: float
    timestamp: datetime

    def to_json(self) -> dict:
        data = asdict(self)
        # Convert datetime to ISO format string for JSON serialization
        data['timestamp'] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_json(cls, json_data: dict) -> 'Dataset':
        # Convert ISO format string back to datetime
        json_data['timestamp'] = datetime.fromisoformat(json_data['timestamp'])
        return cls(**json_data)

@dataclass
class SearchResult:
    query: str
    datasets: List[Dataset]
    total_count: int

    def to_json(self) -> dict:
        return {
            'query': self.query,
            'datasets': [dataset.to_json() for dataset in self.datasets],
            'total_count': self.total_count
        }

    @classmethod
    def from_json(cls, json_data: dict) -> 'SearchResult':
        datasets = [Dataset.from_json(d) for d in json_data['datasets']]
        return cls(
            query=json_data['query'],
            datasets=datasets,
            total_count=json_data['total_count']
        )
