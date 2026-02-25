# ☁️ Stable AWS EKS Infrastructure (DevSecOps Lab)

This repository contains a hardened, deadlock-free Terraform configuration for deploying a production-ready Amazon Elastic Kubernetes Service (EKS) cluster.

It is specifically designed to avoid common EKS provisioning pitfalls, ensuring a clean `apply` and `destroy` cycle while keeping cloud costs strictly managed through a single NAT Gateway architecture.

## 🏗️ Architecture Overview

* **Network (VPC):** * CIDR `10.0.0.0/16`
* 2 Public Subnets (Tagged for external AWS Load Balancers: `kubernetes.io/role/elb = 1`)
* 2 Private Subnets (Tagged for internal AWS Load Balancers: `kubernetes.io/role/internal-elb = 1`)
* **Cost Control:** Single NAT Gateway to route private subnet egress traffic while minimizing hourly AWS charges.


* **Compute (EKS):**
* Kubernetes v1.31 Control Plane.
* AWS Managed Node Group (`t3.medium` instances).
* Private node topology (nodes reside in private subnets, completely shielded from the public internet).



## 🛡️ Key SRE & Reliability Features

This configuration implements several critical stability fixes to ensure the cluster provisions cleanly without manual intervention:

1. **Strict Provider Versioning:** Locked AWS Provider to `~> 5.0` to prevent state-file corruption and lock-file deadlocks caused by major version incompatibilities (v6.x).
2. **IMDSv2 Metadata Hop Limit:** Explicitly set `http_put_response_hop_limit = 2` on the EC2 instances. This allows containerized pods (like the `aws-node` CNI daemonset) to successfully authenticate with the AWS EC2 Metadata service, preventing `timeout: failed to connect service ":50051"` readiness probe failures.
3. **Direct IAM Policy Attachment:** The `AmazonEKS_CNI_Policy` is attached directly to the node group IAM role prior to compute initialization. This prevents the classic EKS "Dependency Deadlock" where nodes remain `NotReady` waiting for the CNI, but the CNI cannot deploy because the nodes are not ready.

## 🚀 Getting Started

### Prerequisites

* [Terraform](https://www.google.com/search?q=https://developer.hashicorp.com/terraform/downloads) (v1.3.0+)
* [AWS CLI](https://www.google.com/search?q=https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) configured with Administrator or PowerUser credentials.
* [kubectl](https://www.google.com/search?q=https://kubernetes.io/docs/tasks/tools/) installed.

### 1. Provision the Infrastructure

Clone the repository and initialize the working directory:

```bash
terraform init

```

Review the deployment plan and apply the configuration. This process takes approximately **12 to 15 minutes** (VPC ~2m, EKS Control Plane ~8m, Node Group ~3m).

```bash
terraform apply -auto-approve

```

### 2. Authenticate the Cluster

Once the apply completes successfully, update your local `kubeconfig` to communicate with the EKS control plane:

```bash
aws eks update-kubeconfig --region us-east-1 --name lab-cluster

```

Verify the nodes are online and healthy:

```bash
kubectl get nodes

```

*(You should see a `Ready` status for your EC2 instances).*

---

## 🧪 Deployment Testing (Ingress & Egress)

To verify the cluster's network routing and Load Balancer Controller are functioning, deploy a test Nginx application.

**1. Create the deployment and LoadBalancer service:**

```bash
kubectl apply -f nginx-app.yaml

```

**2. Test Egress (Outbound internet access):**
Ensure the private pods can reach the internet through the NAT Gateway:

```bash
kubectl exec -it deployment/nginx-test -- ping -c 3 google.com

```

**3. Test Ingress (Inbound internet access):**
Wait for AWS to provision the Classic Load Balancer and fetch the public URL:

```bash
kubectl get service nginx-service -w

```

Copy the `EXTERNAL-IP` (e.g., `a1b2c3d4...us-east-1.elb.amazonaws.com`) and test it via `curl` or a web browser (ensure you use `http://`, not `https://`).

```bash
curl http://<EXTERNAL-IP>

```

---

## 🛑 Cost Management & Teardown

**WARNING:** AWS charges by the hour for the EKS Control Plane and the NAT Gateway. To ensure zero unexpected charges, strictly follow this teardown order.

**Step 1: Delete Kubernetes-managed AWS Resources**
Kubernetes dynamically provisions AWS Load Balancers. You must delete the service via `kubectl` first, otherwise Terraform will leave an orphaned load balancer on your AWS bill.

```bash
kubectl delete -f nginx-app.yaml

```

*(Wait 60 seconds for the AWS ELB to fully terminate).*

**Step 2: Destroy Terraform Infrastructure**
Cleanly wipe the VPC, subnets, NAT Gateway, and EKS cluster:

```bash
terraform destroy -auto-approve

```
