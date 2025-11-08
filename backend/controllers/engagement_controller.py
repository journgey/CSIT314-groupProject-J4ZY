from typing import List, Dict, Any

class EngagementsController:
    def __init__(self, repository):
        self.repository = repository

    def list_pin_engagement(self, pin_id: int) -> List[Dict[str, Any]]:
        if not isinstance(pin_id, int) or pin_id <= 0:
            raise ValueError("Invalid pin_id")
        return self.repository.list_by_pin_current(pin_id)
