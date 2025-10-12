# 빌드 가이드

## 개요

이 프로젝트는 두 가지 빌드 방식을 지원합니다:

1. **NCP SourceCommit 빌드**: Object Storage에서 모델 다운로드
2. **로컬 빌드**: 로컬 모델 파일 포함

---

## 1. NCP SourceCommit 빌드 (권장)

### 사전 준비

1. NCP Object Storage에 모델 업로드
   ```bash
   # 예시 경로: bucket-name/models/embedder_model.onnx
   ```

2. SourceCommit 빌드 설정에서 Build Args 추가

### Build Arguments

```bash
docker build \
  --build-arg NCP_ACCESS_KEY=your_access_key \
  --build-arg NCP_SECRET_KEY=your_secret_key \
  --build-arg NCP_BUCKET_NAME=your_bucket_name \
  --build-arg NCP_MODEL_KEY=models/embedder_model.onnx \
  -t nose-embedder:latest .
```

### NCP SourceCommit에서 설정

빌드 설정에서 다음 Build Args를 환경변수로 추가:

- `NCP_ACCESS_KEY`: NCP Access Key
- `NCP_SECRET_KEY`: NCP Secret Key (Secret으로 설정)
- `NCP_BUCKET_NAME`: 버킷 이름
- `NCP_MODEL_KEY`: 모델 객체 키 (예: `models/embedder_model.onnx`)

> **참고**: `NCP_ENDPOINT`와 `NCP_REGION`은 기본값이 설정되어 있습니다.
> - Endpoint: `https://kr.object.ncloudstorage.com`
> - Region: `kr-standard`

---

## 2. 로컬 빌드

### 사전 준비

1. 모델 파일을 프로젝트 루트에 복사
   ```bash
   cp /path/to/embedder_model.onnx .
   ```

### 빌드

```bash
docker build -t nose-embedder:latest .
```

NCP 자격증명이 제공되지 않으면 자동으로 로컬 모델 파일(`embedder_model.onnx`)을 사용합니다.

---

## 3. 런타임 모델 다운로드 (대안)

빌드 시 모델을 포함하지 않고, 런타임에 다운로드할 수도 있습니다.

### 환경변수 설정

```bash
# .env 파일
NCP_ACCESS_KEY=your_access_key
NCP_SECRET_KEY=your_secret_key
NCP_BUCKET_NAME=your_bucket_name
NCP_MODEL_KEY=models/embedder_model.onnx
```

### 실행

```bash
docker run --env-file .env -p 50052:50052 nose-embedder:latest
```

서버 시작 시 자동으로 NCP Object Storage에서 모델을 다운로드합니다.

---

## 빌드 전략 비교

| 방식 | 장점 | 단점 |
|------|------|------|
| **빌드 시 다운로드** | • 파드 시작 빠름<br>• 네트워크 장애에 강함 | • 이미지 크기 증가 (500MB+)<br>• 모델 업데이트 시 재빌드 필요 |
| **런타임 다운로드** | • 이미지 크기 작음<br>• 모델 업데이트 용이 | • 파드 시작 느림<br>• Object Storage 의존성 |
| **로컬 파일** | • 간단함<br>• 외부 의존성 없음 | • 이미지 크기 증가<br>• CI/CD 복잡도 증가 |

**권장**: NCP 환경에서는 **빌드 시 다운로드** 방식 권장

---

## 검증

빌드가 성공했는지 확인:

```bash
# 컨테이너 실행
docker run -p 50052:50052 nose-embedder:latest

# 로그 확인 (모델 로드 성공 메시지)
# ✓ 모델 로드 성공
# ✓ 애플리케이션이 성공적으로 시작되었습니다
```

---

## 문제 해결

### 빌드 시 모델 다운로드 실패

```
✗ Download failed (ClientError): 403 - Forbidden
```

**해결책**: NCP 자격증명 확인 및 Object Storage 권한 확인

### 로컬 모델 파일 없음

```
ERROR: failed to solve: failed to compute cache key
```

**해결책**:
1. `embedder_model.onnx` 파일을 프로젝트 루트에 복사
2. 또는 NCP Build Args 제공

### 런타임 다운로드 실패

```
ModelNotLoadedError: NCP Object Storage에서 모델 다운로드 실패
```

**해결책**: 환경변수 확인 (`NCP_ACCESS_KEY`, `NCP_SECRET_KEY`, `NCP_BUCKET_NAME`, `NCP_MODEL_KEY`)
