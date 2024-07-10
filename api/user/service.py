from api.user.models import User, Token, AddUserReq
from database import DataBaseConnector
from jose.jwe import decrypt, encrypt
from dotenv import load_dotenv
import os

load_dotenv()


class UserService:
    @staticmethod
    def add_new_user(addUserReq: AddUserReq):
        try:
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                check_user = (
                    s.query(User)
                    .filter(User.id == addUserReq.id or User.email == addUserReq.email)
                    .first()
                )
                print(check_user.id)
                if check_user:
                    return True
                else:
                    new_user = User(
                        id=addUserReq.id,
                        name=addUserReq.name,
                        email=addUserReq.email,
                        image=addUserReq.image,
                    )
                    s.add(new_user)
                    s.commit()
            return True
        except Exception as e:
            print("오류 발생:", e)
            return None
