# 게임 배포 가이드 (pygbag → Render Static Site)

## 폴더 구조
```
game/
├── main.py
├── requirements.txt
└── README.md
```

> ⚠️ 원본 코드에서 recall.png, purse.png, blink.png를 사용했는데,
> pygbag 웹 환경에서는 이미지 파일을 같은 폴더에 넣으면 그대로 사용 가능합니다.
> 현재 main.py는 이미지 없이도 동작하도록 도형으로 대체했습니다.
> 이미지를 쓰고 싶다면 아래 "이미지 사용법" 섹션을 참고하세요.

---

## 1단계: pygbag으로 빌드

### 설치
```bash
pip install pygbag
```

### 빌드
```bash
# game 폴더 안에서 실행
pygbag --build game/
```

빌드가 완료되면 `game/build/web/` 폴더가 생깁니다.

---

## 2단계: Render에 배포

### 방법 A: GitHub 연동 (추천)

1. `game/build/web/` 폴더 내용을 GitHub 레포에 올리기
2. [render.com](https://render.com) 접속 → New → Static Site
3. GitHub 레포 연결
4. 설정:
   - **Build Command**: (비워두기)
   - **Publish Directory**: `.` (루트)
5. Deploy 클릭

### 방법 B: 수동 업로드

Render Static Site에서 "Manual Deploy" 옵션으로
`build/web/` 폴더를 직접 드래그 업로드

---

## 이미지 사용법 (선택사항)

recall.png, purse.png, blink.png를 쓰고 싶다면:

1. 이미지 파일을 `game/` 폴더 안에 넣기
2. main.py 상단의 이미지 로드 부분을 아래로 교체:

```python
# pygbag에서는 asyncio로 감싸야 이미지 로드 가능
import asyncio

async def load_assets():
    global blink_img, recall_img, purse_img
    recall_img = pygame.image.load("recall.png")
    purse_img  = pygame.image.load("purse.png")
    blink_img  = pygame.image.load("blink.png")
    blink_img  = pygame.transform.scale(blink_img,  (24, 24))
    recall_img = pygame.transform.scale(recall_img, (24, 24))
    purse_img  = pygame.transform.scale(purse_img,  (24, 24))
    await asyncio.sleep(0)
```

그리고 `main()` 함수 시작 부분에 `await load_assets()` 추가

---

## 변경된 사항 요약

| 원본 | pygbag 버전 |
|------|-------------|
| `while True:` 루프 | `async def main():` + `await asyncio.sleep(0)` |
| `pygame.time.delay(2000)` | `await asyncio.sleep(2)` |
| `pygame.image.load(...)` | Surface로 대체 (이미지 없이 동작) |
| `pygame.quit(); sys.exit()` | `return` (함수 종료) |

---

## 로컬 테스트

빌드 전에 로컬에서 테스트하려면:
```bash
pygbag game/
```
브라우저에서 `http://localhost:8000` 접속
