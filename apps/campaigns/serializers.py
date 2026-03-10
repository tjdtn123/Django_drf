from rest_framework import serializers

from .models import Ad, Campaign, Creative, Inventory


class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = ('id', 'name', 'slot_code', 'width', 'height', 'media_type', 'is_active')


class CreativeSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Creative
        fields = ('id', 'ad', 'file', 'file_url', 'click_url', 'alt_text', 'is_active', 'created_at')
        read_only_fields = ('id', 'file_url', 'created_at')

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


class AdSerializer(serializers.ModelSerializer):
    creatives = CreativeSerializer(many=True, read_only=True)
    inventory_detail = InventorySerializer(source='inventory', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Ad
        fields = (
            'id', 'campaign', 'inventory', 'inventory_detail',
            'name', 'status', 'status_display', 'weight',
            'frequency_cap', 'targeting', 'creatives',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_weight(self, value):
        if not 1 <= value <= 100:
            raise serializers.ValidationError("가중치는 1~100 사이여야 합니다.")
        return value


class AdListSerializer(serializers.ModelSerializer):
    """목록 조회용 - creatives 제외한 경량 버전"""
    inventory_detail = InventorySerializer(source='inventory', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Ad
        fields = (
            'id', 'campaign', 'inventory', 'inventory_detail',
            'name', 'status', 'status_display', 'weight', 'frequency_cap',
        )


class CampaignSerializer(serializers.ModelSerializer):
    ads = AdListSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    billing_type_display = serializers.CharField(source='get_billing_type_display', read_only=True)
    advertiser_name = serializers.CharField(source='advertiser.company_name', read_only=True)

    class Meta:
        model = Campaign
        fields = (
            'id', 'advertiser', 'advertiser_name',
            'name', 'status', 'status_display',
            'budget', 'daily_budget', 'start_date', 'end_date',
            'target_impressions', 'billing_type', 'billing_type_display',
            'unit_price', 'ads', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'advertiser', 'created_at', 'updated_at')

    def validate(self, data):
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] >= data['end_date']:
                raise serializers.ValidationError("종료일은 시작일보다 늦어야 합니다.")
        return data


class CampaignListSerializer(serializers.ModelSerializer):
    """목록 조회용 - ads 제외한 경량 버전"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    billing_type_display = serializers.CharField(source='get_billing_type_display', read_only=True)
    advertiser_name = serializers.CharField(source='advertiser.company_name', read_only=True)
    ad_count = serializers.IntegerField(source='ads.count', read_only=True)

    class Meta:
        model = Campaign
        fields = (
            'id', 'advertiser_name', 'name', 'status', 'status_display',
            'budget', 'daily_budget', 'start_date', 'end_date',
            'billing_type', 'billing_type_display', 'ad_count',
        )
