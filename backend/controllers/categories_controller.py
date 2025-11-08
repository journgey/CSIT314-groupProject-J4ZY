from typing import Dict, Any, Optional, List
from backend.schemas.categories import Category 

class CategoriesController:
    def __init__(self, repository):
        self.repository = repository

    @staticmethod
    def _require_pm(role: Optional[str]):
        if role != "PlatformManager":
            raise PermissionError("PlatformManager role required")

    def create_category(self, data: Dict[str, Any], *, acting_role: Optional[str] = None) -> Dict[str, Any]:
        self._require_pm(acting_role)
        cat = Category(**(data or {}))

        created = self.repository.create_category(
            name=cat.name,
            description=cat.description,
        )

        fresh = self.repository.get_category_by_id(created["id"])
        return fresh or created

    def get_category_by_id(self, category_id: int, *, acting_role: Optional[str] = None) -> Optional[Dict[str, Any]]:
        self._require_pm(acting_role)
        return self.repository.get_category_by_id(category_id)

    def list_categories(self) -> List[Dict[str, Any]]:
        return self.repository.list_categories()

    def update_category(self, category_id: int, data: Dict[str, Any], *, acting_role: Optional[str] = None) -> Optional[Dict[str, Any]]:
        self._require_pm(acting_role)
        current = self.repository.get_category_by_id(category_id)
        if not current:
            return None
        merged = {**current, **(data or {})}
        Category(**merged)  
        self.repository.update_category(category_id, **(data or {}))
        return self.repository.get_category_by_id(category_id)

    def delete_category(self, category_id: int, *, acting_role: Optional[str] = None) -> bool:
        self._require_pm(acting_role)
        try:
            self.repository.delete_category(category_id)
            return True
        except ValueError:
            return False