# ☁️ **Amazon Web Services + Terraform

MASTER CHEAT SHEET (Production Blueprint)**

> **Mental shift to reach “Master” level:**
> AWS is **not a set of icons**.
> AWS is **a programmable graph of dependencies**, and Terraform is the compiler.

---

## 🧠 Global Mental Model (Read First)

```
VPC
 ├── Subnets
 │    ├── Public  → ALB / NAT
 │    └── Private → EC2 / EKS / RDS
 ├── Route Tables
 ├── Security Groups
 └── IAM (Permissions)
```

**Everything is connected.**
If networking is wrong → compute fails
If IAM is wrong → nothing works
If state is wrong → teammates break prod

---

# 🏗️ 1️⃣ Foundation — VPC (Non-Negotiable Mastery)

A **production-grade VPC** is the most important AWS skill.

### Why VPCs fail in real life

* No NAT → private instances can’t update packages
* DB in public subnet → security incident
* Single AZ → outage during maintenance

---

## Terraform Concept: **Modules = Reuse + Safety**

Never hand-roll VPCs in production.
Use the **official, battle-tested module**.

```hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.0.0"

  name = "main-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b"]

  private_subnets = [
    "10.0.1.0/24",
    "10.0.2.0/24"
  ] # Apps, EKS nodes, RDS

  public_subnets = [
    "10.0.101.0/24",
    "10.0.102.0/24"
  ] # ALB, NAT Gateway

  enable_nat_gateway = true
  single_nat_gateway = true # OK for dev, NOT prod

  tags = {
    Environment = "production"
  }
}
```

### Why each choice matters

| Feature         | Reason                                  |
| --------------- | --------------------------------------- |
| `/16 CIDR`      | Room to grow                            |
| Private subnets | No direct internet exposure             |
| NAT Gateway     | Outbound internet for private workloads |
| Multiple AZs    | Survive AZ failure                      |

⚠️ **Prod rule:** One NAT Gateway **per AZ**.

---

# 💻 2️⃣ Compute — EC2 (Permissions + Network First)

**EC2 is never “just a VM.”**
It is always:

* Network-restricted
* Permission-scoped
* Disposable

---

## Security Group = Firewall (Stateful)

```hcl
resource "aws_security_group" "web_sg" {
  name   = "allow-web-traffic"
  vpc_id = module.vpc.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Replace with ALB SG in prod
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

⚠️ **Never allow SSH (22) from 0.0.0.0/0 in prod**

---

## EC2 Instance (Disposable Compute)

```hcl
resource "aws_instance" "web_server" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"

  subnet_id              = module.vpc.public_subnets[0]
  vpc_security_group_ids = [aws_security_group.web_sg.id]

  user_data = <<-EOF
              #!/bin/bash
              yum update -y
              yum install -y httpd
              systemctl start httpd
              EOF
}
```

### Production truth

* User data = **bootstrap**, not configuration management
* Instances should be **replaceable**, not patched forever
* Use **ASG + ALB** in real prod

---

# 💾 3️⃣ Persistence — RDS (Never Public)

> **Golden rule:**
> Databases never live in public subnets. Ever.

---

## Why RDS instead of self-managed DB

* Automatic backups
* Automated failover
* Managed patching
* Monitoring out of the box

---

```hcl
resource "aws_db_instance" "postgres" {
  allocated_storage      = 20
  engine                 = "postgres"
  engine_version         = "15.3"
  instance_class         = "db.t3.micro"

  db_name  = "myappdb"
  username = "dbadmin"
  password = var.db_password

  db_subnet_group_name   = module.vpc.database_subnet_group
  vpc_security_group_ids = [aws_security_group.db_sg.id]

  multi_az            = true
  skip_final_snapshot = true # ❌ prod = false
}
```

### Production settings checklist

* ✅ Multi-AZ
* ✅ Automated backups
* ✅ Private subnets
* ❌ Hardcoded passwords
* ❌ Public accessibility

---

# 🚀 4️⃣ Kubernetes — EKS (The Modern Default)

> Kubernetes without managed control plane = pain.

Using **Amazon EKS** lets you focus on workloads, not etcd babysitting.

---

```hcl
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = "my-cluster"
  cluster_version = "1.27"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  eks_managed_node_groups = {
    general = {
      desired_size = 2
      min_size     = 1
      max_size     = 5

      instance_types = ["t3.medium"]
      capacity_type  = "SPOT"
    }
  }
}
```

### Why this setup works

| Choice                   | Benefit             |
| ------------------------ | ------------------- |
| Private subnets          | Secure by default   |
| Managed node groups      | Easy upgrades       |
| SPOT                     | ~70% cost savings   |
| OIDC (enabled by module) | IAM for Pods (IRSA) |

---

# 🛠️ 5️⃣ Terraform Workflow — Team-Safe Operations

### The **ONLY** correct workflow

```bash
terraform init
terraform plan
terraform apply
```

⚠️ **Never skip `plan`** — it is your last line of defense.

---

## Remote State (Mandatory)

```hcl
terraform {
  backend "s3" {
    bucket         = "my-terraform-state-bucket"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
  }
}
```

### Why this matters

* S3 = shared truth
* DynamoDB = prevents double apply
* Enables CI/CD + teamwork

---

# 📜 Terraform Command Cheat Sheet (Master Level)

```bash
terraform init
terraform validate
terraform fmt
terraform plan
terraform apply
terraform destroy

terraform state list
terraform state show <resource>

terraform taint <resource>
terraform import <resource> <id>
```

---

# 🔍 AWS CLI Essentials (Ops Survival)

```bash
aws sts get-caller-identity
aws ec2 describe-instances
aws eks update-kubeconfig --name my-cluster
aws rds describe-db-instances
```

---

# ✅ Professional AWS + Terraform Checklist

☑ No hardcoded secrets
☑ IAM roles everywhere
☑ Private subnets for apps & DBs
☑ Remote Terraform state
☑ Multi-AZ enabled
☑ Modules used
☑ Resources tagged
☑ Cost awareness (SPOT, right sizing)

---

# 🧠 Final Master Insight

> **AWS mastery = understanding blast radius.**
> Terraform mastery = **making infrastructure boring and repeatable**.


