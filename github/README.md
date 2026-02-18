## 🏗️ 1. The Core Concepts

GitHub Actions follows a specific hierarchy:

* **Workflow:** The top-level automated process (a `.yml` file in `.github/workflows`).
* **Event:** The trigger (push, pull_request, release, schedule).
* **Job:** A set of steps that runs on the same **Runner**. Jobs run in parallel by default.
* **Step:** An individual task (running a command or an Action).
* **Action:** A reusable extension (like `actions/checkout`).

---

## ⌨️ 2. The Master Cheat Sheet

### Common Triggers (`on`)

* **`push` / `pull_request**`: Filter by `branches`, `tags`, or `paths`.
* **`workflow_dispatch`**: Adds a "Run Workflow" button in the UI (manual trigger).
* **`schedule`**: Runs on a cron timer (e.g., `- cron: '0 0 * * *'` for midnight).

### Runner Controls

* **`runs-on: ubuntu-latest`**: Use GitHub-hosted Linux.
* **`strategy: matrix`**: Run the same job across multiple versions (e.g., Node 18, 20, 22).
* **`needs: [job_name]`**: Create a dependency chain (Job B waits for Job A).

### Secret Management

* **`${{ secrets.GITHUB_TOKEN }}`**: Automatically provided for API calls.
* **`${{ secrets.MY_AWS_KEY }}`**: Custom secrets stored in **Repo Settings > Secrets**.

---

## 🚀 3. The "Production-Grade" CI/CD Template

This template handles a full lifecycle: **Linting → Testing → Terraform Plan → Deployment.**

```yaml
name: Production CI/CD

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  workflow_dispatch: # Allows manual triggering

jobs:
  # JOB 1: Code Quality
  quality-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install & Test
        run: |
          npm ci
          npm test
          npm run lint

  # JOB 2: Infrastructure Preview (Only on Pull Requests)
  terraform-plan:
    name: Terraform Plan
    needs: quality-check
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3

      - name: Terraform Plan
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_KEY }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET }}
        run: |
          terraform init
          terraform plan -no-color

  # JOB 3: Deploy (Only on Push to Main)
  deploy:
    name: Deploy to Production
    needs: quality-check
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production # Requires manual approval if configured in GitHub
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to AWS EKS
        run: |
          echo "Connecting to EKS..."
          # Imagine your kubectl commands here
          echo "Deployment successful!"

```

---

## 🔍 4. Advanced "Work Proficiency" Features

### 1. Environments & Approvals

In the GitHub UI, you can create an "Environment" called `production`. You can require a **manual approval** (a manager must click a button) before any job using that environment is allowed to run.

### 2. Caching for Speed

Don't download the internet every time. Use the cache action to store `node_modules` or Docker layers.

```yaml
- name: Cache dependencies
  uses: actions/cache@v4
  with:
    path: ~/.npm
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}

```

### 3. Reusable Workflows

If you have 10 repos, don't copy-paste. Create one central `.yml` and call it:

```yaml
jobs:
  call-workflow:
    uses: my-org/central-repo/.github/workflows/standard-ci.yml@main

```

---

## 🛠️ 5. Troubleshooting Mastery

* **`GITHUB_STEP_SUMMARY`**: Write Markdown to this file to show custom reports in the Actions UI.
* **Debug Logging**: Set the secret `ACTIONS_STEP_DEBUG` to `true` to see more verbose logs.
* **`if: failure()`**: Run a step only if a previous step failed (e.g., send a Slack alert).

