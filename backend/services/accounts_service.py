class AccountService:
    def __init__(self, repository):
        """Initialize with a repository/data-access object."""
        pass

    # Create
    def create_account(self, username, password, email, role):
        pass

    # Read (single)
    def get_account_by_id(self, account_id):
        pass

    def get_account_by_username(self, username):
        pass

    # Read (collection)
    def list_accounts(self, filters=None, page: int | None = None, page_size: int | None = None):
        pass

    # Update
    def update_account(self, account_id, **updates):
        pass

    # Delete
    def delete_account(self, account_id):
        pass
