from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class Dataset:
    name: str
    description: str
    url: str
    domain: str
    use_cases: List[str]
    relevance_score: float
    timestamp: datetime

@dataclass
class SearchResult:
    query: str
    datasets: List[Dataset]
    total_count: int
