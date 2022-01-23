from rest_framework.fields import CharField, IntegerField
from rest_framework.serializers import ModelSerializer

from news.models import Item


class ItemSerializer(ModelSerializer):
    class Meta:
        fields = Item.serializable_fields()
        model = Item

    id = IntegerField(read_only=False, required=False, allow_null=True)
    text = CharField(allow_blank=True)

    def create(self, validated_data):
        validated_data.pop("children")
        instance, _ = self.Meta.model.objects.update_or_create(
            defaults=validated_data,
            id=validated_data.get("id"),
        )
        return instance
