from domain.models import UserInDB, UserRole
from typing import List, Optional

class UserRepository:
    def get_user_by_email(self, email: str) -> UserInDB | None:
        raise NotImplementedError

    def get_user_by_id(self, user_id: int) -> UserInDB | None:
        raise NotImplementedError

    def create_user(self, user: UserInDB) -> UserInDB:
        raise NotImplementedError

    def get_all_users(self) -> List[UserInDB]:
        raise NotImplementedError

    def update_user_role(self, user_id: int, role: UserRole) -> UserInDB | None:
        raise NotImplementedError
