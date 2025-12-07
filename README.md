# 🎥 Chzzk Downloader

<div align="center">

**네이버 치지직(Chzzk) VOD와 클립을 다운로드할 수 있는 데스크톱 애플리케이션**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.6+-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)

[다운로드](#-다운로드) • [기능](#-주요-기능) • [사용법](#-사용-방법) • [개발](#-개발자-가이드)

</div>

---

## 📸 스크린샷

> 모던하고 직관적인 UI로 누구나 쉽게 사용할 수 있습니다.

## ✨ 주요 기능

- 🎨 **모던 GUI** - PyQt6 기반의 아름다운 다크 테마 인터페이스
- 🎥 **고화질 지원** - 최대 1080p 60fps 원본 화질 다운로드
- 🚀 **고속 다운로드** - yt-dlp 기반의 멀티스레드 다운로드
- 📦 **완벽한 재생** - MP4 포맷으로 자동 병합 (VLC, IINA 등 모든 플레이어 지원)
- 🍪 **연령 제한 컨텐츠** - 쿠키를 통한 성인 인증 영상 다운로드 지원
- 🖼️ **썸네일 표시** - 실제 영상 썸네일을 다운로드 목록에 표시
- 📊 **실시간 진행률** - 다운로드 속도, 진행률, 남은 시간 표시
- 🖥️ **크로스 플랫폼** - Windows, macOS, Linux 지원

## 📥 다운로드 및 설치

### 방법 1: Python으로 실행 (권장)

Python이 설치되어 있다면 소스 코드를 직접 실행할 수 있습니다.

#### 1. Python 설치 확인

```bash
python3 --version
# 또는
python --version
```

Python 3.8 이상이 필요합니다. 없다면 [python.org](https://www.python.org/downloads/)에서 다운로드하세요.

#### 2. 저장소 복제

```bash
git clone https://github.com/SamKSH/chzzkdownloader-gui.git
cd chzzkdownloader-gui
```

또는 ZIP 다운로드:
1. https://github.com/SamKSH/chzzkdownloader-gui 접속
2. 녹색 "Code" 버튼 → "Download ZIP"
3. 압축 해제 후 터미널에서 해당 폴더로 이동

#### 3. 의존성 설치

```bash
pip3 install -r requirements.txt
# 또는
pip install -r requirements.txt
```

**필요한 패키지:**
- PyQt6 (GUI 프레임워크)
- yt-dlp (다운로드 엔진)
- requests (HTTP 요청)

#### 4. 실행

```bash
python3 src/main.py
# 또는
python src/main.py
```

---

### 방법 2: 실행 파일 사용

Python 설치 없이 바로 사용하고 싶다면:

1. [Releases](https://github.com/SamKSH/chzzkdownloader-gui/releases) 페이지 접속
2. 최신 버전에서 OS에 맞는 파일 다운로드
   - **macOS**: `ChzzkDownloader-macOS.zip`
   - **Windows**: `ChzzkDownloader-Windows.zip` (GitHub Actions로 자동 빌드)
3. 압축 해제 후 실행

**macOS 보안 경고 해결:**
```bash
# 터미널에서 실행
xattr -cr ChzzkDownloader.app
```

또는 `시스템 환경설정` → `보안 및 개인 정보 보호` → `확인 없이 열기`

---

## 🎯 사용 방법

### 1. 프로그램 실행

```bash
python3 src/main.py
```

### 2. 기본 다운로드

1. **URL 입력**: 치지직 VOD 또는 클립 URL을 입력창에 붙여넣기
   - VOD 예시: `https://chzzk.naver.com/video/12345`
   - 클립 예시: `https://chzzk.naver.com/clips/abcde`

2. **정보 가져오기**: "정보 가져오기" 버튼 클릭
   - 영상 제목, 길이, 썸네일 표시
   - 사용 가능한 화질 목록 표시

3. **화질 선택**: 드롭다운에서 원하는 해상도 선택
   - 1080p 60fps (최고 화질)
   - 1080p
   - 720p
   - 480p
   - 360p

4. **다운로드**: "다운로드" 버튼 클릭
   - 실시간 진행률 표시
   - 다운로드 속도 표시
   - 남은 시간 표시

5. **완료**: 다운로드가 완료되면 "파일 열기" 버튼으로 바로 재생 가능

### 3. 연령 제한 컨텐츠 다운로드

일부 영상은 네이버 로그인이 필요합니다. 쿠키를 설정하면 다운로드할 수 있습니다.

#### 쿠키 찾는 방법

1. 브라우저에서 [네이버](https://www.naver.com)에 로그인
2. `F12` 키를 눌러 개발자 도구 열기
3. **Application** (또는 **애플리케이션**) 탭 클릭
4. 좌측 메뉴에서 **Cookies** → `https://naver.com` 선택
5. 목록에서 `NID_AUT`와 `NID_SES` 찾기
6. **Value** (값) 복사

#### 쿠키 설정

1. 애플리케이션 메뉴에서 **파일** → **설정** 클릭
2. **인증** 탭으로 이동
3. `NID_AUT`와 `NID_SES` 값 붙여넣기
4. **저장** 클릭

### 4. 다운로드 파일 위치

- **기본 경로**: `~/Downloads/ChzzkDownloads`
- **파일명 형식**: `영상제목_1080p.mp4`
- **설정 변경**: 메뉴 → 파일 → 설정 → 일반 탭

---

## 💡 사용 팁

### 최고 화질로 다운로드

- 항상 **1080p 60fps** 또는 **1080p** 선택
- 원본 화질 그대로 다운로드됨
- 모든 플레이어에서 재생 가능 (VLC, IINA, QuickTime 등)

### 여러 영상 다운로드

1. 첫 번째 영상 다운로드 시작
2. 다운로드 진행 중에도 새 URL 입력 가능
3. 순차적으로 다운로드됨

### 다운로드 속도 향상

- 안정적인 인터넷 연결 사용
- VPN 사용 시 비활성화
- 다른 다운로드 프로그램 종료

---

## 🛠️ 개발자 가이드

### 프로젝트 구조

```
chzzk-downloader-gui/
├── src/
│   ├── main.py              # 애플리케이션 진입점
│   ├── ui/                  # UI 컴포넌트
│   │   ├── main_window.py   # 메인 윈도우
│   │   ├── download_item.py # 다운로드 아이템 위젯
│   │   ├── settings_dialog.py # 설정 다이얼로그
│   │   └── styles.py        # 스타일시트
│   └── core/                # 핵심 로직
│       ├── chzzk_api.py     # Chzzk API 클라이언트
│       ├── downloader.py    # 다운로드 매니저
│       └── config.py        # 설정 관리
├── requirements.txt         # Python 의존성
├── build.spec              # PyInstaller 설정
└── README.md
```

### 로컬 개발 환경 설정

```bash
# 가상환경 생성 (선택사항)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 개발 모드 실행
python src/main.py
```

### 실행 파일 빌드

#### Windows

```bash
pyinstaller build.spec
# 출력: dist/ChzzkDownloader.exe
```

#### macOS

```bash
pyinstaller build.spec
# 출력: dist/ChzzkDownloader.app

# DMG 생성 (선택사항)
create-dmg \
  --volname "Chzzk Downloader" \
  --window-size 600 400 \
  --icon-size 100 \
  --app-drop-link 450 150 \
  ChzzkDownloader.dmg \
  dist/ChzzkDownloader.app
```

---

## 🐛 문제 해결

### "Python not found" 오류

- Python 3.8 이상이 설치되어 있는지 확인
- 터미널에서 `python --version` 또는 `python3 --version` 실행

### 다운로드가 멈추거나 실패

- 인터넷 연결 확인
- 연령 제한 영상의 경우 쿠키 설정 필요
- VPN 사용 시 비활성화 후 재시도

### macOS에서 "확인되지 않은 개발자" 경고

1. `시스템 환경설정` → `보안 및 개인 정보 보호`
2. `확인 없이 열기` 버튼 클릭

### Windows에서 실행 파일이 바이러스로 감지됨

- 오탐지입니다. PyInstaller로 빌드된 파일은 종종 오탐지됩니다.
- Windows Defender에서 예외 추가하거나 소스 코드를 직접 실행하세요.

---

## 📝 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

---

## 🙏 기여

버그 리포트, 기능 제안, Pull Request는 언제나 환영합니다!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## ⚠️ 면책 조항

이 프로그램은 개인적인 용도로만 사용하세요. 다운로드한 콘텐츠를 무단으로 배포하거나 상업적으로 사용하는 것은 저작권법 위반입니다.

---

<div align="center">

**Made with ❤️ for Chzzk users**

⭐ 이 프로젝트가 유용하다면 Star를 눌러주세요!

</div>
