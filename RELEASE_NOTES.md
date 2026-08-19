## ClipCatcher v2.0.10

### 주요 변경 사항

- 변경된 치지직 클립 API에 맞춰 클립 정보·화질 조회와 다운로드를 복구했습니다.
- 대기열에서 클립 다운로드를 시작할 때 만료되지 않은 주소를 자동으로 다시 가져옵니다.
- 치지직 VOD/클립 및 YouTube 링크를 정확한 HTTPS 호스트와 경로 기준으로 검증합니다.
- YouTube 재생목록 링크에서도 선택한 영상 한 개만 다운로드합니다.
- 빠른 다시보기가 정식 VOD로 변환되면 최신 `yt-dlp` 방식으로 자동 전환합니다.
- 다운로드 취소 시 `yt-dlp`와 수동 HLS 병합용 FFmpeg 프로세스를 함께 종료합니다.

### 보안 및 안정성

- 앱 전용 `yt-dlp`는 공식 SHA-256 체크섬과 실행 검증을 통과한 뒤에만 업데이트됩니다.
- API와 HLS 요청에 제한 시간, 재시도, 응답 크기 제한을 적용했습니다.
- CHZZK 로그인 쿠키는 NAVER 도메인에만 전송됩니다.
- 썸네일 로딩이 앱 화면을 멈추지 않도록 별도 작업으로 분리했습니다.
- 앱 전용 `yt-dlp` 설치·업데이트도 별도 작업에서 실행되어 화면이 멈추지 않습니다.

### 다운로드

- Windows: `ClipCatcher-Windows.zip`
- macOS: `ClipCatcher-macOS.zip`

### 참고

다운로드한 콘텐츠의 저작권은 원 저작권자에게 있으며, 플랫폼 이용약관과 저작권자의 허락 범위를 확인해 주세요.

전체 변경 이력은 [CHANGELOG.md](https://github.com/ThankyouJerry/ClipCatcher/blob/main/CHANGELOG.md)에서 확인할 수 있습니다.
