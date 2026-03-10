"""
샘플 데이터 생성 커맨드
사용법: python manage.py seed_data
"""
import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import Advertiser
from apps.campaigns.models import Ad, Campaign, Creative, Inventory


class Command(BaseCommand):
    help = "샘플 데이터 생성 (광고주 5, 캠페인 10, 광고 20, 인벤토리 6)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="기존 데이터 삭제 후 생성",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self._clear_data()

        self._create_inventories()
        self._create_advertisers()
        self._create_campaigns_and_ads()

        self.stdout.write(self.style.SUCCESS("샘플 데이터 생성 완료!"))
        self._print_summary()

    def _clear_data(self):
        Creative.objects.all().delete()
        Ad.objects.all().delete()
        Campaign.objects.all().delete()
        Inventory.objects.all().delete()
        Advertiser.objects.all().delete()
        User.objects.filter(username__startswith="advertiser").delete()
        self.stdout.write("기존 데이터 삭제 완료")

    def _create_inventories(self):
        inventories = [
            {"name": "메인 배너", "slot_code": "main_banner", "width": 728, "height": 90, "media_type": "web"},
            {"name": "사이드바 배너", "slot_code": "sidebar_banner", "width": 300, "height": 250, "media_type": "web"},
            {"name": "모바일 배너", "slot_code": "mobile_banner", "width": 320, "height": 50, "media_type": "mobile"},
            {"name": "모바일 전면", "slot_code": "mobile_interstitial", "width": 320, "height": 480, "media_type": "mobile"},
            {"name": "동영상 프리롤", "slot_code": "video_preroll", "width": 640, "height": 360, "media_type": "video"},
            {"name": "인앱 배너", "slot_code": "inapp_banner", "width": 320, "height": 50, "media_type": "inapp"},
        ]
        for data in inventories:
            Inventory.objects.get_or_create(slot_code=data["slot_code"], defaults=data)
        self.stdout.write(f"  인벤토리 {len(inventories)}개 생성")

    def _create_advertisers(self):
        companies = [
            ("삼성전자", "123-45-67890"),
            ("LG전자", "234-56-78901"),
            ("현대자동차", "345-67-89012"),
            ("네이버", "456-78-90123"),
            ("카카오", "567-89-01234"),
        ]
        self.advertisers = []
        for i, (company, biz_num) in enumerate(companies, 1):
            username = f"advertiser{i:02d}"
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={"email": f"{username}@example.com"},
            )
            user.set_password("test1234!")
            user.save()

            advertiser, _ = Advertiser.objects.get_or_create(
                user=user,
                defaults={
                    "company_name": company,
                    "business_number": biz_num,
                    "balance": random.randint(1, 10) * 1_000_000,
                },
            )
            self.advertisers.append(advertiser)
        self.stdout.write(f"  광고주 {len(companies)}명 생성 (비밀번호: test1234!)")

    def _create_campaigns_and_ads(self):
        inventories = list(Inventory.objects.all())
        now = timezone.now()

        campaign_data = [
            ("삼성 갤럭시 S25 출시 캠페인", Campaign.BillingType.CPM, 5_000_000, 500_000, 1_000_000),
            ("LG OLED TV 봄 프로모션", Campaign.BillingType.CPC, 3_000_000, 300_000, 500),
            ("현대차 아이오닉6 브랜딩", Campaign.BillingType.CPM, 8_000_000, 800_000, 2_000_000),
            ("네이버 플러스 멤버십", Campaign.BillingType.CPC, 2_000_000, 200_000, 300),
            ("카카오T 신규 가입 이벤트", Campaign.BillingType.CPC, 1_500_000, 150_000, 200),
            ("삼성 비스포크 가전 특가", Campaign.BillingType.CPM, 4_000_000, 400_000, 800_000),
            ("LG 그램 노트북 출시", Campaign.BillingType.CPM, 3_500_000, 350_000, 700_000),
            ("현대차 캐스퍼 일렉트릭", Campaign.BillingType.CPP, 6_000_000, 6_000_000, 0),
            ("네이버 쇼핑라이브", Campaign.BillingType.CPV, 2_500_000, 250_000, 0),
            ("카카오 선물하기 이벤트", Campaign.BillingType.CPC, 1_000_000, 100_000, 100),
        ]

        status_cycle = [
            Campaign.Status.ACTIVE,
            Campaign.Status.ACTIVE,
            Campaign.Status.ACTIVE,
            Campaign.Status.ACTIVE,
            Campaign.Status.PAUSED,
            Campaign.Status.ACTIVE,
            Campaign.Status.DRAFT,
            Campaign.Status.ACTIVE,
            Campaign.Status.COMPLETED,
            Campaign.Status.ACTIVE,
        ]

        ad_count = 0
        for i, (name, billing, budget, daily, unit) in enumerate(campaign_data):
            advertiser = self.advertisers[i % len(self.advertisers)]
            status = status_cycle[i]

            campaign = Campaign.objects.create(
                advertiser=advertiser,
                name=name,
                status=status,
                budget=budget,
                daily_budget=daily,
                start_date=now - timedelta(days=random.randint(1, 10)),
                end_date=now + timedelta(days=random.randint(10, 60)),
                target_impressions=random.randint(10_000, 500_000),
                billing_type=billing,
                unit_price=unit,
            )

            # 캠페인당 광고 2개 생성
            for j in range(2):
                inventory = random.choice(inventories)
                ad = Ad.objects.create(
                    campaign=campaign,
                    inventory=inventory,
                    name=f"{name} - 소재{j + 1}",
                    status=Ad.Status.ACTIVE if status == Campaign.Status.ACTIVE else Ad.Status.PAUSED,
                    weight=random.choice([50, 70, 80, 100]),
                    frequency_cap=random.choice([None, None, 3, 5, 10]),
                    targeting={"hours": list(range(9, 22))} if j % 2 == 0 else {},
                )
                Creative.objects.create(
                    ad=ad,
                    file=f"creatives/sample/banner_{i}_{j}.jpg",
                    click_url=f"https://example.com/landing/{i}/{j}",
                    alt_text=f"{name} 광고 이미지",
                )
                ad_count += 1

        self.stdout.write(f"  캠페인 {len(campaign_data)}개 생성")
        self.stdout.write(f"  광고 {ad_count}개 + 소재 {ad_count}개 생성")

    def _print_summary(self):
        self.stdout.write("\n--- 생성 결과 ---")
        self.stdout.write(f"  광고주: {Advertiser.objects.count()}명")
        self.stdout.write(f"  인벤토리: {Inventory.objects.count()}개")
        self.stdout.write(f"  캠페인: {Campaign.objects.count()}개")
        self.stdout.write(f"  광고: {Ad.objects.count()}개")
        self.stdout.write(f"  소재: {Creative.objects.count()}개")
        self.stdout.write("\n광고주 계정: advertiser01~05 / test1234!")
