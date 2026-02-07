# DevOps-Platform

/DevOps-Platform
├── backend/                # FastAPI Application
│   ├── app/
│   │   ├── main.py         # Entry point
│   │   ├── api/            # API Routes (Proxmox, K8s, AI)
│   │   ├── services/       # Logic for TF/Ansible/Subprocess
│   │   └── agents/         # Future AI Agent logic (LangChain/Gemini)
│   ├── terraform/          # .tf templates for Lab VMs
│   └── ansible/            # .yml playbooks for Lab configuration
├── frontend/               # React + Tailwind (Vite)
│   ├── src/
│   │   ├── components/     # Reusable UI (Charts, Log Viewers)
│   │   └── hooks/          # Custom WebSocket hooks for real-time logs
└── docker-compose.yml      # Run the whole stack locally
