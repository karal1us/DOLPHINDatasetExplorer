from typing import List
from models import Dataset

def filter_datasets(datasets: List[Dataset], domain: str = None, min_relevance: float = 0.0) -> List[Dataset]:
    filtered = datasets
    
    if domain:
        filtered = [d for d in filtered if d.domain.lower() == domain.lower()]
    
    filtered = [d for d in filtered if d.relevance_score >= min_relevance]
    
    return filtered

def sort_datasets(datasets: List[Dataset], sort_by: str = "relevance") -> List[Dataset]:
    if sort_by == "relevance":
        return sorted(datasets, key=lambda x: x.relevance_score, reverse=True)
    elif sort_by == "name":
        return sorted(datasets, key=lambda x: x.name.lower())
    elif sort_by == "domain":
        return sorted(datasets, key=lambda x: x.domain.lower())
    return datasets
