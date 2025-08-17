class CommentUtil:

    @staticmethod
    def insert_parent_comment():
        return """
            INSERT INTO community_comments (id, parent_id, post_id, contents, path)
            VALUES (
                :comment_id,        -- id (nanoid)
                NULL,            -- parent_id 없음
                :post_id,               -- post_id
                :contents,
                :comment_id::ltree  -- path = id
            )        
        """

    @staticmethod
    def insert_child_comment():
        return """
            WITH parent AS (
                SELECT path
                FROM community_comments
                WHERE id = :parent_comment_id
            )
            INSERT INTO community_comments (id, parent_id, post_id, contents, path)
            SELECT
                :comment_id,       -- id (nanoid)
                :parent_comment_id,       -- parent_id
                :post_id,               -- post_id
                :contents,
                parent.path || :comment_id  -- path = 부모 path + 새 id
            FROM parent  
        """

    @staticmethod
    def update_comment():
        return """
        """

    @staticmethod
    def delete_comment_by_user():
        return """
        """

    @staticmethod
    def delete_comment_by_admin():
        return """
        """

    @staticmethod
    def get_comment():
        """
        rn_start = (page - 1) * limit + 1
        rn_end   = page * limit
        """
        return """
            WITH RECURSIVE tree AS (
                SELECT id, parent_id, post_id, path, contents, delete_by_admin, delete_by_user, create_time, update_time
                FROM community_comments
                WHERE post_id = :post_id AND nlevel(path) = 1
                UNION ALL
                SELECT c.id, c.parent_id, c.post_id, c.path, c.contents, c.delete_by_admin, c.delete_by_user, c.create_time, c.update_time
                FROM community_comments c
                JOIN tree t ON c.parent_id = t.id
                WHERE c.post_id = :post_id
            )
            SELECT *
            FROM (
                SELECT *, row_number() OVER (ORDER BY path, create_time) AS rn
                FROM tree
            ) t
            WHERE rn BETWEEN :rn_start AND :rn_end
            ORDER BY path
        """

    @staticmethod
    def my_page_comment():
        return """
        """
