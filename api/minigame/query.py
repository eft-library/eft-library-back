class MinigameQueryV3:
    @staticmethod
    def get_rng_item_rank_v3():
        return """
            SELECT
              ROW_NUMBER() OVER (ORDER BY score DESC, create_time) AS rank,
              nickname,
              score,
              create_time
            FROM user_minigame_score
            WHERE game_type = 'RNG-ITEM'
              AND create_time >= date_trunc('week', now() + interval '9 hour') - interval '9 hour'
              AND create_time <  date_trunc('week', now() + interval '9 hour') + interval '7 day' - interval '9 hour'
            ORDER BY score DESC, create_time
            LIMIT 10;
        """

    @staticmethod
    def get_rng_item_my_rank_list_v3():
        return """
            WITH ranked AS (
              SELECT
                ROW_NUMBER() OVER (ORDER BY score DESC, create_time) AS rank,
                nickname,
                score,
                create_time
              FROM user_minigame_score
              WHERE game_type = 'RNG-ITEM'
                AND create_time >= date_trunc('week', now() + interval '9 hour') - interval '9 hour'
                AND create_time <  date_trunc('week', now() + interval '9 hour') + interval '7 day' - interval '9 hour'
            ),
            my_rank AS (
              SELECT COUNT(*) + 1 AS rank
              FROM user_minigame_score
              WHERE game_type = 'RNG-ITEM'
                AND create_time >= date_trunc('week', now() + interval '9 hour') - interval '9 hour'
                AND create_time <  date_trunc('week', now() + interval '9 hour') + interval '7 day' - interval '9 hour'
                AND score > :score
            )
            SELECT *
            FROM ranked
            WHERE
              rank <= 3
              OR rank BETWEEN
                (SELECT rank FROM my_rank) - 3
                AND
                (SELECT rank FROM my_rank) + 2
            ORDER BY rank
        """
