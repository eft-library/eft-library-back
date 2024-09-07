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
                select tkl_board_union.id,
                       tkl_board_union.title,
                       tkl_board_union.contents,
                       tkl_board_union.thumbnail,
                       tkl_board_union.writer,
                       tkl_board_union.like_count,
                       tkl_board_union.view_count,
                       tkl_board_union.type,
                       tkl_board_union.create_time,
                       tkl_board_union.update_time,
                       count(tkl_comments.id) as comment_cnt,
                       tkl_board_type.name_kr as type_kr
                from tkl_board_union
                         left join tkl_comments on tkl_board_union.id = tkl_comments.board_id
                         left join tkl_board_type on tkl_board_union.type = tkl_board_type.value
                where writer = :email
                group by tkl_board_union.id, tkl_board_type.name_kr, tkl_board_union.title, tkl_board_union.contents,
                         tkl_board_union.thumbnail, tkl_board_union.writer, tkl_board_union.like_count, tkl_board_union.view_count,
                         tkl_board_union.type, tkl_board_union.create_time, tkl_board_union.update_time
                ORDER BY tkl_board_union.create_time DESC
                LIMIT 5
                """

    @staticmethod
    def get_user_post_detail_max_count():
        return """
            select count(*)
            from tkl_board_union
            where writer = :user_email
        """

    @staticmethod
    def get_user_post_detail():
        return """
            select tkl_board_union.id,
                   tkl_board_union.title,
                   tkl_board_union.contents,
                   tkl_board_union.thumbnail,
                   tkl_board_union.writer,
                   tkl_board_union.like_count,
                   tkl_board_union.view_count,
                   tkl_board_union.type,
                   tkl_board_union.create_time,
                   tkl_board_union.update_time,
                   tkl_user.nick_name,
                   tkl_user.icon,
                   count(tkl_comments.board_id) as comment_cnt,
                   tkl_board_type.name_kr       as type_kr
            from tkl_board_union
                     left join tkl_user on tkl_board_union.writer = tkl_user.email
                     left join tkl_comments on tkl_board_union.id = tkl_comments.board_id
                     left join tkl_board_type on tkl_board_union.type = tkl_board_type.value
            where writer = :user_email
            group by tkl_user.icon, tkl_user.nick_name, tkl_board_union.title, tkl_board_union.contents,
                     tkl_board_union.thumbnail, tkl_board_union.writer, tkl_board_union.like_count,
                     tkl_board_union.view_count, tkl_board_union.type, tkl_board_union.create_time,
                     tkl_board_union.update_time, tkl_board_union.id, tkl_user.icon, tkl_board_type.name_kr
            ORDER BY tkl_board_union.create_time DESC
            LIMIT :limit OFFSET :offset
        """

    @staticmethod
    def get_user_comment_detail_max_count():
        return """
        SELECT COUNT(*)
        FROM (
            SELECT tkl_comments.id,
                   tkl_board_union.id AS post_id
            FROM tkl_comments
            LEFT JOIN tkl_board_union
            ON tkl_comments.board_id = tkl_board_union.id
               AND tkl_comments.board_type = tkl_board_union.type
            WHERE tkl_comments.user_email = :user_email
              AND tkl_comments.is_delete_by_admin = false
              AND tkl_comments.is_delete_by_user = false
        ) AS a
        WHERE a.post_id IS NOT NULL;
        """

    @staticmethod
    def get_user_comment_detail():
        return """
        select * from (
        select tkl_comments.id,
               tkl_comments.board_id,
               tkl_comments.user_email,
               tkl_comments.board_type,
               tkl_comments.parent_id,
               tkl_comments.contents,
               tkl_comments.depth,
               tkl_comments.create_time,
               tkl_comments.update_time,
               tkl_comments.is_delete_by_admin,
               tkl_comments.is_delete_by_user,
               tkl_comments.like_count,
               tkl_comments.dislike_count,
               tkl_comments.parent_user_email,
               tkl_board_union.title,
               tua.nick_name as parent_nick_name,
               tub.icon,
               tub.nick_name
        from tkl_comments
        left join tkl_board_union on tkl_comments.board_id = tkl_board_union.id
        left join tkl_user tua on tkl_comments.parent_user_email = tua.email
        left join tkl_user tub on tkl_comments.user_email = tub.email
        where tkl_comments.user_email = :user_email and tkl_comments.is_delete_by_admin = false and tkl_comments.is_delete_by_user = false 
        order by tkl_comments.create_time desc) as a
        where a.title is not null
        limit 5
        """

    @staticmethod
    def get_user_info():
        return """
        select
               tkl_user.icon,
               tkl_user.nick_name,
               tkl_user_grade.value,
               tkl_user_post_statistics.post_count,
               tkl_user_post_statistics.comment_count,
               tkl_user_ban.ban_reason,
               tkl_user_ban.ban_end_time,
               tkl_user.attendance_count
        from tkl_user
        left join tkl_user_post_statistics on tkl_user.email = tkl_user_post_statistics.user_email
        left join tkl_user_grade on tkl_user.grade = tkl_user_grade.id
        left join tkl_user_ban on tkl_user.email = tkl_user_ban.user_email
        where email = :user_email
        """
