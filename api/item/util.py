class ItemUtil:

    @staticmethod
    def get_rig_query():
        return """
            SELECT *
            FROM TKL_ITEM
            where category = 'Rig'
            ORDER BY (INFO->>'class_value')::NUMERIC, (INFO->>'capacity')::NUMERIC
        """

    @staticmethod
    def get_head_wear_query():
        return """
            SELECT *
            FROM TKL_ITEM
            where category = 'Headwear'
            ORDER BY (INFO->>'class_value')::NUMERIC, (INFO->>'capacity')::NUMERIC
        """

    @staticmethod
    def get_glasses_query():
        return """
            SELECT *
            FROM TKL_ITEM
            where category = 'Glasses'
            ORDER BY (INFO->>'class_value')::NUMERIC, (INFO->>'blindness_protection')::NUMERIC
        """

    @staticmethod
    def get_face_cover_query():
        return """
            SELECT *
            FROM TKL_ITEM
            where category = 'FaceCover'
            ORDER BY (INFO->>'class_value')::NUMERIC, (INFO->>'capacity')::NUMERIC
        """