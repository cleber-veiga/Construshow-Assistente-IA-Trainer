from app.api.v1.resources.resources import *


def created_routes(api):
    api.add_resource(ChatTrainerResource, '/chat/train/')
    api.add_resource(ChatTrainerManager, '/chat/train/core')
    api.add_resource(ChatTrainerIntentionResource, '/chat/train/model/intention')
    api.add_resource(ChatTrainerDomainResource, '/chat/train/domain/')