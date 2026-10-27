# lecture-video-to-slides

강의 녹화 영상의 **원본 슬라이드와 손필기를 보존하고, 한국어 강의 해설을 덧붙인 PPTX·PDF를 만드는 Codex 스킬**입니다.

원본 반응식·수식·도표는 이미지로 유지하고, 해설은 편집 가능한 텍스트로 추가합니다. 각 페이지의 영상 시각과 PPTX 발표자 노트로 원본 강의를 다시 확인할 수 있습니다.

## 무엇을 하나요?

- 실제 페이지와 전환 후보를 구별하고 반복 등장 페이지를 정리합니다.
- 완성된 필기·애니메이션을 추출하며, 필요한 중간 단계도 보존합니다.
- 복습용 예제는 정답 공개 전 문제와 최종 필기·정답·해설을 연속된 두 페이지로 구성합니다.
- 이해에 필요한 개념·풀이 순서·비교·검산을 별도 보충 설명으로 연결합니다.
- 실제 음성 전사와 화면을 대조해 핵심 설명을 작성합니다.
- 입력 음성의 언어와 해설 언어를 구분합니다. 영어 강의를 한국어 자료로 정리할 수 있습니다.
- 최종 PPTX와 PDF를 각각 렌더링해 잘림·겹침·기호 표시를 확인합니다.

이 저장소는 **Codex용 작업 지침과 미디어·전사 도우미**를 제공합니다. 슬라이드 선택, 해설 작성, PPTX·PDF 저작은 Codex가 수행하며, 해당 세션에서 사용할 수 있는 프레젠테이션·PDF 저작 및 렌더링 도구가 필요합니다. 두 Python 도우미만으로 전체 자료가 자동 완성되는 구성은 아닙니다.

## 설치

Codex의 스킬 폴더로 저장소를 복제합니다. `CODEX_HOME`이 설정되어 있으면 그 경로를 사용하고, 기본 경로는 `~/.codex/skills`입니다.

```bash
git clone https://github.com/t09n0tch/lecture-video-to-slides.git \
  "${CODEX_HOME:-$HOME/.codex}/skills/lecture-video-to-slides"
```

이미 같은 이름의 스킬이 설치되어 있으면 기존 폴더를 덮어쓰지 말고 설치 내용을 먼저 확인하세요. 이번 배포 버전을 고정하려면 위 명령의 `git clone` 뒤에 `--branch v0.2.0 --depth 1`을 추가할 수 있습니다.

Git으로 설치한 기존 사용자는 해당 스킬 폴더의 로컬 변경을 확인한 뒤 `git pull --ff-only`로 업데이트할 수 있습니다. ZIP으로 설치했다면 새 버전을 별도 폴더에 풀어 비교한 후 교체합니다.

Codex의 `$skill-installer`에 다음과 같이 요청해 설치할 수도 있습니다.

```text
$skill-installer
t09n0tch/lecture-video-to-slides 저장소의 루트 경로(.)를
lecture-video-to-slides 이름으로 설치해줘.
```

설치 후 다음 대화 턴에서 스킬을 사용합니다.

## 사용

강의 영상을 첨부하거나 접근 가능한 로컬 파일 경로를 지정하고 요청합니다.

```text
$lecture-video-to-slides
이 영상으로 원본 슬라이드와 필기를 보존하고,
한국어 강의노트와 영상 시각을 덧붙인 PPTX와 PDF를 만들어줘.
예제는 문제 다음에 필기·정답·해설을 배치하고, 어려운 개념은 보충 설명으로 풀어줘.
```

요청에 맞춰 언어·분량·구성을 바꿀 수 있습니다.

```text
$lecture-video-to-slides
이 영어 강의를 한국어 복습자료로 정리해줘.
화학 구조식은 원본으로 유지하고, 중요한 중간 필기도 포함해줘.
```

기본 구성은 원본 화면, 한국어 핵심 해설, 영상 시각입니다. 자세한 설명은 PPTX 발표자 노트에 들어갑니다. PDF에서 보아야 할 핵심 해설은 페이지 본문에도 담습니다. 원본 이미지 속 글자와 구조식은 개별 편집 대상이 아니며, 추가한 해설은 편집 가능합니다.

복습용 자료의 문제 페이지에는 정답을 먼저 넣지 않고, 다음 풀이 페이지에 최종 필기와 해설을 둡니다. 보충 페이지는 `보충 설명`으로 표시해 강의 원본과 구별하고, 관련 원본 페이지와 구간을 연결합니다. 예제·보충 페이지 수는 영상 내용과 요청에 맞춰 정합니다. 원본 추출만 요청하거나 구성·장수를 지정하면 그 요청을 우선합니다. 본문·풀이가 없는 마지막 종료 인사 화면은 기본적으로 제외합니다.

