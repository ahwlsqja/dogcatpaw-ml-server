# 🔐 Kubernetes Secret 안전 관리 가이드

NCP 자격증명과 같은 민감한 정보를 안전하게 관리하는 방법입니다.

## ⚠️ 중요: Git에 Secret을 커밋하지 마세요!

`k8s/secret.yaml` 파일은 템플릿입니다. 실제 자격증명은 **절대 Git에 커밋하면 안 됩니다**.

## 🛠️ 권장 방법들

### 방법 1: kubectl 명령어로 직접 생성 (가장 안전 - 권장)

```bash
# Secret 생성
kubectl create secret generic nose-embedder-secret \
  --namespace=petdid-network \
  --from-literal=NCP_ACCESS_KEY='your-actual-access-key' \
  --from-literal=NCP_SECRET_KEY='your-actual-secret-key'

# 확인
kubectl get secret -n petdid-network nose-embedder-secret
```

### 방법 2: 환경변수에서 생성

```bash
# 환경변수 설정
export NCP_ACCESS_KEY='your-actual-access-key'
export NCP_SECRET_KEY='your-actual-secret-key'

# Secret 생성
kubectl create secret generic nose-embedder-secret \
  --namespace=petdid-network \
  --from-literal=NCP_ACCESS_KEY="$NCP_ACCESS_KEY" \
  --from-literal=NCP_SECRET_KEY="$NCP_SECRET_KEY"
```

### 방법 3: 로컬 파일에서 생성 (Git에 커밋하지 않음)

```bash
# 1. secret.yaml 파일을 로컬에 복사
cp k8s/secret.yaml k8s/secret.local.yaml

# 2. secret.local.yaml 파일 수정 (실제 자격증명 입력)
vi k8s/secret.local.yaml

# 3. Secret 생성
kubectl apply -f k8s/secret.local.yaml

# 4. 로컬 파일 삭제 (보안)
rm k8s/secret.local.yaml
```

**참고**: `k8s/secret.local.yaml`은 `.gitignore`에 추가되어 있어 Git에 커밋되지 않습니다.

### 방법 4: Sealed Secrets 사용 (프로덕션 권장)

Sealed Secrets를 사용하면 암호화된 Secret을 Git에 안전하게 저장할 수 있습니다.

```bash
# 1. Sealed Secrets Controller 설치
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml

# 2. kubeseal CLI 설치
# macOS
brew install kubeseal

# Linux
wget https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/kubeseal-linux-amd64 -O kubeseal
chmod +x kubeseal
sudo mv kubeseal /usr/local/bin/

# 3. Secret을 SealedSecret으로 암호화
kubectl create secret generic nose-embedder-secret \
  --namespace=petdid-network \
  --from-literal=NCP_ACCESS_KEY='your-actual-access-key' \
  --from-literal=NCP_SECRET_KEY='your-actual-secret-key' \
  --dry-run=client -o yaml | \
  kubeseal -o yaml > k8s/sealed-secret.yaml

# 4. SealedSecret 배포 (이건 Git에 커밋해도 안전함)
kubectl apply -f k8s/sealed-secret.yaml
```

## 🔍 Secret 확인

```bash
# Secret 목록 확인
kubectl get secrets -n petdid-network

# Secret 상세 확인
kubectl describe secret -n petdid-network nose-embedder-secret

# Secret 값 디코딩 (base64)
kubectl get secret -n petdid-network nose-embedder-secret -o jsonpath='{.data.NCP_ACCESS_KEY}' | base64 --decode
```

## 🗑️ Secret 삭제 및 재생성

```bash
# Secret 삭제
kubectl delete secret -n petdid-network nose-embedder-secret

# 새로운 Secret 생성
kubectl create secret generic nose-embedder-secret \
  --namespace=petdid-network \
  --from-literal=NCP_ACCESS_KEY='new-access-key' \
  --from-literal=NCP_SECRET_KEY='new-secret-key'

# 파드 재시작 (새 Secret 적용)
kubectl rollout restart deployment/nose-embedder-server -n petdid-network
```

## 📋 실수로 Git에 커밋한 경우

만약 실수로 실제 자격증명을 Git에 커밋했다면:

### 1. 즉시 자격증명 변경
```bash
# NCP 콘솔에서 Access Key 삭제 및 재생성
# https://console.ncloud.com/
```

### 2. Git 히스토리에서 제거 (마지막 커밋인 경우)
```bash
# secret.yaml 수정 (실제 자격증명 제거)
vi k8s/secret.yaml

# 마지막 커밋 수정
git add k8s/secret.yaml
git commit --amend --no-edit

# 강제 푸시
git push origin main --force-with-lease
```

### 3. Git 히스토리에서 완전 제거 (이전 커밋인 경우)
```bash
# BFG Repo-Cleaner 사용 (권장)
# https://rtyley.github.io/bfg-repo-cleaner/

# 또는 git filter-branch
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch k8s/secret.yaml" \
  --prune-empty --tag-name-filter cat -- --all

git push origin --force --all
```

## 🔒 보안 모범 사례

1. **절대 Git에 커밋하지 않기**: `.gitignore`에 secret 파일 추가
2. **최소 권한 원칙**: Secret에는 필요한 권한만 부여
3. **정기적인 로테이션**: 자격증명을 주기적으로 변경
4. **암호화**: Sealed Secrets, Vault 등 사용
5. **접근 제어**: K8s RBAC로 Secret 접근 제한
6. **모니터링**: Secret 접근 로그 감사

## 🛡️ NCP IAM 최소 권한 설정

ML 서버에 필요한 최소 권한:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::dogcatpaw-backend/pet/*",
        "arn:aws:s3:::dogcatpaw-backend/nose-print-photo/*"
      ]
    }
  ]
}
```
