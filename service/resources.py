from import_export import resources
from .models import BlockedSentence

class BlockedSentenceResource(resources.ModelResource):
    class Meta:
        model = BlockedSentence
        fields = ('message', 'date', 'status',)