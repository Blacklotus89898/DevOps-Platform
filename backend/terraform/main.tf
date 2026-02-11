provider "aws" {
  region = "us-east-1"
}

# =========================================================================
# 1. NETWORKING (VPC, Subnets, Security Groups)
# =========================================================================

# The "House"
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = { Name = "Production-VPC" }
}

# Subnet 1 (e.g., us-east-1a)
resource "aws_subnet" "subnet_1" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true

  tags = { Name = "Subnet-1" }
}

# Subnet 2 (e.g., us-east-1b) - REQUIRED for RDS
resource "aws_subnet" "subnet_2" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "us-east-1b"
  map_public_ip_on_launch = true

  tags = { Name = "Subnet-2" }
}

# The Internet Gateway (Front Door)
resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.main.id
}

# Route Table (The Map to the Internet)
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }
}

# Associate Route Table with BOTH Subnets
resource "aws_route_table_association" "a" {
  subnet_id      = aws_subnet.subnet_1.id
  route_table_id = aws_route_table.public_rt.id
}
resource "aws_route_table_association" "b" {
  subnet_id      = aws_subnet.subnet_2.id
  route_table_id = aws_route_table.public_rt.id
}

# -------------------------------------------------------------------------
# SECURITY GROUPS (The Firewalls)
# -------------------------------------------------------------------------

# SG for EC2: Allow SSH and HTTP from ANYWHERE
resource "aws_security_group" "web_sg" {
  name        = "web_server_sg"
  description = "Allow Web traffic"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# SG for RDS: Allow MySQL ONLY from the Web Server
resource "aws_security_group" "db_sg" {
  name        = "database_sg"
  description = "Allow specific DB access"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "MySQL from Web Server"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.web_sg.id] # <--- MAGIC LINK
  }
}

# =========================================================================
# 2. EC2 (The Web Server)
# =========================================================================

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }
}

resource "aws_instance" "web" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = "t3.micro"
  subnet_id              = aws_subnet.subnet_1.id
  vpc_security_group_ids = [aws_security_group.web_sg.id]

  # SAFETY: Prevent extra charges
  credit_specification {
    cpu_credits = "standard"
  }

    user_data = <<-EOF
                #!/bin/bash
                # 1. Wait until DNF is free (prevents "Lock Error")
                while fuser /var/lib/dnf/last_makecache_lock >/dev/null 2>&1 ; do
                    echo "Waiting for other software updates to finish..."
                    sleep 5
                done

                # 2. Force install with a retry loop
                for i in {1..5}; do
                    dnf install -y httpd mariadb105 && break || sleep 15
                done

                # 3. Create directory and index page
                mkdir -p /var/www/html
                echo "<h1>System Online</h1><p>Database: ${aws_db_instance.default.address}</p>" > /var/www/html/index.html

                # 4. Permissions and Start
                chown -R apache:apache /var/www/html
                systemctl enable --now httpd
                EOF

  tags = { Name = "Web-Server" }
}

# =========================================================================
# 3. RDS (The Database)
# =========================================================================

# DB Subnet Group (Required: Must list subnets in at least 2 AZs)
resource "aws_db_subnet_group" "default" {
  name       = "main_subnet_group"
  subnet_ids = [aws_subnet.subnet_1.id, aws_subnet.subnet_2.id]

  tags = { Name = "My DB Subnet Group" }
}

resource "aws_db_instance" "default" {
  allocated_storage      = 20
  db_name                = "mydb"
  engine                 = "mysql"
  engine_version         = "8.0"
  instance_class         = "db.t3.micro" # Free tier eligible
  username               = "admin"
  password               = "password123456" # CHANGE THIS IN REAL LIFE!
  parameter_group_name   = "default.mysql8.0"
  skip_final_snapshot    = true             # FAST DELETE (Don't backup when destroying)
  
  # Networking
  db_subnet_group_name   = aws_db_subnet_group.default.name
  vpc_security_group_ids = [aws_security_group.db_sg.id]
  publicly_accessible    = false            # Security Best Practice: Keep it private

  tags = { Name = "My-RDS-Database" }
}

# =========================================================================
# 4. S3 (The Storage)
# =========================================================================

resource "random_id" "bucket_id" {
  byte_length = 4
}

resource "aws_s3_bucket" "private_bucket" {
  bucket = "my-app-storage-${random_id.bucket_id.hex}"
}

# Enable Versioning (Keep history of files)
resource "aws_s3_bucket_versioning" "versioning" {
  bucket = aws_s3_bucket.private_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Enable Encryption (Security Best Practice)
resource "aws_s3_bucket_server_side_encryption_configuration" "encrypt" {
  bucket = aws_s3_bucket.private_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# =========================================================================
# OUTPUTS
# =========================================================================
output "website_url" {
  value = "http://${aws_instance.web.public_ip}"
}

output "database_endpoint" {
  value = aws_db_instance.default.address
}