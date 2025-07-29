from domain.models import UserInDB

class UserRepository:
    def get_user_by_email(self, email: str) -> UserInDB | None:
        raise NotImplementedError

    def create_user(self, user: UserInDB) -> None:
        raise NotImplementedError
