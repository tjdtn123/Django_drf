Mini Ad Manager

Django 미니 광고 관리 플랫폼 프로젝트 설계서

니트머스(주) 입사 준비용 포트폴리오 프로젝트

목표 기술 스택: Python  |  Django  |  DRF  |  PostgreSQL  |  Redis  |  Celery  |  Docker

예상 기간: 4주 (1일 2~3시간 기준)  |  난이도: ★★☆ (중급)

# 1. 프로젝트 개요

## 1.1 배경 및 목적

니트머스는 2004년 설립된 디지털 광고 플랫폼 전문 기업으로, Ad Server 기술을 기반으로 웹/모바일/동영상/인게임 등 다양한 채널의 광고 송출 및 관리 솔루션을 제공합니다.

이 프로젝트는 니트머스의 핵심 비즈니스인 광고 송출 및 캔페인 관리 시스템의 축소판을 Django로 직접 구현함으로써, 아래 목적을 달성합니다:

니트머스의 광고 도메인에 대한 기술적 이해도 입증

Spring 경험을 Django로 전환할 수 있는 프레임워크 적응력 시연

실제 동작하는 포트폴리오로 면접 시 구체적인 기술 논의 가능

## 1.2 프로젝트 범위

광고주가 캔페인을 등록하고, 광고 소재를 업로드하고, 노출/클릭 통계를 확인할 수 있는 관리 플랫폼. 외부에서 광고를 요청하면 타겟 조건에 맞는 광고를 JSON으로 반환하는 Ad Serving API까지 포함.

## 1.3 Spring → Django 개념 매핑

Spring 2년 경험을 Django로 빠르게 전환하기 위한 핵심 개념 대응표:

# 2. 시스템 아키텍처

## 2.1 전체 구성도

시스템은 아래 4개 계층으로 구성됩니다:

Client Layer: Django Template 또는 간단한 React 대시보드

API Layer: DRF ViewSet + Serializer (캔페인 CRUD, 광고 서빙, 리포트)

Service Layer: 광고 선택 로직, 타겟팅, 통계 집계 (비즈니스 로직 분리)

Data Layer: PostgreSQL + Redis(캐시) + Celery(비동기)

## 2.2 프로젝트 디렉토리 구조

Spring의 패키지 구조와 비교하며 Django 프로젝트를 구성합니다:

# 3. 데이터 모델 설계

## 3.1 Advertiser (광고주)

광고주 계정 및 기본 정보를 관리합니다.

## 3.2 Campaign (캔페인)

광고 집행의 최상위 단위입니다. 니트머스의 캔페인 관리 기능을 반영합니다.

## 3.3 Inventory (지면/인벤토리)

광고가 노출되는 위치(지면)를 관리합니다.

## 3.4 Ad (광고)

캔페인 하위의 개별 광고 단위입니다.

## 3.5 Creative (소재)

광고에 사용되는 실제 이미지/동영상 소재입니다.

## 3.6 EventLog (이벤트 로그)

노출/클릭 이벤트를 기록합니다. 니트머스의 리포팅 시스템의 기초입니다.

## 3.7 DailyReport (일별 통계)

Celery 태스크로 일별 집계하는 통계 테이블입니다.

# 4. API 설계

## 4.1 캔페인 관리 API

## 4.2 광고 관리 API

## 4.3 광고 서빙 API (★ 핵심)

외부 매체가 호출하여 광고를 받아가는 핵심 API입니다. 니트머스의 Ad Server의 핵심 로직을 반영합니다.

광고 서빙 요청 예시:

## 4.4 리포트 API

# 5. 핵심 비즈니스 로직

## 5.1 광고 선택 알고리즘 (Ad Selection)

니트머스의 핵심인 광고 선택 로직을 단순화하여 구현합니다:

인벤토리 필터링: slot_code로 해당 지면에 배정된 광고만 필터

상태 필터링: active 상태의 캔페인/광고만 선택

기간 필터링: start_date <= now <= end_date

예산 필터링: 일일 예산 초과하지 않은 캔페인

가중치 기반 랜덤 선택: weight 값에 비례하여 확률적 선택 (Weighted Random)

## 5.2 타겟팅 로직

간단한 수준의 타겟팅을 구현합니다:

시간대 타겟팅: 광고별 노출 시간대 설정 (JSON 필드로 저장)

