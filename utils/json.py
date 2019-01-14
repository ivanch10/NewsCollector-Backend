import json
from bson import ObjectId

UTF_8 = 'utf-8'

"""Encode object for mongo."""
class JSONEncoder(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, ObjectId):
      return str(obj)
    elif isinstance(obj, bytes):
      return str(obj, encoding=UTF_8)
    return json.JSONEncoder.default(self, obj)
