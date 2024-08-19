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
                LIMIT 5 OFFSET 1
                """

    @staticmethod
    def get_user_post_detail():
        return """
        select post.id,
               post.title,
               post.contents,
               post.thumbnail,
               post.writer,
               post.like_count,
               post.view_count,
               post.type,
               post.create_time,
               post.update_time
        from (select tkl_board_pvp.id,
                     tkl_board_pvp.title,
                     tkl_board_pvp.contents,
                     tkl_board_pvp.thumbnail,
                     tkl_board_pvp.writer,
                     tkl_board_pvp.like_count,
                     tkl_board_pvp.view_count,
                     tkl_board_pvp.type,
                     tkl_board_pvp.create_time,
                     tkl_board_pvp.update_time
              from tkl_board_pvp
              where writer = :user_email
              union all
              select id,
                     title,
                     contents,
                     thumbnail,
                     writer,
                     like_count,
                     view_count,
                     type,
                     create_time,
                     update_time
              from tkl_board_pve
              where writer = :user_email
              union all
              select tkl_board_tip.id,
                     tkl_board_tip.title,
                     tkl_board_tip.contents,
                     tkl_board_tip.thumbnail,
                     tkl_board_tip.writer,
                     tkl_board_tip.like_count,
                     tkl_board_tip.view_count,
                     tkl_board_tip.type,
                     tkl_board_tip.create_time,
                     tkl_board_tip.update_time
              from tkl_board_tip
              where writer = :user_email
              union all
              select tkl_board_arena.id,
                     tkl_board_arena.title,
                     tkl_board_arena.contents,
                     tkl_board_arena.thumbnail,
                     tkl_board_arena.writer,
                     tkl_board_arena.like_count,
                     tkl_board_arena.view_count,
                     tkl_board_arena.type,
                     tkl_board_arena.create_time,
                     tkl_board_arena.update_time
              from tkl_board_arena
              where writer = :user_email
              union all
              select tkl_board_forum.id,
                     tkl_board_forum.title,
                     tkl_board_forum.contents,
                     tkl_board_forum.thumbnail,
                     tkl_board_forum.writer,
                     tkl_board_forum.like_count,
                     tkl_board_forum.view_count,
                     tkl_board_forum.type,
                     tkl_board_forum.create_time,
                     tkl_board_forum.update_time
              from tkl_board_forum
              where writer = :user_email
              union all
              select tkl_board_question.id,
                     tkl_board_question.title,
                     tkl_board_question.contents,
                     tkl_board_question.thumbnail,
                     tkl_board_question.writer,
                     tkl_board_question.like_count,
                     tkl_board_question.view_count,
                     tkl_board_question.type,
                     tkl_board_question.create_time,
                     tkl_board_question.update_time
              from tkl_board_question
              where writer = :user_email) as post
        ORDER BY post.create_time DESC
        """

    @staticmethod
    def get_user_comment_detail():
        return """
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
               tkl_comments.parent_user_email
        from tkl_comments
        where tkl_comments.user_email = :user_email
        order by tkl_comments.create_time desc
        """

    @staticmethod
    def get_user_info():
        return """
        select
               tkl_user.icon,
               tkl_user.nick_name,
               tkl_user_grade.value,
               tkl_user_post_statistics.post_count,
               tkl_user_post_statistics.comment_count
        from tkl_user
        left join tkl_user_post_statistics on tkl_user.email = tkl_user_post_statistics.user_email
        left join tkl_user_grade on tkl_user.grade = tkl_user_grade.id
        where email = :user_email
        """
