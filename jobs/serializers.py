from rest_framework.fields import DateTimeField
from rest_framework.serializers import ModelSerializer

from jobs.models import Job


class JobSerializer(ModelSerializer):
    class Meta:
        fields = Job.serializable_fields()
        model = Job

    synced_at = DateTimeField(required=False, allow_null=True)