디바이스 타겟팅: User-Agent 파싱으로 PC/Mobile/Tablet 구분

Frequency Capping: Redis로 사용자별 노출 횟수 제한 (니트머스의 Frequency 조절 기능 반영)

## 5.3 이벤트 트래킹 및 통계

트래킹 플로우:

광고 서빙 시 impression_url을 함께 반환

클라이언트가 impression_url 호출 → EventLog에 impression 기록

클릭 시 click_url 호출 → EventLog에 click 기록 → 광고주 URL로 302 Redirect

Celery Beat가 매일 새벽 EventLog를 집계하여 DailyReport 생성

Redis 활용 포인트:

실시간 노출/클릭 카운터 (INCR 명령)

Frequency Capping 저장소 (IP 기반, TTL 24h)

광고 선택 결과 캐싱 (TTL 5min)

# 6. 주차별 상세 계획

## 1주차: Django 기초 + 모델 설계 + Admin

목표: Django 프로젝트 세팅, 전체 모델 구현, Django Admin으로 기본 CRUD 확인

학습 포인트: Django의 MTV 패턴 vs Spring MVC, ORM의 Lazy Loading 차이, Migration 시스템 vs Flyway/Liquibase

## 2주차: DRF API 개발 + 광고 서빙

목표: REST API 전체 구현, 광고 서빙 핵심 로직 완성

학습 포인트: Serializer vs DTO, ViewSet vs @Controller, DRF Permission vs Spring Security, pytest vs JUnit

## 3주차: 통계/리포팅 + 비동기 처리

목표: Celery로 비동기 통계 집계, Redis 캐싱, 리포트 API 완성

학습 포인트: Celery vs @Async/@Scheduled, Django ORM aggregate vs JPA @Query, Redis를 활용한 캐시 전략

## 4주차: 프론트엔드 + Docker + 마무리

목표: 대시보드 UI, Docker 배포 환경, 문서화, GitHub 정리

학습 포인트: Django Template vs Thymeleaf, Docker Compose로 멀티 컨테이너 구성, CI/CD 기초

# 7. 면접 대비 포인트

## 7.1 이 프로젝트로 어필할 수 있는 것

### 기술적 질문 대비

"Spring과 Django의 차이점은?" → 직접 둘 다 사용해보며 느낀 ORM, 설정, 테스트 등의 차이를 구체적으로 설명

"광고 서빙 시 성능을 어떻게 보장했나요?" → Redis 캐싱, DB 인덱스 최적화, select_related 등 실제 적용 사례

"통계 처리 방식은?" → 실시간(Redis INCR) + 배치(Celery 일별 집계) 이원 구조 설명

### 도메인 지식 어필

"니트머스의 제품에 대해 아시나요?" → 직접 미니 Ad Server를 만들어봄으로써 광고 송출, 타겟팅, 리포팅의 흐름을 이해

"CPM, CPC, CTR 등의 개념을 아시나요?" → 프로젝트에서 실제 과금 및 통계 로직을 구현했으므로 실무 수준 설명 가능

## 7.2 README에 반드시 넣을 내용

프로젝트 개요 + 니트머스에 대한 관심을 바탕으로 만들었다는 동기

시스템 아키텍처 다이어그램 (Mermaid 또는 이미지)

API 문서 링크 (Swagger UI)

Spring → Django 전환 경험 정리 섹션

기술적 챌린지 및 해결 과정 기록

## 7.3 확장 가능한 방향 (면접 어필 용)

시간이 남거나 면접에서 확장성을 물을 때 언급할 수 있는 포인트:

A/B 테스트: 복수 Creative를 비율로 분배하여 CTR 비교

RTB (Real-Time Bidding): OpenRTB 프로토콜 기반 입찰 시스템

DMP 연동: 사용자 세그먼트 기반 오디언스 타겟팅

복수 매체 통합: 니트머스처럼 One Platform, Multi Media 구현

Kubernetes 배포: Docker Compose에서 K8s로 확장

# 8. 기술 스택 상세

Mini Ad Manager — Django 미니 광고 관리 플랫폼 프로젝트 설계서



| Spring (Java) | Django (Python) | 💡 팅 |

|---|---|---|

| @Entity | models.Model | Django ORM은 JPA보다 직관적 |

| @RestController | ViewSet + Router | DRF의 ViewSet = Controller |

| @Service | 별도 service.py | Django는 관례적 분리 |

