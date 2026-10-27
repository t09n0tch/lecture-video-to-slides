# 처리 절차와 데이터 형식

## 파일 배치

작업 공간 안에 영상별 디렉터리를 만들고 해당 디렉터리에서 상대 경로를 사용한다.

```text
work/lecture/
  inspection/       메타데이터, 전환 후보, 검토용 이미지
  slides/           최종 선택한 원본 화면 PNG
  audio/            전사용 오디오와 구간 재전사
  transcript/       타임스탬프 전사
  manifest.json     원본 화면과 구간의 대응
  notes.json        편집 가능한 해설
  build/            저작 코드, 렌더링, 검수 기록
```

입력 원본은 그대로 두고 결과물을 별도 경로에 쓴다. 모델·폰트·런타임을 스킬 폴더로 복사하지 않는다. 샘플 화면의 크기를 줄일 수 있지만 최종 원본 화면은 영상의 실제 해상도로 추출한다.

## 후보 탐색과 수동 확인

`scripts/media.py --help`와 각 하위 명령의 도움말에서 현재 인수를 확인한다. `probe`는 메타데이터, `scenes`는 전환 후보 시각, `frame`은 지정 시각의 PNG, `audio`는 모노 16kHz WAV를 만든다. 경로에 공백이나 한글이 있으면 셸에서 인수를 따옴표로 감싼다.

아래 예시에서 `SKILL_DIR`은 이 스킬의 설치 디렉터리이다. `--work-dir`와 `--overwrite`는 하위 명령 **앞**에 놓는다. 상대 출력 경로는 `--work-dir` 아래로 해석한다.

```bash
python "$SKILL_DIR/scripts/media.py" --work-dir work/lecture probe "lecture.mp4" --output inspection/probe.json
python "$SKILL_DIR/scripts/media.py" --work-dir work/lecture scenes "lecture.mp4" --output inspection/scenes.json --threshold 0.08
python "$SKILL_DIR/scripts/media.py" --work-dir work/lecture frame "lecture.mp4" --seconds 12.5 --output slides/slide-01.png
python "$SKILL_DIR/scripts/media.py" --work-dir work/lecture audio "lecture.mp4" --output audio/full.wav
```

`scenes` 출력의 `candidate_times_seconds`는 시작 시각 0을 포함한 후보 목록이다. `candidate_count`를 최종 장수로 사용하지 않는다. 선택한 프레임 시각이 영상 길이를 벗어나거나 오디오 스트림이 없으면 원인을 확인한다. 기존 출력 대체는 확인한 경로에만 `--overwrite`로 수행한다.

크롭은 `WIDTH:HEIGHT:X:Y` 순서이다. 첫 영상의 크롭 좌표를 다음 영상에 재사용하지 않는다. 전환 탐색 점수 0.08은 시작값으로 쓸 수 있으나 화면 구성과 애니메이션에 따라 조정한다. 낮은 점수는 필기나 포인터도 더 많이 검출한다. 모든 프레임을 저장할 필요 없이 후보 시각과 고정 간격 샘플을 조합한다.

화면 전환 직전의 프레임이 녹화 도구나 마우스 메뉴를 포함할 수 있으므로 필요하면 수초 앞도 비교한다. 시간 순서가 뒤섞인 반복 페이지는 동일한 원본 페이지로 묶되, 다른 필기 상태가 정보를 추가하는지 확인한다. 내용이 같은 이미지 두 장이 있더라도 원본 등장 구간 정보는 모두 유지한다.

## 선택한 페이지의 manifest 예시

다음은 파일 형식의 예시이다. 실제 시간과 페이지 수를 영상에서 확인해 채운다. `path`는 manifest 파일의 위치를 기준으로 해석한다. 입력 원본 경로가 필요하면 비공개 작업 manifest에만 추가한다.

```json
{
  "source_file": "lecture.mp4",
  "duration_seconds": 600.0,
  "crop": {"width": 1440, "height": 1080, "x": 240, "y": 0},
  "slides": [
    {
      "index": 1,
      "source_page_id": "page-01",
      "state_label": "최종 필기",
      "title": "원본 페이지 제목",
      "segments": [{"start": 0.0, "end": 80.0}, {"start": 105.0, "end": 110.0}],
      "chosen_frame_seconds": 78.5,
      "path": "slides/slide-01.png",
      "content_slide": true,
      "annotation_notes": "추가된 손필기와 순차 표시가 완성된 화면"
    }
  ]
}
```

