from rest_framework.serializers import ModelSerializer

from news.models import Article


class ArticleSerializer(ModelSerializer):
    class Meta:
        fields = Article.serializable_fields()
        model = Article
