# 📊 Mini Ad Manager

> Django 미니 광고 관리 플랫폼

## 프로젝트 개요

**Ad Server + 캠페인 관리 시스템**을 Django로 직접 구현한 포트폴리오 프로젝트입니다.
광고주가 캠페인을 등록하고, 광고 소재를 업로드하고, 노출/클릭 통계를 확인할 수 있는 관리 플랫폼에
**타겟팅 기반 Ad Serving API**까지 포함합니다.

---

## 기술 스택

| 분류 | 기술 |
|---|---|
| Backend | Python 3.11+, Django 5.x, Django REST Framework |
| 인증 | JWT (djangorestframework-simplejwt) |
| 데이터베이스 | PostgreSQL 16 |
| 캐시/브로커 | Redis 7 |
| 비동기 | Celery 5.x + Celery Beat |
| API 문서 | drf-spectacular (Swagger UI) |
| 테스트 | pytest + pytest-django |
| 컨테이너 | Docker + Docker Compose |

---

## 아키텍처

```
Client (Browser)
    │
    ├── Dashboard UI (Django Template + Chart.js)
    └── API Layer (DRF ViewSet + Serializer)
            │
            ├── apps/accounts/   # 광고주 인증/관리
            ├── apps/campaigns/  # 캠페인/광고/소재 CRUD
            ├── apps/serving/    # Ad Serving + 트래킹
            └── apps/reports/    # 통계 리포트
                    │
                    ├── PostgreSQL  (영구 저장)
                    ├── Redis       (캐시 + Frequency Cap)
                    └── Celery Beat (일별 통계 집계)
```

---

## 핵심 기능

### 1. 광고 서빙 파이프라인 (`/api/v1/serve/`)
외부 매체가 호출하면 7단계 필터링으로 최적의 광고를 선택하여 JSON으로 반환합니다.

```
슬롯 확인 → 상태/기간/예산 필터 → 타겟팅(시간대/디바이스) → Frequency Cap → 가중치 랜덤 선택
```

### 2. 이벤트 트래킹
- **노출**: 1x1 투명 GIF 픽셀 → EventLog 기록 → Redis INCR
- **클릭**: 302 리다이렉트 → EventLog 기록 → CPC 과금 처리

### 3. Redis 활용
- 실시간 노출/클릭 카운터 (INCR)
- Frequency Capping (IP 기반, TTL 24h)
- 광고 후보 캐싱 (TTL 5분)
- 일일 예산 소진액 추적

### 4. Celery 비동기 처리
- **매일 새벽 1시**: EventLog → DailyReport 집계
- **매주 일요일**: 90일 이전 이벤트 로그 정리

---

## 빠른 시작 (Docker)

```bash
# 1. 환경변수 설정 (필요시)
cp .env.example .env

# 2. 컨테이너 실행
docker compose up -d

# 3. 샘플 데이터 생성
docker compose exec web python manage.py seed_data

# 4. 접속
# 대시보드: http://localhost:8000/
# Swagger:  http://localhost:8000/api/docs/
# Admin:    http://localhost:8000/admin/
```

**샘플 계정**
- 관리자: `admin` / `admin1234`
- 광고주: `advertiser01~05` / `test1234!`

---

## 로컬 개발 환경 (venv)

```bash
python -m venv venv
venv/Scripts/activate  # Windows
pip install -r requirements/local.txt

python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

---

## API 엔드포인트

| Method | Endpoint | 설명 |
|---|---|---|
| POST | `/api/v1/auth/token/` | JWT 로그인 |
| GET/POST | `/api/v1/campaigns/` | 캠페인 목록/생성 |
| POST | `/api/v1/campaigns/{id}/activate/` | 캠페인 활성화 |
| POST | `/api/v1/campaigns/{id}/pause/` | 캠페인 일시정지 |
| **GET** | **`/api/v1/serve/?slot=main_banner`** | **광고 서빙 (핵심)** |
| GET | `/api/v1/track/impression/{id}/` | 노출 트래킹 (1x1 GIF) |
| GET | `/api/v1/track/click/{id}/` | 클릭 트래킹 (302 redirect) |
| GET | `/api/v1/reports/dashboard/` | 대시보드 요약 |
| GET | `/api/v1/reports/campaign/{id}/` | 캠페인별 통계 |
| GET | `/api/v1/reports/export/` | CSV 다운로드 |

전체 문서: **[Swagger UI](/api/docs/)**

---

## Spring → Django 전환 경험

| Spring | Django | 비고 |
|---|---|---|
| `@Entity` | `models.Model` | Django ORM이 더 직관적 |
| `@RestController` | `ViewSet + Router` | DRF ViewSet = Controller |
| `@Service` | `services.py` | 관례적 분리, 강제 아님 |
| `application.yml` | `settings.py` | Python 파일로 설정 관리 |
| `Spring Security` | `DRF Permission + JWT` | 데코레이터 패턴 |
| `@Scheduled` | `Celery Beat` | 비동기 태스크 처리 |
| `JUnit` | `pytest-django` | fixture 방식이 더 유연 |

---

## 테스트

```bash
pytest tests/ -v
# 27개 테스트 전부 통과 (Redis 없이도 실행 가능)
```

---

## 프로젝트 구조

```
mini_ad_manager/
├── config/                  # 설정 (≈ application.yml)
│   ├── settings/
│   │   ├── base.py          # 공통 설정
│   │   ├── local.py         # 개발 환경
│   │   └── production.py    # 운영 환경
│   ├── urls.py
│   └── celery.py
├── apps/
│   ├── accounts/            # 광고주 인증/관리
│   ├── campaigns/           # 캠페인, 인벤토리, 광고, 소재
│   ├── serving/             # Ad Serving + 이벤트 트래킹
│   └── reports/             # 통계 집계 + 리포트 API
├── templates/dashboard/     # 대시보드 UI
├── tests/                   # pytest 테스트
├── docker-compose.yml
└── Dockerfile
```