`segments`는 페이지가 실제로 표시된 구간이다. 두 구간 사이를 한 연속 구간처럼 기록하지 않는다. 페이지를 넘긴 뒤에도 설명이 이어지는 경우 별도의 발화 구간을 노트에 적을 수 있다. 마지막 종료 인사 화면을 본문 장수에 자동 포함하지 않는다.

같은 원본 페이지에서 서로 다른 필기나 중간 단계 두 장을 보존해야 하면 `slides` 항목을 두 개 만든다. 출력 페이지마다 고유한 `index`를 부여하고 동일한 `source_page_id`로 연결한다. 각 항목의 `state_label`, `chosen_frame_seconds`, `path`를 따로 기록하며, `segments`에는 해당 상태가 실제로 표시된 구간을 넣는다. 해설도 출력 `index`별로 작성해 의미 있는 중간 상태를 중복으로 제거하지 않는다.

## 예제와 보충 설명 구성

### 문제와 풀이의 짝

문제 풀이를 요구하는 문항과 설명용 예시를 구분한다. 예제라는 제목만 보고 완성 반응식마다 문제 페이지를 추가하지 않는다. 직접 풀 문항은 정답 공개 전의 첫 화면과 풀이·필기가 끝난 화면을 각각 확보해 **문제 → 풀이** 순서로 놓는다. 문제 화면은 모든 문항·반응물·조건이 나타난 상태인지 확인한다.

문제 페이지에는 정답 이름이나 구체적인 풀이 단계를 넣지 않는다. 풀이 페이지의 복제본으로 만들었다면 텍스트 본문뿐 아니라 발표자 노트, 이미지 대체 텍스트, 숨긴 객체도 교체·삭제해 정답이 남지 않게 한다. 풀이 페이지에서는 최종 필기와 원본 정답을 유지하고 해설을 덧붙인다.

문제와 정답이 처음부터 함께 보이면 원본 안에서 문제 영역만 정확히 발췌할 수 있는지 확인한다. 문항·구조·시약·조건을 모두 보존한 발췌는 `원본 문제 영역 발췌`로 표시하고 출처를 남긴다. 화학 결합·전하·수식을 지우거나 다시 생성해 정답 공개 전 프레임처럼 꾸미지 않는다. 문제를 온전히 분리할 수 없으면 원본을 보존하고, 가능한 문제 제시 방식과 그 제한을 사용자에게 설명한다.

두 상태는 같은 `source_page_id`를 사용한다. 예를 들면 다음과 같이 출력 페이지를 구별할 수 있다. 아래는 필드 대응을 보이는 일부 예시이며, 각 항목에 실제 `segments`와 `path`도 기록한다.

```json
[
  {"index": 7, "source_page_id": "example-a", "kind": "question", "state_label": "정답 공개 전", "chosen_frame_seconds": 210.0},
  {"index": 8, "source_page_id": "example-a", "kind": "solution", "state_label": "최종 필기와 정답", "chosen_frame_seconds": 245.5}
]
```

출력 `index`는 보충 페이지까지 포함해 고유하게 부여한다. 각 문제·풀이의 해설도 해당 출력 `index`에 연결한다.

### 보충 설명의 내용과 근거

먼저 학습자가 어려워할 연결 고리를 고른다. 예를 들어 반응 전체 지도, 기호의 뜻, 조건에 따른 변화 비교, 문제를 푸는 순서, 답의 단위·원자 수 검산 등이다. 원본의 긴 문장을 다시 나열하기보다 한 개념을 짧은 설명과 필요한 식·표로 풀어 쓴다. 후속 예제를 위한 일반적인 원리는 설명하되, 해당 문항의 정답을 예제보다 앞에서 공개하지 않는다.

- **원본과 연결:** 화면과 발화를 바탕으로 정리하고, 보충임을 본문에 표시한다. 관련 원본 페이지와 영상 구간은 근거로 연결한다. 필요한 외부 사실은 신뢰할 수 있는 자료로 확인하고 출처를 발표자 노트에 넣는다.
- **초심자에게 필요한 순서:** 낯선 기호와 용어를 먼저 설명하고, 무엇을 확인해 어떻게 판단하는지 보여 준다. 최종 답만 추가하는 방식은 피한다.
- **적용 범위:** 원본의 조건·예외를 보존한다. 특정 기질·실험 조건에서의 결과를 모든 경우에 일반화하거나 생성물 조립법을 실제 반응 기전과 혼동하지 않는다.
- **읽을 수 있는 분량:** 우측 강의노트는 핵심 해설로 유지하고, 길어지는 개념 설명은 보충 페이지로 옮긴다. 작은 글씨로 원본이나 해설을 압축하지 않는다.

