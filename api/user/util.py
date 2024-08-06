import requests
from fastapi import FastAPI, HTTPException
import os
from dotenv import load_dotenv


load_dotenv()


class UserUtil:

    @staticmethod
    def verify_token(provider: str, access_token: str):
        """
        1차 토큰 분류
        naver를 없애면서 사용안함
        """
        if provider == "naver":
            res = UserUtil.verify_naver_token(access_token)
            if res:
                return res
            else:
                return False
        else:
            res = UserUtil.verify_google_token(access_token)
            if res:
                return res
            else:
                return False

    @staticmethod
    def verify_naver_token(access_token: str):
        """
        naver 검증
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
        }
        response = requests.get(os.getenv("NAVER_USER_INFO_URL"), headers=headers)

        if response.status_code != 200:
            return False
        data = response.json()
        return data["response"]["email"]

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
    def user_quest_query():
        """
        사용자 퀘스트 조회 쿼리
        """

        return """
                select tkl_npc.id                                             as npc_id,
                       tkl_npc.name_kr                                        as npc_name_kr,
                       tkl_npc.name_en                                        as npc_name_en,
                       tkl_npc.image                                          as npc_image,
                       jsonb_agg(jsonb_build_object('quest_id', rq, 'quest_name_en', tkl_quest.name_en, 'quest_name_kr',
                                                    tkl_quest.name_kr, 'objectives_kr', tkl_quest.objectives_kr, 'objectives_en',
                                                    tkl_quest.objectives_en, 'next', COALESCE(tkl_quest.next, jsonb '[]'::jsonb))) as quest_info
                from tkl_user_quest
                         left join lateral unnest(tkl_user_quest.quest_id) AS rq ON true
                         left join tkl_quest on rq = tkl_quest.id
                         left join tkl_npc on tkl_quest.npc_value = tkl_npc.id
                WHERE tkl_user_quest.user_email = :user_email
                group by tkl_npc.id, tkl_npc.name_kr, tkl_npc.name_en
                order by tkl_npc.id
                """

    @staticmethod
    def get_user_posts():
        """
        사용자 작성글 조회
        """

        return """
                select *
                from tkl_board_pvp
                where writer = :email
                union all
                select *
                from tkl_board_pve
                where writer = :email
                union all
                select *
                from tkl_board_tip
                where writer = :email
                union all
                select *
                from tkl_board_arena
                where writer = :email
                union all
                select *
                from tkl_board_forum
                where writer = :email
                union all
                select *
                from tkl_board_question
                where writer = :email
                ORDER BY create_time DESC
                LIMIT 10 OFFSET 1
                """
