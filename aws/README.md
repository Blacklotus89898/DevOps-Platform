# 🔥 PART 1 — What Ingress and Egress REALLY Mean

## 🟢 Ingress = Incoming Traffic

Traffic entering a resource.

Example:

* User → Web Server (Port 80/443)
* App Server → Database (Port 5432)

## 🔵 Egress = Outgoing Traffic

Traffic leaving a resource.

Example:

* Web Server → Internet (for updates)
* App → RDS
* Pod → External API

---

# 🧠 PART 2 — Security Groups Deep Dive (REAL Understanding)

Security Groups are:

* Stateful firewalls
* Attached to ENIs (Elastic Network Interfaces)
* Applied at instance level (not subnet level)
* Default deny inbound
* Default allow outbound

### 🔐 Stateful = Critical Concept

If inbound traffic is allowed, response traffic is automatically allowed.

Example:
If port 443 is allowed inbound, return traffic does NOT require an outbound rule.

This is where many junior engineers get confused.

---

# 🏗 PART 3 — Production Architecture Example (Full Flow)

Real-world setup:

```
Internet
   ↓
Load Balancer (Public Subnet)
   ↓
EC2 or EKS (Private Subnet)
   ↓
RDS (Private Subnet)
```

Now let’s break every connection.

---

# 🌍 Layer 1 — Internet → Load Balancer

### Required Ingress on LB Security Group:

| Port | Protocol | Source    |
| ---- | -------- | --------- |
| 80   | TCP      | 0.0.0.0/0 |
| 443  | TCP      | 0.0.0.0/0 |

### Why?

Public-facing application.

### Egress?

Usually allow all (default).
LB needs to talk to target group.

---

# 🖥 Layer 2 — Load Balancer → EC2

Here is where mastery begins.

❌ WRONG:
Allow 0.0.0.0/0 to EC2 on port 80.

✅ CORRECT:
Allow inbound from the Load Balancer Security Group.

Example:

| Port | Source          |
| ---- | --------------- |
| 80   | sg-loadbalancer |

This ensures only the LB can reach EC2.

---

# 🧱 Layer 3 — EC2 → RDS

Database must NEVER be public.

### RDS Security Group Ingress:

| Port | Source |
| ---- | ------ |
| 5432 | sg-ec2 |

### Why?

Only app servers should connect.

---

# 🔄 FULL TRAFFIC FLOW EXPLAINED

Let’s trace a request:

1. User hits HTTPS (443)
2. LB receives it
3. LB forwards to EC2
4. EC2 queries RDS
5. RDS responds
6. EC2 returns response
7. LB sends back to user

Notice:

* Only specific SG → SG references
* No public DB
* No open EC2 ports

This is professional-grade networking.

---

# 🧨 PART 4 — Egress Rules (Where People Fail Interviews)

Most engineers ignore egress.

Default egress is:

```
All traffic
0.0.0.0/0
```

In regulated environments, this is NOT acceptable.

---

## 🔐 Restricted Egress Example

EC2 should:

* Talk to RDS (5432)
* Talk to S3
* Reach NAT for updates

So egress might be:

| Port | Destination |
| ---- | ----------- |
| 5432 | sg-rds      |
| 443  | 0.0.0.0/0   |

This prevents data exfiltration on random ports.

---

# 🚪 PART 5 — Port Mastery (Memorize These)

| Service        | Port  |
| -------------- | ----- |
| HTTP           | 80    |
| HTTPS          | 443   |
| SSH            | 22    |
| RDP            | 3389  |
| PostgreSQL     | 5432  |
| MySQL          | 3306  |
| MongoDB        | 27017 |
| Redis          | 6379  |
| Kubernetes API | 6443  |
| Nginx default  | 80    |
| NodeJS typical | 3000  |

If you don’t know ports, you are not senior.

---

# 🌐 PART 6 — Subnet + Routing Interaction

Security Groups control:
✔ Who can talk to resource

Route Tables control:
✔ Where traffic can go

NAT Gateway allows:
✔ Private subnet → Internet (egress only)

Internet Gateway allows:
✔ Public subnet ↔ Internet

Without proper routing, SG rules do nothing.

---

# 🧠 PART 7 — EKS Special Case (Kubernetes Networking)

In **Amazon EKS**:

You now have 3 layers:

1. Security Groups
2. Node Security Groups
3. Kubernetes Network Policies

Traffic must pass all three.

Example:

Pod → Pod
Pod → Service
Pod → RDS

Kubernetes Network Policy can block traffic even if SG allows it.

Senior engineers know:
Security Groups = Infrastructure layer
Network Policies = Application layer

---

# 🛑 PART 8 — Security Group vs NACL (Interview Classic)

Security Groups:

* Stateful
* Instance level
* Easier to manage

Network ACLs:

* Stateless
* Subnet level
* Need inbound + outbound rules

99% of production filtering is done with Security Groups.

---

# 🧪 PART 9 — Debugging Like a Pro

When something can't connect:

1. Check Security Group inbound
2. Check Security Group outbound
3. Check Route Table
4. Check NACL
5. Check DNS
6. Check Service listening port (`netstat -tulnp`)
7. Check app-level firewall

---

# 💼 PART 10 — Interview-Level Questions

If they ask:

**Why are security groups stateful?**
→ So response traffic doesn't require explicit outbound rules.

**Why use SG references instead of CIDR blocks?**
→ More secure, dynamic, scales automatically.

**Why restrict egress?**
→ Prevent data exfiltration and lateral movement.

---

# 🎯 FINAL: What “Mastery” Looks Like at Work

A true professional:

✔ Never exposes databases publicly
✔ Uses SG-to-SG referencing
✔ Restricts SSH to their IP
✔ Understands ephemeral ports
✔ Can trace full request path in their head
✔ Knows how NAT, IGW, and routing interact

