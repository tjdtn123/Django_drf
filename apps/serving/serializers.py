from rest_framework import serializers


class AdServeSerializer(serializers.Serializer):
    """광고 서빙 응답 Serializer"""
    ad_id = serializers.IntegerField()
    creative_url = serializers.CharField()
    click_url = serializers.CharField()
    impression_url = serializers.CharField()
    width = serializers.IntegerField()
    height = serializers.IntegerField()
    alt_text = serializers.CharField()
