import json

# Sample User API Functions

def get_user(user_id: int):
    """Retrieves user details by ID."""
    # In a real app, fetch from database
    print(f"Fetching user {user_id}")
    return {"id": user_id, "name": f"User {user_id}"}

def list_users():
    """Lists all users."""
    # In a real app, fetch from database
    print("Listing all users")
    return [{"id": 1, "name": "User 1"}, {"id": 2, "name": "User 2"}]

class UserProfile:
    """Represents a user profile."""
    def __init__(self, user_id):
        self.user_id = user_id
        self.data = get_user(user_id) # Example usage

    def get_profile_data(self):
        return self.data

def create_user(name: str):
    """Creates a new user."""
    print(f"Creating user: {name}")
    return {"name": name, "id": 3}

def delete_user(user_id: int):
    """Deletes a user."""
    print(f"Deleting user: {user_id}")
    return {"status": "deleted"}

def update_user(user_id: int, name: str):
    """Updates a user's name."""
    print(f"Updating user {user_id} to {name}")
    return {"id": user_id, "name": name}