보충 항목은 원본 화면 항목과 구별해 기록한다. 예를 들어 `kind: "supplement"`, 고유한 출력 `index`, `related_source_page_ids`, `basis_segments`, `title`을 둘 수 있다. `basis_segments`는 설명의 근거 구간이며 보충 페이지 자체가 영상에 등장한 구간이 아니다. 보충에는 원본 대표 프레임인 것처럼 `chosen_frame_seconds`를 만들어 넣지 않는다.

기존 자료를 보완하는 경우 승인된 원본 이미지·필기·강의노트를 재사용한다. 바뀐 예제·보충 페이지를 검토하면서 전체 원본의 누락 여부도 확인한다. 원본 내용 장수, 문제로 추가한 장수, 보충 장수를 따로 세면 누락과 중복을 확인하기 쉽다.

## 전사

`scripts/transcribe_local.py --help`를 확인해 음성 파일, 모델 경로 또는 저장소 ID, 출력 경로를 지정한다. 발화 언어의 기본값은 자동 감지이며, 알고 있으면 `--language ko` 또는 `--language en` 등으로 지정한다. 이 값은 한국어 해설 작성 여부와 별개다. Apple Silicon과 MLX Whisper가 준비된 환경용 도우미다. 전사 엔진이 없으면 기존 런타임을 확인하고 필요한 경우 작업 폴더의 격리 환경에 설치한다. 현재 세션의 번들 의존성을 수정하지 않는다.

모델을 처음 받는 작업에는 다운로드가 필요할 수 있으나 음성 인식은 로컬에서 한다. 모델 저장소의 이용 조건과 실행 환경을 확인한다. 다른 운영체제에서는 사용 가능한 로컬 Whisper 계열 엔진으로 타임스탬프 전사를 얻어 같은 방식으로 대조할 수 있다.

재전사는 문제 구간 앞뒤 문맥을 조금 포함해 오디오를 잘라 수행한다. `--offset`에는 잘라낸 오디오가 **원본 영상에서 시작한 초**를 넣고, `--independent`를 사용해 앞선 전사의 반복 오류가 이어지지 않게 한다. 원래 전사는 보관하고 검토한 구간만 통합본에 교체한다. 구간 경계의 중복·누락과 시간의 단조 증가를 확인한다.

```bash
python "$SKILL_DIR/scripts/transcribe_local.py" work/lecture/audio/full.wav --model "/path/to/local-model" --output work/lecture/transcript/raw.json --work-dir work/lecture/cache --language ko
python "$SKILL_DIR/scripts/media.py" --work-dir work/lecture audio "lecture.mp4" --start 120 --duration 40 --output audio/retry.wav
python "$SKILL_DIR/scripts/transcribe_local.py" work/lecture/audio/retry.wav --model "/path/to/local-model" --output work/lecture/transcript/retry.json --work-dir work/lecture/cache --language ko --offset 120 --independent
```

위의 `120`과 `40`은 명령 형식의 예시이며, 실제로 확인한 구간으로 바꾼다. 재전사에서도 본 전사와 같은 발화 언어를 사용한다. 예시의 `ko`는 한국어 음성인 경우다.

전사 JSON은 `segments`의 `start`, `end`, `text`와 `provenance`를 포함하며, 같은 이름의 TXT도 생성한다. `--offset`을 적용한 시간은 원본 영상 기준 초이다. `automatic_transcript: true`, `human_verified: false`는 자동 전사를 사실 검증 완료본으로 오인하지 않도록 남긴다. 기본 덮어쓰기 거부는 JSON과 TXT 모두에 적용된다.

## 해설 데이터 예시

```json
{
  "slides": [
    {
      "index": 1,
      "title": "한국어 주제",
      "blocks": [
        {"heading": "핵심 원리", "body": "영상과 원본 화면에서 확인한 내용을 짧게 설명한다."},
        {"heading": "필기 포인트", "body": "원본 손필기의 의미를 정확하게 정리한다."}
      ],
      "speakerNotes": "자세한 강의 설명과 필요한 보충. 강사의 발언과 작성자의 보충을 구별한다.",
      "timeRange": "00:00–01:20"
    }
  ]
}
```

`index`로 원본 페이지와 해설을 연결한다. `timeRange`는 페이지 하단에 표시할 대표 구간이다. 모든 재등장 구간은 발표자 노트에 기록한다. 출처에는 사용자가 제공한 파일명을 쓰고, 강사 이름·기관·교재명은 확인되었을 때만 넣는다.