| application.yml | settings.py | 파이썬 파일로 설정 관리 |

| JPA Repository | Django ORM Manager | QuerySet 체이닝 = Stream API |

| Spring Security | DRF Permission + JWT | 데코레이터 패턴 사용 |

| Gradle/Maven | pip + requirements.txt | Poetry도 고려 가능 |

| @Scheduled | Celery Beat | 비동기 태스크 처리용 |





| mini_ad_manager/              # 프로젝트 루트
├── config/                     # 설정 (≈ application.yml)
│   ├── settings/
│   │   ├── base.py            # 공통 설정
│   │   ├── local.py           # 개발 환경
│   │   └── production.py      # 운영 환경
│   ├── urls.py                # URL 라우팅 (≈ @RequestMapping)
│   └── celery.py              # Celery 설정
├── apps/
│   ├── accounts/              # 사용자/광고주 관리
│   │   ├── models.py          # ≈ @Entity
│   │   ├── serializers.py     # ≈ DTO
│   │   ├── views.py           # ≈ @RestController
│   │   ├── services.py        # ≈ @Service
│   │   ├── urls.py            # ≈ Router
│   │   └── tests.py
│   ├── campaigns/             # 캔페인/광고 관리
│   ├── serving/               # 광고 서빙 API
│   └── reports/               # 통계/리포트
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── requirements/
│   ├── base.txt
│   ├── local.txt
│   └── production.txt
└── manage.py |

|---|





| 필드명 | 타입 | 설명 | Spring 대응 |

|---|---|---|---|

| id | BigAutoField | PK, 자동증가 | @Id @GeneratedValue |

| user | OneToOneField(User) | Django 기본 User 확장 | UserDetails |

| company_name | CharField(100) | 회사명 | String |

| business_number | CharField(20) | 사업자등록번호 | String |

| balance | DecimalField | 광고비 잔액 (선불) | BigDecimal |

| created_at | DateTimeField(auto_now_add) | 등록일 | @CreatedDate |





| 필드명 | 타입 | 설명 | Spring 대응 |

|---|---|---|---|

| id | BigAutoField | PK | @Id |

| advertiser | ForeignKey(Advertiser) | 광고주 (N:1) | @ManyToOne |

| name | CharField(200) | 캔페인명 | String |

| status | CharField(choices) | draft/active/paused/completed | Enum |

| budget | DecimalField | 총 예산 | BigDecimal |

| daily_budget | DecimalField | 일일 예산 상한 | BigDecimal |

| start_date | DateTimeField | 시작일 | LocalDateTime |

| end_date | DateTimeField | 종료일 | LocalDateTime |

| target_impressions | IntegerField | 목표 노출수 | Integer |

| billing_type | CharField(choices) | CPM/CPC/CPP/CPV | Enum |

| unit_price | DecimalField | 단가 (예: CPM 1,000원) | BigDecimal |





| 필드명 | 타입 | 설명 | Spring 대응 |

|---|---|---|---|

| id | BigAutoField | PK | @Id |

| name | CharField(100) | 지면명 (ex: 메인배너) | String |

| slot_code | SlugField(unique) | API 호출용 코드 | String |

| width | IntegerField | 광고 너비 (px) | Integer |

| height | IntegerField | 광고 높이 (px) | Integer |

| media_type | CharField(choices) | web/mobile/video/inapp | Enum |

| is_active | BooleanField | 활성 여부 | Boolean |





| 필드명 | 타입 | 설명 | Spring 대응 |

|---|---|---|---|

| id | BigAutoField | PK | @Id |

| campaign | ForeignKey(Campaign) | 캔페인 (N:1) | @ManyToOne |

| inventory | ForeignKey(Inventory) | 타겟 지면 (N:1) | @ManyToOne |

| name | CharField(200) | 광고명 | String |

| status | CharField(choices) | active/paused/ended | Enum |

| weight | IntegerField(default=100) | 노출 비중 (1~100) | Integer |

| frequency_cap | IntegerField(null) | 빈도 제한 (1일 기준) | Integer |





| 필드명 | 타입 | 설명 | Spring 대응 |

|---|---|---|---|

| id | BigAutoField | PK | @Id |

| ad | ForeignKey(Ad) | 광고 (N:1) | @ManyToOne |

| file | FileField | 소재 파일 (S3 또는 로컬) | MultipartFile |

