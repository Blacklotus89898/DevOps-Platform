# ☸️ **Kubernetes MASTER Cheat Sheet (Production Edition)**


---

## 1️⃣ Core Architecture — *Why Kubernetes behaves the way it does*

**Mental model**

> Kubernetes is a **declarative reconciliation engine**, not an imperative tool.

You don’t “run” things — you **declare desired state**, and controllers enforce it.

### Control Plane (decision-making)

| Component            | What it actually does in prod                       |
| -------------------- | --------------------------------------------------- |
| `kube-apiserver`     | Auth, validation, admission, persistence            |
| `etcd`               | Source of truth — lose it, lose the cluster         |
| `kube-scheduler`     | Chooses nodes based on resources + constraints      |
| `controller-manager` | Constantly fixes drift (replicas, endpoints, nodes) |

### Workers (execution)

| Component    | Reality                  |
| ------------ | ------------------------ |
| `kubelet`    | Ensures pod spec is met  |
| `kube-proxy` | Programs iptables / IPVS |

---

## 2️⃣ kubectl — **Elite Operator Cheat Sheet**

### Must-have setup

```bash
alias k=kubectl
export do="--dry-run=client -o yaml"
```

### Context safety (do this always)

```bash
k config get-contexts
k config use-context prod
k config set-context --current --namespace=backend
```

⚠️ **Most production mistakes = wrong context**

---

### 🔥 Top 15 kubectl commands (memorize)

```bash
k get pods -A -owide
k get nodes -owide
k describe pod <pod>
k logs <pod>
k logs <pod> --previous
k get events --sort-by=.metadata.creationTimestamp
k top nodes
k top pods
k rollout status deployment/app
k rollout undo deployment/app
k get endpoints svc-name
k auth can-i get pods --as system:serviceaccount:ns:sa
k explain deployment.spec.template.spec
k get pvc
k describe pvc
```

---

## 3️⃣ Storage — **Where most clusters break**

### Mental model

```
StorageClass → PVC → PV → Pod
```

Pods **never** talk to PVs directly.

---

### ✅ StorageClass (Dynamic provisioning)

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp3
reclaimPolicy: Retain        # Keep data after PVC deletion
volumeBindingMode: WaitForFirstConsumer
```

**Why these fields matter**

* `WaitForFirstConsumer` → avoids AZ mismatch
* `Retain` → prevents data loss

---

### ✅ PersistentVolumeClaim

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-pvc
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 10Gi
```

**If PVC is Pending**

```bash
k describe pvc
k get sc
```

---

## 4️⃣ RBAC — **Why “Forbidden” happens**

### Mental model

```
ServiceAccount → Role → RoleBinding
```

Pods **do NOT** use your kubectl credentials.

---

### ✅ ServiceAccount

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-sa
```

---

### ✅ Role (what is allowed)

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: app-role
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]
```

---

### ✅ RoleBinding (who gets it)

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: app-rb
subjects:
- kind: ServiceAccount
  name: app-sa
roleRef:
  kind: Role
  name: app-role
  apiGroup: rbac.authorization.k8s.io
```

### Debug RBAC fast

```bash
k auth can-i list pods --as system:serviceaccount:ns:app-sa
```

---

## 5️⃣ Production Deployment — **Every field explained**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pro-app
  labels:
    app: pro-app
spec:
  replicas: 3                    # HA
  revisionHistoryLimit: 5        # Rollback safety
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1                # Extra pod during update
      maxUnavailable: 0          # Zero downtime
  selector:
    matchLabels:
      app: pro-app
  template:
    metadata:
      labels:
        app: pro-app
    spec:
      serviceAccountName: app-sa
      securityContext:
        runAsNonRoot: true       # Security baseline
        fsGroup: 2000
      containers:
      - name: api
        image: nginx:1.25        # NEVER use latest
        imagePullPolicy: IfNotPresent

        ports:
        - containerPort: 80

        resources:
          requests:
            cpu: "100m"          # Scheduler uses this
            memory: "128Mi"
          limits:
            cpu: "500m"          # Node protection
            memory: "256Mi"

        readinessProbe:           # Traffic gating
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5

        livenessProbe:            # Self-healing
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 15
          periodSeconds: 10

        envFrom:
        - configMapRef:
            name: app-config

        volumeMounts:
        - name: app-storage
          mountPath: /data

      volumes:
      - name: app-storage
        persistentVolumeClaim:
          claimName: app-pvc
```

---

## 6️⃣ Service — **Traffic abstraction**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: pro-app-svc
spec:
  type: ClusterIP
  selector:
    app: pro-app
  ports:
  - port: 80
    targetPort: 80
