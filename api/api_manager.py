from api.auth_api import AuthAPI
from api.genres_api import GenresAPI
from api.movies_api import MoviesAPI
from api.user_api import UserAPI


class ApiManager:

    def __init__(self, session):
        self.session = session
        self.auth_api = AuthAPI(session)
        self.genres_api = GenresAPI(session)
        self.movies_api = MoviesAPI(session)
        self.user_api = UserAPI(session)
