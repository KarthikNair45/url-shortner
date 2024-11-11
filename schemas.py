from marshmallow import Schema, fields, validate

class UrlSchema(Schema):
    id = fields.Number()
    url = fields.String()
    shortened_url = fields.String()
    created = fields.DateTime()