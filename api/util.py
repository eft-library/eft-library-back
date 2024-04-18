from sqlalchemy.orm import class_mapper
import json


class Jsonify:
    def serialize_sqlalchemy_object(self, obj):
        if not obj:
            return None
        mapper = class_mapper(obj.__class__)
        columns = [column.key for column in mapper.columns]
        return {col: getattr(obj, col) for col in columns}

    def serialize_sqlalchemy_objects(self, objects):
        return [self.serialize_sqlalchemy_object(obj) for obj in objects]

    @classmethod
    def jsonify_sqlalchemy_objects(cls, objects):
        serialized_objects = cls.serialize_sqlalchemy_objects(objects)
        return json.dumps(serialized_objects)
