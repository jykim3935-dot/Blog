# 아크릴 테크블로그 — 일일 글감 추천 에이전트

매일 **외신·AI 권위 커뮤니티·Reddit·arXiv·MLPerf·NVIDIA 등 빅테크 블로그**, 그리고
**내가 직접 넣은 소스 URL**을 수집·분석해서, 아크릴(Acryl) 테크블로그에 쓰면 좋을
**글감(주제)을 매일 추천**해 주는 에이전트입니다.

분석은 **Claude API(`claude-opus-4-8`)**가 담당하고, 결과는 `reports/` 폴더에
날짜별 Markdown 리포트로 저장됩니다. **GitHub Actions가 매일 자동 실행**합니다.

---

## 동작 방식

```
수집(collectors) → 중복 제거(dedup) → Claude 분석(analyzer) → Markdown 리포트(report)
```

1. **수집** — RSS 피드, arXiv API, Reddit/Hacker News 공개 API, 사용자 지정 URL에서 항목을 모읍니다.
2. **중복 제거** — 과거에 추천한 URL은 `reports/seen.json`에 기록해 같은 주제 반복을 줄입니다.
3. **분석** — 키워드로 1차 추림 → Claude가 아크릴 관심분야와의 관련도 기준으로 주제를 선별하고 기획안을 작성합니다.
4. **리포트** — `reports/YYYY-MM-DD.md`로 저장하고 `reports/README.md` 인덱스를 갱신합니다.

---

## 빠른 시작 (로컬 실행)

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-ant-..."
python -m src.main
```

실행이 끝나면 `reports/<오늘날짜>.md` 가 생성됩니다.

---

## 자동 실행 (GitHub Actions)

`.github/workflows/daily-topics.yml` 이 매일 **KST 오전 8시**에 자동 실행됩니다.

**필요한 설정 — API 키 등록 (1회):**

1. GitHub 저장소 → **Settings → Secrets and variables → Actions**
2. **New repository secret** 클릭
3. 이름 `ANTHROPIC_API_KEY`, 값에 Anthropic API 키 입력 후 저장

이후 매일 자동으로 리포트가 생성되어 저장소에 커밋됩니다.
수동으로 돌려보려면 **Actions 탭 → "일일 글감 추천" → Run workflow** 에서 실행할 수 있고,
이때 추가 분석할 URL을 쉼표로 구분해 넣을 수도 있습니다.

---

## 배포 (Cafe24 호스팅)

생성된 리포트(`reports/` 의 HTML)를 카페24 호스팅으로 **FTP 자동 배포**합니다.
`reports/` 가 갱신되면 `.github/workflows/deploy-cafe24.yml` 이 실행돼 파일을 올립니다.

**필요한 설정 — GitHub Secret 등록 (1회):**
Settings → Secrets and variables → Actions 에서 아래를 추가하세요.

| 이름 | 값 | 비고 |
| --- | --- | --- |
| `CAFE24_FTP_SERVER` | `naace1.mycafe24.com` | FTP 호스트 |
| `CAFE24_FTP_USERNAME` | 카페24 FTP 아이디 | |
| `CAFE24_FTP_PASSWORD` | 카페24 FTP 비밀번호 | **채팅에 붙여넣지 말 것** |
| `CAFE24_FTP_DIR` | `/www/` (선택) | 웹 루트가 다르면 지정, 끝에 `/` 필수 |
| `CAFE24_FTP_PROTOCOL` | `ftp` (선택) | FTPS 사용 시 `ftps` |
| `CAFE24_FTP_PORT` | `21` (선택) | |

등록 후에는 리포트가 만들어질 때마다 자동 업로드되며,
**Actions → "Cafe24 FTP 배포" → Run workflow** 로 수동 배포도 됩니다.
사이트의 모든 링크는 상대경로라 어떤 경로(루트/하위폴더)에 올려도 동작합니다.

---

## 설정 커스터마이즈

모든 설정은 `config/` 폴더에 있습니다. 코드를 건드릴 필요가 없습니다.

| 파일 | 용도 |
| --- | --- |
| `config/profile.yaml` | 아크릴 회사 소개, **관심 분야**, 키워드, 제외 주제, 하루 추천 개수, 톤/독자 |
| `config/sources.yaml` | RSS 피드, arXiv 카테고리, Reddit 서브레딧, HN 검색어, **내 소스 URL** |

### 내가 보고 싶은 소스 URL 추가하기

다음 세 가지 방법 중 아무거나:

1. `config/sources.yaml` 의 `custom_urls` 리스트에 추가
2. `config/my_sources.txt` 파일을 만들어 **한 줄에 URL 하나씩** 적기
3. Actions 수동 실행 시 `extra_urls` 입력란에 쉼표로 구분해 입력

일반 웹페이지면 제목/설명을 추출하고, RSS 피드 주소면 항목들을 가져옵니다.

### 추천 방향 바꾸기

`config/profile.yaml` 의 `focus_areas`(핵심 분야)와 `keywords`(가산점 키워드)를
회사 상황에 맞게 고치면 추천 주제의 결이 바뀝니다.
`topics_per_day` 로 하루 추천 개수를, `avoid` 로 거를 주제를 조정합니다.

---

## 프로젝트 구조

```
.
├── config/
│   ├── profile.yaml          # 아크릴 관심분야 / 키워드 / 톤
│   └── sources.yaml          # 수집 소스 정의
├── src/
│   ├── main.py               # 엔트리포인트
│   ├── config.py             # 설정 로딩
│   ├── util.py               # HTTP / HTML / 날짜 유틸
│   ├── dedup.py              # 중복 방지
│   ├── analyzer.py           # Claude 분석
│   ├── report.py             # Markdown 생성
│   └── collectors/           # 소스별 수집기
│       ├── rss.py            # 외신 + 빅테크 블로그
│       ├── arxiv.py          # arXiv 논문
│       ├── reddit.py         # Reddit 커뮤니티
│       ├── hackernews.py     # Hacker News
│       └── custom.py         # 사용자 지정 URL
├── reports/                  # 생성되는 일일 리포트
├── .github/workflows/
│   └── daily-topics.yml      # 매일 자동 실행
└── requirements.txt
```

---

## 비용 메모

하루 1회 실행, 항목 100여 건 분석 기준으로 `claude-opus-4-8` 입력/출력 토큰이
소량 사용됩니다. 비용을 더 줄이고 싶으면 워크플로/환경변수에서
`MODEL=claude-sonnet-4-6` 으로 바꾸면 됩니다.