| click_url | URLField | 클릭 시 이동 URL | String |

| alt_text | CharField(200) | 대체 텍스트 | String |

| is_active | BooleanField | 활성 여부 | Boolean |





| 필드명 | 타입 | 설명 | Spring 대응 |

|---|---|---|---|

| id | BigAutoField | PK | @Id |

| ad | ForeignKey(Ad) | 광고 | @ManyToOne |

| event_type | CharField(choices) | impression/click | Enum |

| ip_address | GenericIPAddressField | 사용자 IP | String |

| user_agent | TextField | 브라우저 정보 | String |

| device_type | CharField(choices) | pc/mobile/tablet | Enum |

| created_at | DateTimeField(auto_now_add) | 이벤트 발생 시각 | @CreatedDate |





| 필드명 | 타입 | 설명 | Spring 대응 |

|---|---|---|---|

| id | BigAutoField | PK | @Id |

| ad | ForeignKey(Ad) | 광고 | @ManyToOne |

| date | DateField | 집계 날짜 | LocalDate |

| impressions | IntegerField | 총 노출수 | Integer |

| clicks | IntegerField | 총 클릭수 | Integer |

| ctr | DecimalField | CTR (클릭률) | BigDecimal |

| spent | DecimalField | 소진 광고비 | BigDecimal |





| Method | Endpoint | 설명 | 응답 |

|---|---|---|---|

| GET | /api/v1/campaigns/ | 캔페인 목록 조회 | Paginated list |

| POST | /api/v1/campaigns/ | 캔페인 생성 | Campaign object |

| GET | /api/v1/campaigns/{id}/ | 캔페인 상세 조회 | Campaign detail |

| PATCH | /api/v1/campaigns/{id}/ | 캔페인 수정 | Updated object |

| DELETE | /api/v1/campaigns/{id}/ | 캔페인 삭제 | 204 No Content |

| POST | /api/v1/campaigns/{id}/activate/ | 캔페인 활성화 | Status changed |

| POST | /api/v1/campaigns/{id}/pause/ | 캔페인 일시정지 | Status changed |





| Method | Endpoint | 설명 | 응답 |

|---|---|---|---|

| GET | /api/v1/ads/ | 광고 목록 | Paginated list |

| POST | /api/v1/ads/ | 광고 생성 | Ad object |

| PATCH | /api/v1/ads/{id}/ | 광고 수정 | Updated object |

| POST | /api/v1/ads/{id}/creatives/ | 소재 업로드 | Creative object |





| Method | Endpoint | 설명 | 응답 |

|---|---|---|---|

| GET | /api/v1/serve/ | 광고 요청 (쿼리 파라미터) | Ad JSON + tracking URLs |

| GET | /api/v1/track/impression/{ad_id}/ | 노출 트래킹 (1x1 pixel) | 1x1 GIF |

| GET | /api/v1/track/click/{ad_id}/ | 클릭 트래킹 + 리다이렉트 | 302 Redirect |





| GET /api/v1/serve/?slot=main_banner&device=pc&user_ip=1.2.3.4
 
// Response
{
  "ad_id": 42,
  "creative_url": "/media/creatives/banner_001.jpg",
  "click_url": "/api/v1/track/click/42/?redirect=https://...",
  "impression_url": "/api/v1/track/impression/42/",
  "width": 728,
  "height": 90,
  "alt_text": "봄 세일 최대 50% 할인"
} |

|---|





| Method | Endpoint | 설명 | 응답 |

|---|---|---|---|

| GET | /api/v1/reports/campaign/{id}/ | 캔페인별 일별 통계 | DailyReport list |

| GET | /api/v1/reports/dashboard/ | 대시보드 요약 | Summary JSON |

| GET | /api/v1/reports/export/ | 리포트 CSV 다운로드 | CSV file |





| # | 태스크 | 세부 내용 | 산출물 | 예상 시간 |

|---|---|---|---|---|

| 1 | 환경 세팅 | venv 생성, Django/DRF 설치, PostgreSQL 연결, 프로젝트 초기화 | requirements.txt, settings.py | 2시간 |

| 2 | 모델 구현 | 위 설계서의 7개 모델 전체 구현, migration 실행 | models.py x 4개 앱 | 3시간 |

| 3 | Admin 커스터마이징 | ModelAdmin으로 관리자 화면 구성, 필터/검색 추가 | admin.py x 4개 앱 | 2시간 |