```

### Debug service issues

```bash
k get svc
k get endpoints pro-app-svc
```

If endpoints empty → label mismatch.

---

## 7️⃣ Ingress — **HTTP routing**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: pro-app-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: pro-app-svc
            port:
              number: 80
```

⚠️ Ingress **requires** an ingress controller.

---

## 8️⃣ Workload Selection Cheat Sheet

| Resource    | Guarantee                 |
| ----------- | ------------------------- |
| Deployment  | Stateless scaling         |
| StatefulSet | Stable identity + storage |
| DaemonSet   | One pod per node          |
| Job         | Guaranteed completion     |
| CronJob     | Scheduled execution       |

---

## 9️⃣ Autoscaling — **Common failure**

```bash
k autoscale deployment pro-app --cpu-percent=70 --min=3 --max=10
```

⚠️ **No resource requests = HPA does nothing**

---

## 🔟 Helm — **Production standard**

```
mychart/
  Chart.yaml
  values.yaml
  templates/
    deployment.yaml
    service.yaml
    ingress.yaml
    pvc.yaml
    serviceaccount.yaml
    rbac.yaml
```

### Daily Helm commands

```bash
helm list
helm history pro-app
helm upgrade --install pro-app .
helm rollback pro-app 2
helm uninstall pro-app
```

---

## 🔥 On-Call Debug Flow (Tattoo this)

```text
Pod broken?
→ k get pods
→ k describe pod
→ k logs --previous
→ k get events

Traffic broken?
→ k get svc
→ k get endpoints
→ k describe ingress

Storage broken?
→ k describe pvc

RBAC broken?
→ k auth can-i
```

---

# 🚀 **1. Production‑Grade Kubernetes Template Pack**
This is a **full microservice bundle** you can drop into any cluster.  
Everything is wired together: config, secrets, storage, autoscaling, networking.

Each file is intentionally minimal but production‑grade.

---

## **📄 01-configmap.yaml**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  LOG_LEVEL: info
  FEATURE_FLAG_X: "true"
```

---

## **📄 02-secret.yaml**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secret
type: Opaque
data:
  DB_PASSWORD: cGFzc3dvcmQ=   # "password"
```

---

## **📄 03-pvc.yaml**
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
  storageClassName: standard
```

---

## **📄 04-deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
  labels:
    app: app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: app
  template:
    metadata:
      labels:
        app: app
    spec:
      containers:
        - name: app
          image: your-registry/app:1.0.0
          ports:
            - containerPort: 8080
          env:
            - name: LOG_LEVEL
              valueFrom:
                configMapKeyRef:
                  name: app-config
                  key: LOG_LEVEL
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: app-secret
                  key: DB_PASSWORD
          volumeMounts:
            - name: data
              mountPath: /var/lib/app
          resources:
            requests:
              cpu: "200m"
              memory: "256Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
          readinessProbe:
            httpGet:
              path: /ready
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 5
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 10
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: app-data
```

---

## **📄 05-service.yaml**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: app
spec:
  type: ClusterIP
  selector:
    app: app
  ports:
    - port: 80
      targetPort: 8080
```

---

## **📄 06-ingress.yaml**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
    - host: app.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: app
                port:
                  number: 80
```

---

## **📄 07-hpa.yaml**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: app
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

---

# 🧠 **2. Visual Map: How All Kubernetes YAML Objects Relate**

Here’s the mental model senior engineers use — clean, layered, and intuitive.

```
                   ┌──────────────────────────────┐
                   │          Ingress              │
                   │   (External HTTP Routing)     │
                   └──────────────┬───────────────┘
                                  │
                                  ▼
                   ┌──────────────────────────────┐
                   │            Service            │
                   │   (Stable Virtual IP)         │
                   └──────────────┬───────────────┘
                                  │
                                  ▼
                   ┌──────────────────────────────┐
                   │          Deployment           │
                   │  (Manages ReplicaSets/Pods)   │
                   └──────────────┬───────────────┘
                                  │
                                  ▼
                   ┌──────────────────────────────┐
                   │             Pods              │
                   │  (Containers + Probes + Env) │
                   └──────────────┬───────────────┘
                                  │
       ┌──────────────────────────┼──────────────────────────┐
       ▼                          ▼                          ▼
┌──────────────┐        ┌────────────────┐        ┌────────────────────┐
│  ConfigMap   │        │    Secret      │        │        PVC          │
│ (Env/config) │        │ (Sensitive env)│        │ (Persistent storage)│
└──────────────┘        └────────────────┘        └────────────────────┘

```

And the autoscaler sits on the side:

```
        ┌──────────────────────────────┐
        │              HPA             │
        │ (Scales Deployment replicas) │
        └──────────────┬──────────────┘
                       │
                       ▼
                Deployment
```


