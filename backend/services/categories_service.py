class CategoryService:
    def __init__(self, repository):
        """Initialize with a repository/data-access object."""
        pass


    # Create
    def create_category(self, name, parent_id=None, description=None):
        pass


    # Read (single)
    def get_category_by_id(self, category_id):
        pass


    def get_category_by_name(self, name):
        pass


    # Read (collection)
    def list_categories(self, parent_id=None, page: int | None = None, page_size: int | None = None):
        pass


    # Update
    def update_category(self, category_id, **updates):
        pass


    # Delete
    def delete_category(self, category_id):
        pass