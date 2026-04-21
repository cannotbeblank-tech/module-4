from __future__ import annotations

from sqlalchemy.orm import Session

from db.db_models import GenreDBModel, MovieDBModel, UserDBModel


class DBHelper:
    def __init__(self, db_session: Session) -> None:
        self.db_session = db_session

    def get_user_by_email(self, email: str) -> UserDBModel | None:
        return self.db_session.query(UserDBModel).filter(UserDBModel.email == email).first()

    def set_user_roles(self, email: str, roles: list[str]) -> UserDBModel | None:
        user = self.get_user_by_email(email)
        if user is None:
            return None
        user.roles = roles
        self.db_session.commit()
        self.db_session.refresh(user)
        return user

    def delete_user(self, user: UserDBModel) -> None:
        self.db_session.delete(user)
        self.db_session.commit()

    def get_movie_by_id(self, movie_id: int) -> MovieDBModel | None:
        return self.db_session.query(MovieDBModel).filter(MovieDBModel.id == movie_id).first()

    def get_movies_by_name(self, name: str) -> list[MovieDBModel]:
        return self.db_session.query(MovieDBModel).filter(MovieDBModel.name == name).all()

    def get_all_genres(self) -> list[GenreDBModel]:
        return self.db_session.query(GenreDBModel).all()
