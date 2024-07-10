from api.user.models import User, Token, AddUserReq
from database import DataBaseConnector
from jose.jwe import decrypt, encrypt
from dotenv import load_dotenv
import os
import uuid


load_dotenv()


class UserService:
    @staticmethod
    def add_new_user(addUserReq: AddUserReq):
        try:
            uuid_v5 = f"{os.getenv('UUID_NAME')}-{uuid.uuid5(uuid.NAMESPACE_DNS, addUserReq.email)}"
            session = DataBaseConnector.create_session_factory()
            with session() as s:
                # 이미 존재하는 사용자인지 확인
                check_user = (
                    s.query(User).filter(User.email == addUserReq.email).first()
                )

                if check_user:
                    return True
                else:
                    new_user = User(
                        id=addUserReq.id,
                        name=addUserReq.name,
                        email=addUserReq.email,
                        image=addUserReq.image,
                        nick_name=uuid_v5,
                    )
                    s.add(new_user)
                    s.commit()
                    return True
        except Exception as e:
            print("오류 발생:", e)
            return None
