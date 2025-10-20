class RequestService:
    def __init__(self, repository):
        """Initialize with a repository/data-access object."""
        pass


    # Create
    def create_request(self, pin_id, title, description, category_id, start_date=None, end_date=None):
        pass


    # Read (single)
    def get_request_by_id(self, request_id):
        pass


    # Read (collection)
    def list_requests(self, filters=None, page: int | None = None, page_size: int | None = None):
        pass


    # Update
    def update_request(self, request_id, **updates):
        pass


    # Delete
    def delete_request(self, request_id):
        pass