from typing import Dict, Any
from backend.repositories.requests_search_repository import RequestsSearchRepository

class RequestsSearchService:
    def __init__(self, repository: RequestsSearchRepository):
        self.repository = repository

    def search_requests(self, filters: Dict[str, Any]):
        # directly use repository
        return self.repository.search_requests(filters)
