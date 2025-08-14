class CommunityUtil:

    @staticmethod
    def get_post_detail():
        return """
            SELECT
                cp.id,
                cp.slug,
                cp.user_email,
                ui.nickname,
                cp.category,
                cp.title,
                cp.contents,
                cp.thumbnail,
                cp.create_time,
                cp.update_time,
                -- 작성자 팔로워 수
                (SELECT COUNT(*)
                 FROM user_follows uf
                 WHERE uf.following_email = cp.user_email) AS follower_count,
                -- 작성자 게시글 전체 수
                (SELECT COUNT(*)
                 FROM community_posts cp2
                 WHERE cp2.user_email = cp.user_email) AS total_post_count
            FROM community_posts cp
            LEFT JOIN user_info ui ON cp.user_email = ui.email
            WHERE cp.id = :post_id        
        """
