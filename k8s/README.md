# Kubernetes 배포 가이드

Nose Embedder gRPC 서버를 NKS(Naver Kubernetes Service)에 배포하는 가이드입니다.

## 📋 사전 요구사항

- Docker 설치
- kubectl 설치 및 NKS 클러스터 연결 설정
- NCP Container Registry 접근 권한

## 🔧 배포 단계

### 1. Docker 이미지 빌드 및 푸시

```bash
# 1-1. 프로젝트 루트로 이동
cd fastapi-gprc-server

# 1-2. Docker 이미지 빌드 (Protobuf 파일 자동 생성됨)
docker build -t nose-embedder:latest .

# 1-3. NCP Container Registry에 태그
docker tag nose-embedder:latest your-registry.kr.ncr.ntruss.com/nose-embedder:latest

# 1-4. NCP Container Registry에 로그인
docker login your-registry.kr.ncr.ntruss.com

# 1-5. 이미지 푸시
docker push your-registry.kr.ncr.ntruss.com/nose-embedder:latest
```

**참고**: Protobuf 파일(`nose_embedder_pb2.py`, `nose_embedder_pb2_grpc.py`)은 Docker 빌드 중에 자동으로 생성됩니다.

### 2. Kubernetes Secret 생성 (NCP 자격증명)

**⚠️ 주의: Secret 파일에는 실제 자격증명이 포함되어 있습니다!**

```bash
# 2-1. Secret 파일 수정 (실제 자격증명으로 교체)
vi k8s/secret.yaml

# 2-2. Secret 생성
kubectl apply -f k8s/secret.yaml
```

또는 명령어로 직접 생성:
```bash
kubectl create secret generic nose-embedder-secret \
  --namespace=petdid-network \
  --from-literal=NCP_ACCESS_KEY=your_access_key \
  --from-literal=NCP_SECRET_KEY=your_secret_key
```

### 3. ConfigMap 생성

```bash
kubectl apply -f k8s/configmap.yaml
```

### 4. Deployment 수정 및 배포

```bash
# 4-1. deployment.yaml 파일에서 이미지 주소 수정
# image: your-registry/nose-embedder:latest
# → image: your-registry.kr.ncr.ntruss.com/nose-embedder:latest

vi k8s/deployment.yaml

# 4-2. Deployment 배포
kubectl apply -f k8s/deployment.yaml
```

### 5. Service 배포

```bash
kubectl apply -f k8s/service.yaml
```

## 🔍 배포 확인

### 파드 상태 확인
```bash
kubectl get pods -n petdid-network -l app=nose-embedder
```

### 로그 확인
```bash
kubectl logs -n petdid-network -l app=nose-embedder --tail=100 -f
```

### 서비스 확인
```bash
kubectl get svc -n petdid-network nose-embedder-service
```

### 상세 정보 확인
```bash
kubectl describe deployment -n petdid-network nose-embedder-server
kubectl describe pod -n petdid-network -l app=nose-embedder
```

## 🧪 서비스 테스트

### 클러스터 내부에서 테스트 (다른 파드에서)
```python
import grpc
import nose_embedder_pb2
import nose_embedder_pb2_grpc

# 서비스 DNS 이름으로 연결
channel = grpc.insecure_channel('nose-embedder-service.petdid-network.svc.cluster.local:50052')
stub = nose_embedder_pb2_grpc.NoseEmbedderServiceStub(channel)

# 헬스체크
request = nose_embedder_pb2.HealthCheckRequest(service='NoseEmbedderService')
response = stub.HealthCheck(request)
print(f"Health check: {response}")
```

### 포트 포워딩으로 로컬에서 테스트
```bash
# 포트 포워딩
kubectl port-forward -n petdid-network svc/nose-embedder-service 50052:50052

# 다른 터미널에서 테스트
python your_client_test.py
```

## 📊 리소스 사양

현재 설정:
- **Replicas**: 1개
- **CPU Request**: 100m (0.1 CPU)
- **CPU Limit**: 500m (0.5 CPU)
- **Memory Request**: 256Mi
- **Memory Limit**: 512Mi

필요에 따라 `k8s/deployment.yaml`에서 조정 가능합니다.

## 🔄 업데이트 방법

### 1. 코드 변경 후 재배포
```bash
# 이미지 재빌드 및 푸시
docker build -t your-registry.kr.ncr.ntruss.com/nose-embedder:v1.1 .
docker push your-registry.kr.ncr.ntruss.com/nose-embedder:v1.1

# Deployment 이미지 업데이트
kubectl set image deployment/nose-embedder-server \
  -n petdid-network \
  nose-embedder=your-registry.kr.ncr.ntruss.com/nose-embedder:v1.1

# 또는 deployment.yaml 수정 후
kubectl apply -f k8s/deployment.yaml
```

### 2. 설정 변경
```bash
# ConfigMap 수정
kubectl edit configmap -n petdid-network nose-embedder-config

# 파드 재시작 (설정 적용)
kubectl rollout restart deployment/nose-embedder-server -n petdid-network
```

## 🗑️ 삭제

```bash
# 모든 리소스 삭제
kubectl delete -f k8s/service.yaml
kubectl delete -f k8s/deployment.yaml
kubectl delete -f k8s/configmap.yaml
kubectl delete -f k8s/secret.yaml
```

## 📝 주요 설정

### 환경변수 (ConfigMap)
- `ENABLE_CENTER_CROP`: `false` - **이미지 크롭 비활성화 (원본 이미지 사용)**
- `GRPC_PORT`: `50052`
- `GRPC_WORKERS`: `3`
- `MODEL_INPUT_SIZE`: `96`

### 서비스 엔드포인트
- **클러스터 내부**: `nose-embedder-service.petdid-network.svc.cluster.local:50052`
- **네임스페이스 내**: `nose-embedder-service:50052`

## ⚠️ 트러블슈팅

### 파드가 시작하지 않는 경우
```bash
# 이벤트 확인
kubectl describe pod -n petdid-network -l app=nose-embedder

# 로그 확인
kubectl logs -n petdid-network -l app=nose-embedder
```

### 이미지 Pull 실패
```bash
# ImagePullBackOff 에러 시 Container Registry 자격증명 확인
kubectl get events -n petdid-network --sort-by='.lastTimestamp'

# Secret 생성 (NCP Container Registry용)
kubectl create secret docker-registry ncp-registry-secret \
  --namespace=petdid-network \
  --docker-server=your-registry.kr.ncr.ntruss.com \
  --docker-username=your-ncp-access-key \
  --docker-password=your-ncp-secret-key

# deployment.yaml에 imagePullSecrets 추가:
# spec:
#   template:
#     spec:
#       imagePullSecrets:
#       - name: ncp-registry-secret
```

### gRPC 연결 실패
```bash
# 서비스 엔드포인트 확인
kubectl get endpoints -n petdid-network nose-embedder-service

# 포트가 열려있는지 확인
kubectl exec -it -n petdid-network <pod-name> -- netstat -tlnp | grep 50052
```
