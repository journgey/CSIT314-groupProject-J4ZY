from typing import Dict, Any, Optional, List
from schemas.categories import Category 

class CategoriesService:
    """Business logic for categories."""

    def __init__(self, repository):
        self.repository = repository

    def create_category(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate payload and create a category, returning the created row."""
        # Validate with schema (id should be omitted on create)
        cat = Category(**data)

        # Persist via repository
        created = self.repository.create_category(
            name=cat.name,
            description=cat.description,
        )

        # Read back to ensure consistent shape (if repository returns only partial)
        fresh = self.repository.get_category_by_id(created["id"])
        return fresh or created

    def get_category_by_id(self, category_id: int) -> Optional[Dict[str, Any]]:
        """Return a single category or None."""
        return self.repository.get_category_by_id(category_id)

    def list_categories(self) -> List[Dict[str, Any]]:
        """Return all categories."""
        return self.repository.list_categories()

    def update_category(self, category_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Apply updates after schema re-validation on a merged view."""
        current = self.repository.get_category_by_id(category_id)
        if not current:
            return None

        # Merge and validate (keeps invariants: name not empty, etc.)
        merged = {**current, **(data or {})}
        Category(**merged)  # validation only

        # Persist updates
        self.repository.update_category(category_id, **(data or {}))

        # Read back and return the latest state
        return self.repository.get_category_by_id(category_id)

    def delete_category(self, category_id: int) -> bool:
        """Delete the category; return True if deleted, False if missing."""
        try:
            self.repository.delete_category(category_id)
            return True
        except ValueError:
            # Repository raises ValueError when row not found
            return False
