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
                   ui.create_time,
                   ui.last_update_nickname,
                   up.start_time,
                   up.end_time,
                   up.reason,
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
                SELECT start_time, end_time, reason
                FROM user_penalty
                WHERE user_email = ui.email
                ORDER BY start_time DESC
                LIMIT 1
                ) up ON TRUE
                     LEFT JOIN user_block ub
                               ON ui.email = ub.blocker_email
            WHERE ui.email = :user_email
            GROUP BY ui.email, ui.is_admin, ui.attendance_count, ui.nickname, ui.create_time, ui.last_update_nickname,
                     up.start_time, up.end_time, up.reason, ub.create_time
            order by ub.create_time desc
            LIMIT 1
        """

    @staticmethod
    def get_my_page_default():
        return """
            SELECT ui.email,
                   COALESCE(c.comment_count, 0) AS comment_count,
                   COALESCE(p.post_count, 0) AS post_count,
                   COALESCE(f.follow_count, 0) AS follow_count,
                   COALESCE(n.notification_count, 0) AS notification_count
            FROM user_info ui
                     LEFT JOIN (
                SELECT user_email, COUNT(*) AS comment_count
                FROM community_comments
                WHERE delete_by_user = false and delete_by_admin = false
                GROUP BY user_email
            ) c ON ui.email = c.user_email
                     LEFT JOIN (
                SELECT user_email, COUNT(*) AS post_count
                FROM community_posts
                WHERE delete_by_user = false and delete_by_admin = false
                GROUP BY user_email
            ) p ON ui.email = p.user_email
                     LEFT JOIN (
                select following_email, COUNT(*) as follow_count
                FROM user_follows
                GROUP BY following_email
            ) f ON ui.email = f.following_email
                    LEFT JOIN (
               select user_email, COUNT(*) as notification_count
               FROM user_notifications
               WHERE is_read = false
               GROUP BY user_email
            ) n ON ui.email = n.user_email
            WHERE ui.email = :user_email        
        """

    @staticmethod
    def get_my_page_posts():
        return """
            select cp.id::text AS id,
                   cp.slug,
                   ui.nickname,
                   cp.user_email,
                   cp.category,
                   cp.title,
                   cp.contents,
                   cp.thumbnail,
                   cp.delete_by_user,
                   cp.delete_by_admin,
                   cpv.view_count,
                   coalesce((SELECT COUNT(*)
                             FROM community_comments cc
                             WHERE cc.post_id = cp.id), 0) AS comment_count,
                   coalesce((SELECT SUM(CASE
                                            WHEN cpr.reaction_type = 1 THEN 1
                                            WHEN cpr.reaction_type = 0 THEN -1
                                            ELSE 0 END)
                             FROM community_posts_reactions cpr
                             WHERE cpr.post_id = cp.id), 0) as reaction_score,
                   cp.create_time,
                   cp.update_time
            from community_posts cp
            LEFT JOIN community_posts_views cpv on cp.id = cpv.post_id
            LEFT JOIN user_info ui on cp.user_email = ui.email
            where user_email = :user_email and cp.delete_by_user = false and cp.delete_by_admin = false
            order by cp.create_time desc
            limit :limit
            offset :offset        
        """

    @staticmethod
    def get_my_page_posts_total():
        return """
            select count(*)
            from community_posts cp
            LEFT JOIN community_posts_views cpv on cp.id = cpv.post_id
            where user_email = :user_email and cp.delete_by_user = false and cp.delete_by_admin = false        
        """

    @staticmethod
    def get_my_page_bookmarks():
        return """
            select cpb.post_id::text AS id,
                   cp.slug,
                   ui.nickname,
                   cp.user_email,
                   cp.category,
                   cp.title,
                   cp.contents,
                   cp.thumbnail,
                   cp.delete_by_user,
                   cp.delete_by_admin,
                   cpv.view_count,
                   coalesce((SELECT COUNT(*)
                             FROM community_comments cc
                             WHERE cc.post_id = cp.id), 0)  AS comment_count,
                   coalesce((SELECT SUM(CASE
                                            WHEN cpr.reaction_type = 1 THEN 1
                                            WHEN cpr.reaction_type = 0 THEN -1
                                            ELSE 0 END)
                             FROM community_posts_reactions cpr
                             WHERE cpr.post_id = cp.id), 0) as reaction_score
            from community_posts_bookmark cpb
                     left join community_posts cp on cpb.post_id = cp.id
                     LEFT JOIN community_posts_views cpv on cp.id = cpv.post_id
                     LEFT JOIN user_info ui on cp.user_email = ui.email
            where cpb.user_email = :user_email   
            and cp.delete_by_user = false and cp.delete_by_admin = false
            order by cp.create_time desc
            limit :limit
            offset :offset        
        """

    @staticmethod
    def get_my_page_bookmarks_total():
        return """
            select count(*)
            from community_posts_bookmark cpb
                     left join community_posts cp on cpb.post_id = cp.id
            where cpb.user_email = :user_email   
             and cp.delete_by_user = false and cp.delete_by_admin = false
        """

    @staticmethod
    def get_my_page_blocks():
        return """
            select ub.blocker_email, ub.blocked_email, ui.nickname, ub.reason, ub.create_time
            from user_block ub
                     left join user_info ui on ub.blocked_email = ui.email
            where ub.blocker_email = :user_email
            order by ub.create_time desc  
            limit :limit
            offset :offset             
        """

    @staticmethod
    def get_my_page_blocks_total():
        return """
            select count(*)
            from user_block ub
            where ub.blocker_email = :user_email        
        """

    @staticmethod
    def get_my_page_comments():
        return """
                WITH comment_count AS (
                    SELECT post_id, COUNT(*) AS comment_count
                    FROM community_comments
                    GROUP BY post_id
                ),
                reaction_sum AS (
                    SELECT post_id,
                           SUM(CASE
                                   WHEN reaction_type = 1 THEN 1
                                   WHEN reaction_type = 0 THEN -1
                                   ELSE 0 END) AS reaction_score
                    FROM community_posts_reactions
                    GROUP BY post_id
                )
                SELECT cp.id::text AS id,
                       cp.slug,
                       cp.user_email,
                       cp.category,
                       ui.nickname,
                       cp.title,
                       cp.contents,
                       cpv.view_count,
                       COALESCE(cc.comment_count, 0) AS comment_count,
                       COALESCE(r.reaction_score, 0) AS reaction_score,
                       cp.thumbnail,
                       cp.delete_by_user,
                       cp.delete_by_admin,
                       cp.create_time,
                       cp.update_time,
                       json_build_object(
                           'id', c.id,
                           'contents', c.contents,
                           'user_email', c.user_email,
                           'create_time', c.create_time,
                           'nickname', cui.nickname,
                           'update_time', c.update_time
                       ) AS comment
                FROM community_posts cp
                         LEFT JOIN user_info ui ON cp.user_email = ui.email
                         LEFT JOIN community_posts_views cpv ON cp.id = cpv.post_id
                         LEFT JOIN comment_count cc ON cc.post_id = cp.id
                         LEFT JOIN reaction_sum r ON r.post_id = cp.id
                         INNER JOIN community_comments c ON c.post_id = cp.id AND c.user_email = :user_email
                         LEFT JOIN user_info cui ON c.user_email = cui.email
                WHERE cp.delete_by_admin = false
                  AND cp.delete_by_user = false
                  AND c.delete_by_admin = false
                  AND c.delete_by_user = false
                  AND NOT EXISTS (
                      SELECT 1
                      FROM user_block ub
                      WHERE ub.blocker_email = :user_email
                        AND ub.blocked_email = cp.user_email
                  )
                ORDER BY cp.create_time DESC   
                LIMIT :limit OFFSET :offset     
        """

    @staticmethod
    def get_my_page_comments_total():
        return """
                SELECT count(*)
                FROM community_posts cp
                         INNER JOIN community_comments c 
                                 ON c.post_id = cp.id 
                WHERE cp.delete_by_admin = false
                  AND cp.delete_by_user = false
                  AND c.delete_by_admin = false
                  AND c.delete_by_user = false
                  AND NOT EXISTS (
                      SELECT 1
                      FROM user_block ub
                      WHERE ub.blocker_email = :user_email
                        AND ub.blocked_email = cp.user_email
                  )      
        """

    @staticmethod
    def get_my_page_follow():
        return """
            select uf.following_email,
                   uf.follower_email,
                   ui.nickname,
                   uf.create_time,
                   (select count(*) from community_posts cp where user_email = uf.following_email and cp.delete_by_admin = false and cp.delete_by_user = false)
            from user_follows uf
                     left join user_info ui on uf.follower_email = ui.email
            where uf.following_email = :user_email
            order by uf.create_time desc
            limit :limit
            offset :offset             
        """

    @staticmethod
    def get_my_page_follow_total():
        return """
            select count(*)
            from user_follows uf
            where uf.following_email = :user_email        
        """

    @staticmethod
    def get_my_page_notification():
        return """
            select user_email, noti_type, payload, is_read, created_time 
            from user_notifications un
            where un.user_email = :user_email
            order by un.created_time desc  
            limit :limit
            offset :offset             
        """

    @staticmethod
    def get_my_page_notification_total():
        return """
            select count(*)
            from user_notifications un
            where un.user_email = :user_email        
        """

    @staticmethod
    def update_my_page_notification():
        return """
            UPDATE user_notifications
            SET is_read = TRUE
            WHERE id = ANY(:ids)
        """
