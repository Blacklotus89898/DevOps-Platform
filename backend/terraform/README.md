# AWS 3-Tier Infrastructure as Code (Terraform)

A production-ready, automated AWS deployment using **Terraform**. This project provisions a secure, scalable 3-tier environment in the `us-east-1` region, integrating compute, managed databases, and object storage.

## 🏗 Architecture Overview

The infrastructure is designed with a focus on security and the **AWS Well-Architected Framework**.

* **Networking**: Custom VPC with public subnets across multiple Availability Zones (AZs) for high availability.
* **Compute**: EC2 instance running Amazon Linux 2023, automated via `user_data` to bootstrap a web server and database client.
* **Database**: Amazon RDS (MySQL 8.0) instance isolated within a private security group, accessible only by the web tier.
* **Storage**: S3 Bucket with versioning and AES-256 server-side encryption enabled.
* **Security**:
* **IAM Roles**: EC2 uses an Instance Profile for S3 access (no hardcoded credentials).
* **Security Groups**: Layered firewall rules allowing HTTP (80) and SSH (22) to the web tier, and only MySQL (3306) to the data tier.



## 🚀 Technical Stack

* **Cloud Provider**: AWS
* **IaC Tool**: Terraform (HCL)
* **OS**: Amazon Linux 2023
* **Web Server**: Apache (httpd)
* **Database**: RDS MySQL 8.0 (Client: MariaDB 10.5)

## 🛠 Prerequisites

* [Terraform](https://www.google.com/search?q=https://www.terraform.io/downloads.html) installed.
* AWS CLI configured with appropriate permissions.
* An active AWS Account (Free Tier eligible).

## 📂 Project Structure

```text
.
├── main.tf            # Core logic (VPC, EC2, RDS, S3)
├── variables.tf       # Input variables for customization
├── outputs.tf         # Key information (Web URL, DB Endpoint)
├── .gitignore         # Prevents committing .tfstate and secrets
└── README.md

```

## ⚡ Deployment Instructions

1. **Clone the repository**:
```bash
git clone https://github.com/your-username/aws-terraform-lab.git
cd aws-terraform-lab

```


2. **Initialize Terraform**:
```bash
terraform init

```


3. **Review the execution plan**:
```bash
terraform plan

```


4. **Deploy the infrastructure**:
```bash
terraform apply

```


5. **Access the application**:
Copy the `website_url` from the output and paste it into your browser.

## 🛡 Security & Best Practices Applied

* **Immutable Infrastructure**: Updates to the server configuration trigger a replacement rather than an in-place patch.
* **Sensitive Data**: Database passwords are managed via Terraform variables (marked as `sensitive`).
* **Least Privilege**: IAM policies are scoped specifically to the resources required by the application.
* **Reliability**: Implemented a `dnf` lock-check loop in the bootstrap script to ensure successful package installation on Amazon Linux 2023.