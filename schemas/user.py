#!/usr/bin/env python
# -*- coding: utf-8 -*-
from marshmallow import Schema, fields
from marshmallow import ValidationError
from marshmallow import validates_schema


class UserName(Schema):
    first_name = fields.Str()
    last_name = fields.Str()


class UserCoordinates(Schema):
    longitude = fields.Float()
    latitude = fields.Float()


class UserLocation(Schema):
    type = fields.Str()
    coordinates = fields.List(fields.Float())


class UserSchema(Schema):
    id = fields.Str(attribute='_id')
    username = fields.Str()
    password = fields.Str(load_only=True)
    name = fields.Nested(UserName)
    location = fields.Nested(UserLocation)

    @validates_schema(pass_original=True)
    def check_unknown_fields(self, data, original_data):
        for key in original_data:
            if key not in self.fields:
                raise ValidationError(
                    'Unknown field name {}'.format(key))
