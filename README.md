# Softility greytHR Attendance Automation

This repository contains a Playwright-based Python script to automate check-in (Sign In) and check-out (Sign Out) on the Softility greytHR Employee Self Service (ESS) portal. It is configured to run automatically using GitHub Actions on a regular schedule (Monday to Friday) or manually via manual workflow dispatch.

> [!WARNING]
> Ensure that your GitHub repository is **PRIVATE**. Storing credentials in GitHub Secrets is secure, but the repository configuration files themselves should not be exposed to the public.

---

## Table of Contents
1. [File Directory Structure](#file-directory-structure)
2. [Local Setup and Testing](#local-setup-and-testing)
3. [Git and GitHub Repository Setup](#git-and-github-repository-setup)
4. [Configuring GitHub Secrets](#configuring-github-secrets)
5. [GitHub Actions Workflow](#github-actions-workflow)
6. [Troubleshooting](#troubleshooting)

---

## File Directory Structure
- `greythr_attendance.py`: Python automation script using Playwright.
- `requirements.txt`: Dependencies (Playwright, python-dotenv).
- `.gitignore`: Files excluded from Git tracking (virtualenv, screenshots, secret configs).
- `.github/workflows/greythr.yml`: CI/CD automation workflow with cron scheduling.
- `README.md`: Setup, deployment, and troubleshooting instructions.

---

## Local Setup and Testing

### 1. Prerequisites
- Python 3.8 or higher installed on your computer.
- Basic terminal knowledge.

### 2. Installation
Open your terminal, navigate to this project folder, and run:

```bash
# Create a virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser binaries
python -m playwright install chromium
```

### 3. Configure Local Credentials
Create a `.env` file in the root of the project directory. This file is ignored by git:

```env
GREYTHR_USER=HR 318
GREYTHR_PASSWORD=Niit@65344556
GREYTHR_URL=https://softility.greythr.com/
```

### 4. Run the Script Locally
Test the script locally to confirm it navigates and interacts correctly.

```bash
# Test check-in flow
python greythr_attendance.py --action in

# Test check-out flow
python greythr_attendance.py --action out
```

*Note: Screenshots will be saved to the `screenshots/` directory. Check them to verify success.*

---

## Git and GitHub Repository Setup

Follow these steps to initialize your repository and push to GitHub:

1. **Initialize Git Repository:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: greytHR attendance automation"
   ```

2. **Create a Private GitHub Repository:**
   - Go to [GitHub](https://github.com/) and click **New Repository**.
   - Set the name (e.g., `greythr-attendance`).
   - Select **Private** (Crucial!).
   - Do **NOT** initialize with README, .gitignore, or license (we already have them).

3. **Link and Push to GitHub:**
   Replace `<your-username>` with your GitHub username:
   ```bash
   git remote add origin https://github.com/<your-username>/greythr-attendance.git
   git branch -M main
   git push -u origin main
   ```

---

## Configuring GitHub Secrets

To allow GitHub Actions to run the script automatically, you must add your credentials as repository secrets:

1. Navigate to your GitHub repository in your web browser.
2. Go to **Settings** > **Secrets and variables** > **Actions**.
3. Click **New repository secret** and add the following:
   - **`GREYTHR_USER`**: `HR 318`
   - **`GREYTHR_PASSWORD`**: `Niit@65344556`
   - **`GREYTHR_URL`**: `https://softility.greythr.com/` (Optional: If omitted, the script defaults to this URL).

---

## GitHub Actions Workflow

The workflow (`.github/workflows/greythr.yml`) is configured to run automatically:
- **Sign In (Action: `in`)**: Monday to Friday at `04:00 UTC` (9:30 AM IST).
- **Sign Out (Action: `out`)**: Monday to Friday at `13:30 UTC` (7:00 PM IST).

### Manual Run
You can manually trigger the script at any time:
1. Navigate to the **Actions** tab in your GitHub repository.
2. Select **greytHR Attendance Automation** in the sidebar.
3. Click **Run workflow**, choose the action (`in` or `out`), and click the **Run workflow** button.

---

## Troubleshooting

### 1. View Screenshots on Failure
If a scheduled run fails in GitHub Actions:
- Go to the **Actions** tab.
- Click on the failed workflow run.
- Scroll down to the **Artifacts** section at the bottom.
- Download `screenshots-in-...` or `screenshots-out-...` zip files to view what the browser saw.

### 2. Multi-Factor Authentication (MFA) or OTP
If Softility's greytHR portal triggers a security challenge (e.g. Email/SMS OTP), headless browser execution will fail. You will see `timeout_error` or `login_challenge` redirects in the screenshot logs. In this case, automation is generally not possible without static security exceptions.

### 3. IP Restrictions / VPN
If your company restricts attendance marking to office networks or specific IP addresses:
- The script may fail or show an "Access Denied" page.
- You can work around this by using a self-hosted GitHub Actions runner inside the corporate network.

### 4. Adjusting Selectors
If greytHR updates their UI, you can debug and generate updated selectors locally:
```bash
python -m playwright codegen https://softility.greythr.com/
```
Interact with the elements, and copy-paste the generated selectors into `greythr_attendance.py`.