## 실행 환경

| 용도 | 필요한 환경 |
| --- | --- |
| 스킬 실행 | 로컬 영상 파일을 읽을 수 있는 Codex 환경 |
| 미디어 처리 | Python 3.10 이상, PATH에 있는 `ffmpeg`와 `ffprobe` |
| PPTX·PDF 제작 | 세션의 프레젠테이션·PDF 저작 및 렌더링 도구, 한글·기호를 지원하는 글꼴 |
| 포함된 로컬 전사 도우미 | Apple Silicon Mac, Metal 접근 권한, `mlx-whisper`와 MLX 호환 음성 모델 |

`media.py`는 Python 표준 라이브러리와 FFmpeg/FFprobe를 사용합니다. `transcribe_local.py`는 선택 사항이며 다른 운영체제에서는 사용 가능한 별도 로컬 음성 인식 엔진을 사용할 수 있습니다.

MLX 전사가 필요한 경우 작업 폴더 안의 가상환경에 설치할 수 있습니다. 다음 버전으로 실제 음성 전사를 확인했습니다.

```bash
python3 -m venv work/asr-env
work/asr-env/bin/python -m pip install "mlx-whisper==0.4.3"
```

모델을 처음 받는 경우 다운로드가 필요합니다. 포함된 전사 도우미는 음성을 로컬에서 처리하며, 모델 저장소 ID를 지정하면 모델 파일을 다운로드할 수 있습니다.

## 도우미 직접 실행

아래 명령은 저장소 폴더에서 실행합니다. `--work-dir`와 `--overwrite`는 `media.py`의 하위 명령 **앞**에 놓습니다. 상대 출력 경로는 `--work-dir` 안에서 해석합니다.

```bash
python3 scripts/media.py --work-dir work/lecture probe "lecture.mp4" \
  --output inspection/probe.json

python3 scripts/media.py --work-dir work/lecture scenes "lecture.mp4" \
  --threshold 0.08 --output inspection/scenes.json

python3 scripts/media.py --work-dir work/lecture frame "lecture.mp4" \
  --seconds 12.5 --output slides/slide-01.png

python3 scripts/media.py --work-dir work/lecture audio "lecture.mp4" \
  --output audio/full.wav
```

전환 후보 목록은 최종 슬라이드 수가 아닙니다. `--crop WIDTH:HEIGHT:X:Y`는 화면을 확인한 뒤 선택적으로 지정합니다. 프레임은 원본 해상도 PNG, 오디오는 16kHz 모노 WAV로 저장합니다.

로컬 MLX 모델이 준비되어 있다면 다음과 같이 전사합니다. `--language` 기본값은 자동 감지입니다.

```bash
work/asr-env/bin/python scripts/transcribe_local.py work/lecture/audio/full.wav \
  --model "/path/to/local-mlx-model" \
  --output work/lecture/transcript/raw.json \
  --work-dir work/lecture/cache
```

JSON과 같은 이름의 TXT를 함께 저장합니다. 부분 재전사에는 `--independent`와 원본 시작 초인 `--offset`을 사용합니다. 자세한 데이터 형식과 절차는 [workflow.md](references/workflow.md), 출력 검수 기준은 [quality.md](references/quality.md)를 참고하세요.

## 데이터와 배포 범위

배포 파일에는 스킬 지침과 도우미 코드만 포함합니다. 강의 영상, 슬라이드 캡처, 녹취, 생성된 강의자료, 모델 가중치, 폰트 파일은 포함하지 않습니다. 작업 중 생성되는 경로는 `.gitignore`로 제외합니다.

MIT 라이선스는 이 저장소의 코드와 문서에 적용됩니다. 입력 강의자료, 별도 다운로드 모델, 글꼴 등 제3자 자료의 이용 조건은 해당 자료의 조건을 따릅니다.

## 저장소 구성

```text
SKILL.md                      Codex 작업 지침
agents/openai.yaml            스킬 표시 정보와 기본 호출 예시
scripts/media.py              영상 정보·전환 후보·프레임·오디오 추출
scripts/transcribe_local.py   선택적 로컬 MLX Whisper 전사
references/workflow.md        처리 절차와 데이터 형식
references/quality.md         원본 보존·글꼴·PPTX·PDF 검수 기준
```

## 라이선스

[MIT](LICENSE)
