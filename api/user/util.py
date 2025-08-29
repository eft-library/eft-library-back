import requests
import os
from dotenv import load_dotenv


load_dotenv()


class UserUtil:
    @staticmethod
    def verify_google_token(access_token: str):
        """
        구글 검증
        """
        response = requests.get(
            f"{os.getenv('GOOGLE_TOKEN_INFO_URL')}?access_token={access_token}"
        )

        if response.status_code != 200:
            return False
        data = response.json()
        return data["email"]

    @staticmethod
    def get_user_info_with_penalty():
        return """
            SELECT ui.email,
                   ui.is_admin,
                   ui.attendance_count,
                   ui.nickname,
                   ui.last_update_nickname,
                   up.start_time,
                   up.end_time,
                   COALESCE(jsonb_agg(
                            jsonb_build_object(
                                    'blocker_email', ub.blocker_email,
                                    'blocked_email', ub.blocked_email,
                                    'reason', ub.reason,
                                    'create_time', ub.create_time
                            )
                                     ) FILTER (WHERE ub.blocker_email IS NOT NULL), '[]'::jsonb) AS user_blocks
            FROM user_info ui
                     LEFT JOIN LATERAL (
                SELECT start_time, end_time
                FROM user_penalty
                WHERE user_email = ui.email
                ORDER BY start_time DESC
                LIMIT 1
                ) up ON TRUE
                     LEFT JOIN user_block ub
                               ON ui.email = ub.blocker_email
            WHERE ui.email = :user_email
            GROUP BY ui.email, ui.is_admin, ui.attendance_count, ui.nickname, ui.last_update_nickname,
                     up.start_time, up.end_time
            LIMIT 1  
        """