| 4 | 테스트 데이터 | management command로 샘플 데이터 생성 (광고주 5, 캔페인 10, 광고 20) | seed_data.py | 1시간 |

| 5 | Django ORM 연습 | shell_plus로 QuerySet 연습 (Spring JPA와 비교 정리) | 개인 노트 | 2시간 |





| # | 태스크 | 세부 내용 | 산출물 | 예상 시간 |

|---|---|---|---|---|

| 1 | Serializer 구현 | Campaign, Ad, Creative, Inventory의 Serializer 작성 (Nested 포함) | serializers.py x 4 | 2시간 |

| 2 | ViewSet + Router | ModelViewSet으로 CRUD, custom action으로 activate/pause | views.py, urls.py | 3시간 |

| 3 | 광고 서빙 API | AdSelectionService 구현: 필터링 → 타겟팅 → 가중치 선택 | serving/services.py | 4시간 |

| 4 | 트래킹 API | impression/click 트래킹 엔드포인트 (1x1 pixel, 302 redirect) | serving/views.py | 2시간 |

| 5 | API 테스트 | pytest + DRF APIClient로 주요 API 테스트 작성 | tests/ x 4 | 2시간 |

| 6 | 인증/권한 | JWT 인증 (simplejwt), 광고주별 데이터 격리 (Permission) | permissions.py | 2시간 |





| # | 태스크 | 세부 내용 | 산출물 | 예상 시간 |

|---|---|---|---|---|

| 1 | Redis 연동 | 실시간 카운터 (INCR), Frequency Cap 저장소 구현 | cache.py, services.py | 2시간 |

| 2 | Celery 세팅 | Celery + Redis broker 설정, Celery Beat 스케줄러 | celery.py, tasks.py | 2시간 |

| 3 | 일별 통계 집계 | EventLog → DailyReport 집계 태스크 (aggregate, annotate) | reports/tasks.py | 3시간 |

| 4 | 리포트 API | 캔페인별/기간별 통계 조회, CSV 익스포트 | reports/views.py | 2시간 |

| 5 | 모니터링 로직 | 목표 노출량 vs 현재 노출량 비교, 예산 소진율 계산 | reports/services.py | 2시간 |

| 6 | 성능 최적화 | DB 인덱스 추가, select_related/prefetch_related, 쿼리 프로파일링 | models.py 수정 | 1시간 |





| # | 태스크 | 세부 내용 | 산출물 | 예상 시간 |

|---|---|---|---|---|

| 1 | 대시보드 UI | Django Template + Chart.js 또는 React로 통계 대시보드 (캔페인 목록, 차트) | templates/ 또는 frontend/ | 4시간 |

| 2 | Docker화 | Dockerfile + docker-compose (Django + PostgreSQL + Redis) | docker/ | 2시간 |

| 3 | API 문서화 | drf-spectacular로 Swagger UI 자동 생성 | schema.yml | 1시간 |

| 4 | README 작성 | 프로젝트 소개, 설치 방법, 주요 기능, 스크린샷, 기술 포인트 | README.md | 2시간 |

| 5 | GitHub 정리 | .gitignore, 브랜치 정리, 커밋 메시지 정리 | repository | 1시간 |

| 6 | 최종 점검 | 전체 플로우 테스트, 버그 수정, 코드 리팩토링 | 최종 버전 | 2시간 |





| 구분 | 기술 | 비고 |

|---|---|---|

| 언어 | Python 3.11+ | Type Hint 적극 활용 |

| 프레임워크 | Django 5.x | LTS 버전 권장 |

| API | Django REST Framework 3.15+ | Serializer + ViewSet |

| 데이터베이스 | PostgreSQL 16 | 프로덕션 급 RDBMS |

| 캐시/브로커 | Redis 7 | 캐싱 + Celery broker |

| 비동기 | Celery 5.x + Beat | 주기적 통계 집계 |

| 인증 | djangorestframework-simplejwt | JWT 토큰 방식 |

| API 문서 | drf-spectacular | OpenAPI 3.0 / Swagger |

| 테스트 | pytest + pytest-django | Spring의 JUnit 대체 |

| 컨테이너 | Docker + docker-compose | 개발/배포 환경 통일 |

| 코드 품질 | black + isort + flake8 | 코드 포매터/린터 |

