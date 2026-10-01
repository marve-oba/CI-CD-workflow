# ATMOS Weather: Zero-to-GitOps Hands-On Runbook

**Scenario:** You received a work ticket and only the developer's `app/` folder.  
**Your role:** Take that source code all the way to Kubernetes through a small but complete CI/CD and GitOps lifecycle.  
**Primary IDE:** VS Code.  
**Primary workstation path:** macOS, with official documentation links for other platforms.  
**Cluster:** KIND, created by Terraform.  
**Image registry:** Private Docker Hub repository for the main learning path.  
**CI:** GitHub Actions.  
**Packaging:** Docker and Helm.  
**Runtime secrets:** HashiCorp Vault Agent Injector.  
**Private-registry credentials:** Vault Secrets Operator.  
**CD:** Argo CD.

> This is a learning lab, not a production reference architecture. It deliberately keeps the engineering surface small while preserving the real lifecycle.

---

## 0. Read the ticket first

Imagine your ticket says:

> **Deploy the ATMOS weather application to Kubernetes.**  
> Create a GitHub repository, containerize the supplied application, publish the image to a private registry, provision a local Kubernetes cluster as Infrastructure as Code, deploy the application first with raw Kubernetes manifests and then with Helm, introduce Vault for runtime secrets, use Vault Secrets Operator for private image-pull credentials, create a minimal three-stage CI pipeline, and finish with Argo CD GitOps deployment.

You begin with only:

```text
weather-cicd-engineer-lab/
├── RUNBOOK.md
└── app/
    ├── DESIGN.md
    ├── app.py
    ├── requirements.txt
    ├── static/
    │   ├── app.js
    │   └── styles.css
    ├── templates/
    │   └── index.html
    └── tests/
        └── test_app.py
```

Nothing else in the infrastructure exists yet.

### What "done" will look like

```text
Developer source
      |
      v
GitHub
      |
      v
CI Stage 1: tests
      |
      v
CI Stage 2: build + immutable Docker Hub image
      |
      v
CI Stage 3: update Helm image tag in Git
      |
      v
Argo CD
      |
      v
KIND Kubernetes cluster
      |
      +---- Vault Agent Injector ----> application runtime secret
      |
      +---- Vault Secrets Operator --> private Docker Hub imagePullSecret
```

The lifecycle rule for the entire lab is:

```text
Build the artifact once.
Give it an immutable identity.
Put desired deployment state in Git.
Let Argo CD reconcile Git into Kubernetes.
```

### Terraform scope for this lab

Terraform has **one job only**:

```text
Terraform -> KIND cluster
```

You will **not** use Terraform to install Vault, VSO, Helm releases, the application, or Argo CD. You will perform those operations manually so you learn the tools.

---

# Part I: Prepare your workstation and source repository

## 1. Open the supplied folder in VS Code

Open Terminal and move to the extracted package.

```bash
cd ~/Downloads/weather-cicd-engineer-lab
```

Confirm your current path.

```bash
pwd
```

Inspect the starting files.

```bash
find . -maxdepth 4 -type f -print
```

Open the folder in VS Code.

```bash
code .
```

### If `code` is not available on macOS

Open VS Code manually.

Press:

```text
Command + Shift + P
```

Search for:

```text
Shell Command: Install 'code' command in PATH
```

Select it, reopen Terminal, return to the project folder, then run `code .` again.

---

## 2. Install helpful VS Code extensions

The extensions are there to help you write the files yourself. They do not bootstrap the environment.

In VS Code, open **Extensions** and install:

```text
YAML
Publisher: Red Hat
Extension ID: redhat.vscode-yaml
```

```text
GitHub Actions
Publisher: GitHub
Extension ID: GitHub.vscode-github-actions
```

```text
HashiCorp Terraform
Publisher: HashiCorp
Extension ID: hashicorp.terraform
```

CLI equivalents:

```bash
code --install-extension redhat.vscode-yaml
```

```bash
code --install-extension GitHub.vscode-github-actions
```

```bash
code --install-extension hashicorp.terraform
```

Official references:

- VS Code Marketplace: https://marketplace.visualstudio.com/
- GitHub Actions extension: https://marketplace.visualstudio.com/items?itemName=GitHub.vscode-github-actions
- Red Hat YAML: https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml
- HashiCorp Terraform: https://marketplace.visualstudio.com/items?itemName=hashicorp.terraform

---

## 3. Audit the workstation before installing anything

Run these commands one at a time.

```bash
git --version
```

```bash
gh --version
```

```bash
python3 --version
```

```bash
docker --version
```

```bash
kubectl version --client
```

```bash
helm version
```

```bash
terraform version
```

```bash
vault version
```

```bash
argocd version --client
```

A `command not found` message simply tells you what is missing.

### What each tool does

| Tool | Purpose in this lab |
|---|---|
| Git | Version control |
| GitHub CLI | Browser-assisted authentication from your terminal |
| Python | Run and test the developer's application |
| Docker | Build, run, tag, push containers |
| kubectl | Talk to Kubernetes |
| Helm | Generate and install templated Kubernetes resources |
| Terraform | Create the KIND cluster |
| Vault CLI | Configure Vault after installation |
| Argo CD CLI | Inspect and manually sync Argo CD applications |

KIND itself will be provisioned through the Terraform provider. You do not need `kind create cluster`.

---

## 4. Install missing tools

### 4.1 macOS package manager

Check Homebrew.

```bash
brew --version
```

If Homebrew is missing, open:

https://brew.sh/

Use the installation command currently shown on the official site.

### 4.2 Git and GitHub CLI

```bash
brew install git gh
```

### 4.3 kubectl

```bash
brew install kubectl
```

Official documentation:

https://kubernetes.io/docs/tasks/tools/

### 4.4 Helm

```bash
brew install helm
```

Official documentation:

https://helm.sh/docs/intro/install/

### 4.5 Terraform

```bash
brew tap hashicorp/tap
```

```bash
brew install hashicorp/tap/terraform
```

Official documentation:

https://developer.hashicorp.com/terraform/install

### 4.6 Vault CLI

```bash
brew tap hashicorp/tap
```

```bash
brew install hashicorp/tap/vault
```

Official documentation:

https://developer.hashicorp.com/vault/install

### 4.7 Argo CD CLI

```bash
brew install argocd
```

Official documentation:

https://argo-cd.readthedocs.io/en/latest/cli_installation/

### 4.8 Docker Desktop

Open:

https://docs.docker.com/desktop/setup/install/mac-install/

Install the current Docker Desktop release for your Mac and start Docker Desktop.

Verify the engine, not merely the CLI.

```bash
docker info
```

If this cannot contact the Docker engine, fix Docker before continuing.

### Linux and Windows

Use the official installation pages rather than translating the macOS commands:

- Docker: https://docs.docker.com/engine/install/
- Kubernetes CLI: https://kubernetes.io/docs/tasks/tools/
- Helm: https://helm.sh/docs/intro/install/
- Terraform: https://developer.hashicorp.com/terraform/install
- Vault: https://developer.hashicorp.com/vault/install
- Argo CD CLI: https://argo-cd.readthedocs.io/en/latest/cli_installation/

For Windows, WSL2 plus Docker Desktop integration gives the cleanest Linux-oriented path.

### Stop checkpoint

Re-run the version checks. Do not continue until the main tools are available.

---

# Part II: Understand the developer's application

## 5. Inspect the application before deploying it

In VS Code, open:

```text
app/app.py
app/templates/index.html
app/static/styles.css
app/static/app.js
app/tests/test_app.py
```

The application is called **ATMOS Weather Intelligence**.

It has:

```text
GET /
GET /healthz
GET /api/weather
```

It can:

- search weather by city,
- use browser geolocation,
- show current conditions,
- show an eight-hour forecast,
- show animated weather visuals,
- show derived "Flash Report" condition summaries,
- expose a build fingerprint through `/healthz`,
- read a Flask signing secret from `/vault/secrets/flask-secret-key` when Vault injects it.

The Flash Report is deliberately labeled as a derived summary, not an official emergency-alert system.

The live weather provider is Open-Meteo:

https://open-meteo.com/en/docs

https://open-meteo.com/en/docs/geocoding-api

---

## 6. Create a virtual environment and run the app

Create the environment.

```bash
python3 -m venv .venv
```

Activate it.

```bash
source .venv/bin/activate
```

Upgrade pip.

```bash
python -m pip install --upgrade pip
```

Install dependencies.

```bash
pip install -r app/requirements.txt
```

Compile the source.

```bash
python -m compileall -q app
```

Run the unit tests.

```bash
python -m unittest discover -s app/tests -v
```

Run the application.

```bash
python app/app.py
```

Open another terminal and verify health.

```bash
curl http://127.0.0.1:8080/healthz
```

Open:

```text
http://127.0.0.1:8080
```

Search for a city.

Try **Use my location**.

Stop the app with `Ctrl+C`.

### Expected learning

Before infrastructure exists, you have proved the developer's source works.

---

# Part III: Git and GitHub from zero

## 7. Configure Git identity

Check the current name.

```bash
git config --global user.name
```

Check the current email.

```bash
git config --global user.email
```

If needed, set your own values.

```bash
git config --global user.name "Your Name"
```

```bash
git config --global user.email "you@example.com"
```

---

## 8. Create `.gitignore`

In VS Code, create this file at the project root:

```text
.gitignore
```

Type:

```gitignore
.venv/
__pycache__/
*.pyc
.DS_Store

terraform/.terraform/
terraform/*.tfstate
terraform/*.tfstate.*
terraform/kubeconfig

.tmp/
```

Do **not** ignore `.terraform.lock.hcl`. That lock file should eventually be committed.

---

## 9. Initialize the local Git repository

```bash
git init
```

```bash
git branch -M main
```

Inspect.

```bash
git status
```

Stage the starting application.

```bash
git add .
```

Commit.

```bash
git commit -m "Initial ATMOS weather application"
```

---

## 10. Create the GitHub repository from the GitHub web console

This is the primary path for the lab.

Open:

https://github.com/

Sign in.

In the upper-right corner:

```text
+ -> New repository
```

Use:

```text
Repository name: atmos-weather-gitops-lab
Visibility: Public
```

For this first lab, **do not** select:

```text
Add a README
Add .gitignore
Choose a license
```

The repository must start empty because your files already exist locally.

Click:

```text
Create repository
```

GitHub now shows instructions for pushing an existing repository.

Official GitHub reference:

https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository

---

## 11. Authenticate your terminal with GitHub

Use GitHub CLI's browser authentication flow.

```bash
gh auth login --hostname github.com --git-protocol https --web
```

Follow the browser authorization.

Verify.

```bash
gh auth status
```

Let Git use the GitHub CLI credential.

```bash
gh auth setup-git
```

Official references:

https://cli.github.com/manual/gh_auth_login

https://cli.github.com/manual/gh_auth_setup-git

---

## 12. Connect the local repository to the GitHub repository

On your GitHub repository page, copy the HTTPS repository URL.

It looks like:

```text
https://github.com/YOUR_GITHUB_USERNAME/atmos-weather-gitops-lab.git
```

Add it.

```bash
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/atmos-weather-gitops-lab.git
```

Verify.

```bash
git remote -v
```

Push.

```bash
git push -u origin main
```

Open the repository in your browser.

```bash
gh repo view --web
```

### Stop checkpoint

You should now see the developer's application in GitHub.

---

# Part IV: Containerize, test locally, then stop using local images

## 13. Write the Dockerfile yourself

In VS Code, create:

```text
Dockerfile
```

Type:

```dockerfile
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/app.py .
COPY app/templates ./templates
COPY app/static ./static

ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION}

USER 10001:10001

EXPOSE 8080

CMD ["python", "app.py"]
```

### Understand the key lines

`FROM` selects the runtime base.

`WORKDIR` selects the application directory in the image.

The first `COPY` plus `pip install` allows Docker to cache dependency installation separately from application code.

`ARG APP_VERSION` gives the build an identity.

`ENV APP_VERSION` exposes that identity to `/healthz`.

`USER 10001:10001` avoids running the application as root.

`EXPOSE 8080` documents the internal application port.

---

## 14. Build and test the image locally

Build.

```bash
docker build --build-arg APP_VERSION=local-test -t atmos-weather:local .
```

Inspect.

```bash
docker image ls atmos-weather
```

Run.

```bash
docker run --rm --name atmos-weather-local -p 8080:8080 atmos-weather:local
```

In another terminal:

```bash
curl http://127.0.0.1:8080/healthz
```

Open:

```text
http://127.0.0.1:8080
```

Verify the animated interface and a weather search.

Stop the container with `Ctrl+C`.

This is the **last stage where `atmos-weather:local` is allowed**.

Every Kubernetes deployment later in the runbook must use a registry-hosted image.

Commit the Dockerfile.

```bash
git add Dockerfile
```

```bash
git commit -m "Containerize ATMOS weather"
```

```bash
git push
```

---

# Part V: Create a private Docker Hub repository and publish the real image

## 15. Create the private Docker Hub repository from the web console

Open:

https://hub.docker.com/

Sign in.

Navigate:

```text
My Hub -> Repositories -> Create repository
```

Choose your personal namespace.

Use:

```text
Repository name: atmos-weather
Visibility: Private
```

Click:

```text
Create
```

Official Docker reference:

https://docs.docker.com/docker-hub/repos/create/

From this point the authoritative image path will be:

```text
YOUR_DOCKER_ID/atmos-weather
```

---

## 16. Create two Docker Hub personal access tokens

You will use two separate credentials because build-time push permissions and runtime pull permissions are different jobs.

### Token A: build/push token

In Docker Hub:

```text
Avatar -> Account settings -> Personal access tokens -> Generate new token
```

Use a descriptive name such as:

```text
atmos-weather-ci-push
```

Give it:

```text
Read & Write
```

Copy the token when it appears. Docker does not show it again.

### Token B: runtime pull token

Create another token named:

```text
atmos-weather-k8s-pull
```

Give it:

```text
Read
```

Copy it.

The read-only token will later live in Vault.

Official token reference:

https://docs.docker.com/security/access-tokens/personal-access-tokens/

### Security rule

Never put either token into Git, YAML committed to Git, screenshots, chat, or the runbook.

---

## 17. Log in to Docker Hub for the first manual push

Set your Docker ID.

```bash
export DOCKERHUB_USERNAME="YOUR_DOCKER_ID"
```

Read the push token without echoing it.

```bash
read -s DOCKERHUB_PUSH_TOKEN; export DOCKERHUB_PUSH_TOKEN; echo
```

Log in.

```bash
echo "$DOCKERHUB_PUSH_TOKEN" | docker login --username "$DOCKERHUB_USERNAME" --password-stdin
```

Create an immutable tag from the current full Git commit SHA.

```bash
export IMAGE_TAG="sha-$(git rev-parse HEAD)"
```

Tag the already-tested local image.

```bash
docker tag atmos-weather:local "${DOCKERHUB_USERNAME}/atmos-weather:${IMAGE_TAG}"
```

Push.

```bash
docker push "${DOCKERHUB_USERNAME}/atmos-weather:${IMAGE_TAG}"
```

Verify the tag in Docker Hub.

You have now crossed the artifact boundary:

```text
local test image
      |
      v
private registry image with immutable Git SHA identity
```

From now on, Kubernetes uses only:

```text
YOUR_DOCKER_ID/atmos-weather:sha-<commit>
```

### Optional comparison: GHCR

GitHub Container Registry is a useful comparison because GitHub Actions can publish to `ghcr.io` with the workflow's generated `GITHUB_TOKEN` when the job grants `packages: write`.

The main lab **does not switch to GHCR**, because the private Docker Hub path is being used intentionally to teach `imagePullSecrets` and Vault-managed registry credentials.

If you later repeat the build stage with GHCR, the image shape is:

```text
ghcr.io/YOUR_GITHUB_USERNAME/atmos-weather-gitops-lab:sha-<commit>
```

Official GitHub reference:

https://docs.github.com/en/actions/tutorials/publish-packages/publish-docker-images

---

# Part VI: Provision Kubernetes with Terraform

## 18. Learn the provider from Terraform Registry first

Open:

https://registry.terraform.io/

Search:

```text
tehcyx kind
```

Open:

```text
tehcyx/kind
```

Verify that the provider is for **Kubernetes IN Docker**.

At the time this runbook was researched, the current provider version was:

```text
0.11.0
```

Do not silently use an older blog post. The Registry is the authority.

Provider page:

https://registry.terraform.io/providers/tehcyx/kind/latest

Resource documentation:

https://registry.terraform.io/providers/tehcyx/kind/latest/docs/resources/cluster

### Why KIND rather than `minikube start`

You specifically want Terraform to create the cluster.

The `tehcyx/kind` provider gives Terraform a native cluster resource. We are not disguising a shell command inside `local-exec`.

---

## 19. Create the Terraform directory

```bash
mkdir -p terraform
```

Create:

```text
terraform/versions.tf
```

Type:

```hcl
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    kind = {
      source  = "tehcyx/kind"
      version = "0.11.0"
    }
  }
}
```

Create:

```text
terraform/main.tf
```

Type:

```hcl
provider "kind" {}

resource "kind_cluster" "weather_lab" {
  name           = "weather-lab"
  wait_for_ready = true
  kubeconfig_path = abspath("${path.module}/kubeconfig")
}
```

Create:

```text
terraform/outputs.tf
```

Type:

```hcl
output "cluster_name" {
  value = kind_cluster.weather_lab.name
}

output "api_endpoint" {
  value = kind_cluster.weather_lab.endpoint
}
```

The cluster is intentionally small. KIND's default single control-plane node is enough for this lab.

---

## 20. Initialize and review Terraform

Move into the directory.

```bash
cd terraform
```

Initialize providers.

```bash
terraform init
```

Format.

```bash
terraform fmt
```

Validate.

```bash
terraform validate
```

Create a plan.

```bash
terraform plan
```

Do not type `apply` until you have read the plan.

You should see Terraform planning one KIND cluster resource.

Apply.

```bash
terraform apply
```

Type `yes` when prompted.

Return to the repository root.

```bash
cd ..
```

Set this shell to use the project-local kubeconfig.

```bash
export KUBECONFIG="$PWD/terraform/kubeconfig"
```

Verify context.

```bash
kubectl config current-context
```

Inspect the node.

```bash
kubectl get nodes -o wide
```

Inspect cluster information.

```bash
kubectl cluster-info
```

### Commit the infrastructure code, not state or kubeconfig

```bash
git add .gitignore terraform
```

```bash
git status
```

Make sure `terraform/kubeconfig` and state files are not staged.

Commit.

```bash
git commit -m "Provision KIND cluster with Terraform"
```

```bash
git push
```

### Stop checkpoint

The cluster exists because of:

```text
terraform/*.tf
```

not because you ran `kind create cluster`.

---

# Part VII: Deploy the private registry image with raw Kubernetes manifests

## 21. Create Kubernetes manifests as code

Create the directory.

```bash
mkdir -p k8s/raw
```

Create:

```text
k8s/raw/namespace.yaml
```

Type:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: weather-lab
```

Create:

```text
k8s/raw/serviceaccount.yaml
```

Type:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: atmos-weather
  namespace: weather-lab
```

Create:

```text
k8s/raw/deployment.yaml
```

Replace `YOUR_DOCKER_ID` and `YOUR_IMAGE_TAG` with the values you pushed.

For this first attempt, intentionally **do not** add `imagePullSecrets`.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: atmos-weather
  namespace: weather-lab
spec:
  replicas: 1

  selector:
    matchLabels:
      app: atmos-weather

  template:
    metadata:
      labels:
        app: atmos-weather

    spec:
      serviceAccountName: atmos-weather

      containers:
        - name: atmos-weather
          image: YOUR_DOCKER_ID/atmos-weather:YOUR_IMAGE_TAG
          imagePullPolicy: IfNotPresent

          ports:
            - name: http
              containerPort: 8080

          readinessProbe:
            httpGet:
              path: /healthz
              port: http
            initialDelaySeconds: 2
            periodSeconds: 5

          livenessProbe:
            httpGet:
              path: /healthz
              port: http
            initialDelaySeconds: 5
            periodSeconds: 10
```

Create:

```text
k8s/raw/service.yaml
```

Type:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: atmos-weather
  namespace: weather-lab
spec:
  type: ClusterIP

  selector:
    app: atmos-weather

  ports:
    - name: http
      port: 80
      targetPort: http
```

---

## 22. Validate the YAML before applying it

```bash
kubectl apply --dry-run=client -f k8s/raw/namespace.yaml
```

```bash
kubectl apply --dry-run=client -f k8s/raw/serviceaccount.yaml
```

```bash
kubectl apply --dry-run=client -f k8s/raw/deployment.yaml
```

```bash
kubectl apply --dry-run=client -f k8s/raw/service.yaml
```

---

## 23. Apply and deliberately observe the private-registry failure

Apply the namespace.

```bash
kubectl apply -f k8s/raw/namespace.yaml
```

Apply the workload files.

```bash
kubectl apply -f k8s/raw/serviceaccount.yaml
```

```bash
kubectl apply -f k8s/raw/deployment.yaml
```

```bash
kubectl apply -f k8s/raw/service.yaml
```

Watch.

```bash
kubectl get pods -n weather-lab -w
```

You are expecting a pull problem because the repository is private.

You may see:

```text
ErrImagePull
ImagePullBackOff
```

Stop the watch with `Ctrl+C`.

Describe the pod.

```bash
kubectl describe pod -n weather-lab -l app=atmos-weather
```

Read the Events section.

### What you just learned

Kubernetes knows the image name but has no credential that authorizes the node to pull from the private registry.

Official Kubernetes reference:

https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/

---

# Part VIII: Learn imagePullSecrets manually before Vault automates the credential

## 24. Create a temporary manual pull secret

This is deliberately imperative because it contains secret material.

It is a temporary learning checkpoint, not the final desired state.

Set your Docker Hub username if this terminal does not already have it.

```bash
export DOCKERHUB_USERNAME="YOUR_DOCKER_ID"
```

Read the **read-only pull token** without echoing it.

```bash
read -s DOCKERHUB_PULL_TOKEN; export DOCKERHUB_PULL_TOKEN; echo
```

Create the temporary Kubernetes registry secret.

```bash
kubectl create secret docker-registry dockerhub-pull-manual --namespace weather-lab --docker-server=https://index.docker.io/v1/ --docker-username="$DOCKERHUB_USERNAME" --docker-password="$DOCKERHUB_PULL_TOKEN"
```

Inspect only metadata and type.

```bash
kubectl get secret dockerhub-pull-manual -n weather-lab
```

Do not decode or print the credential.

---

## 25. Add the pull-secret reference to the Deployment as code

Open:

```text
k8s/raw/deployment.yaml
```

Under:

```yaml
spec:
  serviceAccountName: atmos-weather
```

add:

```yaml
      imagePullSecrets:
        - name: dockerhub-pull-manual
```

The relevant pod spec should now look like:

```yaml
spec:
  serviceAccountName: atmos-weather

  imagePullSecrets:
    - name: dockerhub-pull-manual

  containers:
    - name: atmos-weather
      image: YOUR_DOCKER_ID/atmos-weather:YOUR_IMAGE_TAG
```

Apply.

```bash
kubectl apply -f k8s/raw/deployment.yaml
```

Watch rollout.

```bash
kubectl rollout status deployment/atmos-weather -n weather-lab
```

Inspect the running image.

```bash
kubectl get deployment atmos-weather -n weather-lab -o jsonpath='{.spec.template.spec.containers[0].image}'
```

Print a newline.

```bash
echo
```

---

## 26. Reach the application in Kubernetes

```bash
kubectl port-forward service/atmos-weather -n weather-lab 8080:80
```

Open:

```text
http://127.0.0.1:8080
```

Check health in another terminal.

```bash
curl http://127.0.0.1:8080/healthz
```

At this stage `secret_source` is still the application's local fallback because Vault has not been integrated yet.

Stop port-forwarding with `Ctrl+C`.

Commit the raw manifests.

```bash
git add k8s/raw
```

```bash
git commit -m "Add raw Kubernetes deployment"
```

```bash
git push
```

---

# Part IX: Convert the application to Helm

## 27. Remove the raw workload before Helm takes ownership

Delete only the raw application resources.

```bash
kubectl delete -f k8s/raw/service.yaml
```

```bash
kubectl delete -f k8s/raw/deployment.yaml
```

```bash
kubectl delete -f k8s/raw/serviceaccount.yaml
```

Keep the namespace.

Keep the temporary registry secret.

---

## 28. Generate a chart yourself

Create the parent directory.

```bash
mkdir -p helm
```

Generate a starter chart.

```bash
helm create helm/atmos-weather
```

Inspect the generated tree.

```bash
find helm/atmos-weather -maxdepth 3 -type f -print
```

Open in VS Code:

```text
helm/atmos-weather/Chart.yaml
helm/atmos-weather/values.yaml
helm/atmos-weather/templates/
```

The exact starter chart may change between Helm releases. Inspect what your version generated.

### Understand the three major areas

```text
Chart.yaml
    chart metadata

values.yaml
    changeable input values

templates/
    Kubernetes resources containing Helm expressions
```

---

## 29. Simplify the generated chart

After inspecting the generated templates, delete the template folder.

```bash
rm -rf helm/atmos-weather/templates
```

Recreate it.

```bash
mkdir -p helm/atmos-weather/templates
```

### Replace `Chart.yaml`

```yaml
apiVersion: v2
name: atmos-weather
description: ATMOS weather application for the CI/CD learning lab
type: application
version: 0.1.0
appVersion: "1.0.0"
```

### Replace `values.yaml`

Replace the placeholders with your actual Docker ID and tag.

```yaml
replicaCount: 1

image:
  repository: YOUR_DOCKER_ID/atmos-weather
  tag: YOUR_IMAGE_TAG
  pullPolicy: IfNotPresent

imagePullSecret:
  name: dockerhub-pull-manual

service:
  type: ClusterIP
  port: 80
  targetPort: 8080

vault:
  enabled: false
  role: atmos-weather
  secretPath: secret/data/atmos-weather
```

### Create `templates/serviceaccount.yaml`

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: atmos-weather
```

### Create `templates/service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: atmos-weather
spec:
  type: {{ .Values.service.type }}

  selector:
    app: atmos-weather

  ports:
    - name: http
      port: {{ .Values.service.port }}
      targetPort: http
```

### Create `templates/deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: atmos-weather

spec:
  replicas: {{ .Values.replicaCount }}

  selector:
    matchLabels:
      app: atmos-weather

  template:
    metadata:
      labels:
        app: atmos-weather

    spec:
      serviceAccountName: atmos-weather

      imagePullSecrets:
        - name: {{ .Values.imagePullSecret.name }}

      containers:
        - name: atmos-weather
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}

          ports:
            - name: http
              containerPort: {{ .Values.service.targetPort }}

          env:
            - name: SECRET_KEY_FILE
              value: /vault/secrets/flask-secret-key

          readinessProbe:
            httpGet:
              path: /healthz
              port: http
            initialDelaySeconds: 2
            periodSeconds: 5

          livenessProbe:
            httpGet:
              path: /healthz
              port: http
            initialDelaySeconds: 5
            periodSeconds: 10
```

---

## 30. Render before installing

Lint.

```bash
helm lint helm/atmos-weather
```

Render locally.

```bash
helm template atmos-weather helm/atmos-weather --namespace weather-lab
```

Save the rendered YAML temporarily.

```bash
helm template atmos-weather helm/atmos-weather --namespace weather-lab > /tmp/atmos-weather-rendered.yaml
```

Open it.

```bash
code /tmp/atmos-weather-rendered.yaml
```

Search for:

```text
image:
imagePullSecrets:
ServiceAccount
Deployment
Service
```

`helm template` renders locally. It does not install the workload.

Official reference:

https://helm.sh/docs/helm/helm_template/

---

## 31. Install with Helm

```bash
helm install atmos-weather helm/atmos-weather --namespace weather-lab
```

Inspect release.

```bash
helm list -n weather-lab
```

Inspect Kubernetes.

```bash
kubectl get deployment,pod,service -n weather-lab
```

Wait.

```bash
kubectl rollout status deployment/atmos-weather -n weather-lab
```

Check history.

```bash
helm history atmos-weather -n weather-lab
```

### Practice upgrade

Change `replicaCount` temporarily to `2`.

Render again.

```bash
helm template atmos-weather helm/atmos-weather --namespace weather-lab > /tmp/atmos-weather-upgrade.yaml
```

Upgrade.

```bash
helm upgrade atmos-weather helm/atmos-weather --namespace weather-lab
```

Verify two pods.

```bash
kubectl get pods -n weather-lab
```

Restore `replicaCount: 1` and upgrade again.

```bash
helm upgrade atmos-weather helm/atmos-weather --namespace weather-lab
```

Commit the chart.

```bash
git add helm
```

```bash
git commit -m "Package ATMOS weather with Helm"
```

```bash
git push
```

---

# Part X: Install Vault manually with Helm

## 32. Read HashiCorp's installation guidance

Open:

https://developer.hashicorp.com/vault/docs/deploy/kubernetes/helm/run

Open:

https://developer.hashicorp.com/vault/docs/deploy/kubernetes/injector/installation

The official Vault Helm chart is the path you will use.

This lab uses **dev mode** because the goal is Kubernetes authentication and secret injection, not production Vault operations.

Dev mode is in-memory, automatically unsealed, insecure, and loses data when restarted.

---

## 33. Create Vault configuration as code

Create:

```bash
mkdir -p platform/vault/policies platform/vault/auth platform/vault/roles
```

Create:

```text
platform/vault/namespace.yaml
```

Type:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: vault
```

Create:

```text
platform/vault/values.yaml
```

Type:

```yaml
server:
  dev:
    enabled: true
    devRootToken: root

injector:
  enabled: true
```

The literal `root` token is acceptable only for this disposable learning environment.

---

## 34. Add HashiCorp's Helm repository and inspect Vault

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
```

```bash
helm repo update
```

Search.

```bash
helm search repo hashicorp/vault
```

At the time this runbook was researched, the official chart was:

```text
Vault chart 0.34.1
Vault app 2.0.4
```

Inspect chart values.

```bash
helm show values hashicorp/vault --version 0.34.1 > /tmp/vault-chart-values.yaml
```

Open them.

```bash
code /tmp/vault-chart-values.yaml
```

Search for:

```text
dev:
devRootToken:
injector:
```

---

## 35. Render Vault before installing it

```bash
helm template vault hashicorp/vault --version 0.34.1 --namespace vault --values platform/vault/values.yaml > /tmp/vault-rendered.yaml
```

Open the rendered resources.

```bash
code /tmp/vault-rendered.yaml
```

Look for the Vault server, Service, ServiceAccount, and injector webhook resources.

---

## 36. Install Vault

Create the namespace from the file you wrote.

```bash
kubectl apply -f platform/vault/namespace.yaml
```

Install the pinned chart using the committed values file.

```bash
helm install vault hashicorp/vault --version 0.34.1 --namespace vault --values platform/vault/values.yaml
```

Watch pods.

```bash
kubectl get pods -n vault -w
```

Stop watching when Vault and the injector are ready.

Verify.

```bash
helm list -n vault
```

```bash
kubectl get pods,service -n vault
```

---

# Part XI: Configure Vault as code, then load secret values separately

## 37. Create the Kubernetes auth configuration file

Create:

```text
platform/vault/auth/kubernetes-mount.json
```

Type:

```json
{
  "type": "kubernetes"
}
```

This file represents the Kubernetes auth-method mount itself.

Create:

```text
platform/vault/auth/kubernetes-config.json
```

Type:

```json
{
  "kubernetes_host": "https://kubernetes.default.svc:443"
}
```

Vault is running inside the same Kubernetes cluster, so it can use the cluster-local API address.

---

## 38. Create the application policy

Create:

```text
platform/vault/policies/atmos-weather.hcl
```

Type:

```hcl
path "secret/data/atmos-weather" {
  capabilities = ["read"]
}
```

Create:

```text
platform/vault/roles/atmos-weather.json
```

Type:

```json
{
  "bound_service_account_names": [
    "atmos-weather"
  ],
  "bound_service_account_namespaces": [
    "weather-lab"
  ],
  "policies": [
    "atmos-weather"
  ],
  "ttl": "1h"
}
```

---

## 39. Create the VSO pull-secret policy and role files

Create:

```text
platform/vault/policies/dockerhub-pull.hcl
```

Type:

```hcl
path "secret/data/dockerhub" {
  capabilities = ["read"]
}
```

Create:

```text
platform/vault/roles/dockerhub-vso.json
```

Type:

```json
{
  "bound_service_account_names": [
    "vso-dockerhub"
  ],
  "bound_service_account_namespaces": [
    "weather-lab"
  ],
  "policies": [
    "dockerhub-pull"
  ],
  "ttl": "1h"
}
```

Now the non-secret parts of Vault's application access model are represented in Git.

---

## 40. Port-forward Vault and configure it

In one terminal:

```bash
kubectl port-forward service/vault -n vault 8200:8200
```

Leave that terminal running.

In another terminal, export the lab Vault address and token.

```bash
export VAULT_ADDR="http://127.0.0.1:8200" VAULT_TOKEN="root"
```

Verify.

```bash
vault status
```

Enable the Kubernetes auth mount from the configuration file you created.

```bash
vault write sys/auth/kubernetes @platform/vault/auth/kubernetes-mount.json
```

Verify the mount.

```bash
vault auth list
```

Apply the auth configuration from the file.

```bash
vault write auth/kubernetes/config @platform/vault/auth/kubernetes-config.json
```

Apply the application policy.

```bash
vault policy write atmos-weather platform/vault/policies/atmos-weather.hcl
```

Apply the application role.

```bash
vault write auth/kubernetes/role/atmos-weather @platform/vault/roles/atmos-weather.json
```

Apply the pull-secret policy.

```bash
vault policy write dockerhub-pull platform/vault/policies/dockerhub-pull.hcl
```

Apply the VSO role.

```bash
vault write auth/kubernetes/role/dockerhub-vso @platform/vault/roles/dockerhub-vso.json
```

---

## 41. Store the application secret value

Generate a random Flask signing key.

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Copy it.

Store it in Vault.

```bash
vault kv put secret/atmos-weather flask_secret_key='PASTE_GENERATED_VALUE_HERE'
```

The value is deliberately **not** represented in Git.

Check metadata/value only in your private terminal.

```bash
vault kv get secret/atmos-weather
```

---

# Part XII: Make the Helm application use Vault Agent Injector

## 42. Add injector annotations to the Helm Deployment

Open:

```text
helm/atmos-weather/templates/deployment.yaml
```

Inside:

```yaml
template:
  metadata:
```

change the metadata section to:

```yaml
template:
  metadata:
    labels:
      app: atmos-weather

    {{- if .Values.vault.enabled }}
    annotations:
      vault.hashicorp.com/agent-inject: "true"
      vault.hashicorp.com/agent-pre-populate-only: "true"
      vault.hashicorp.com/role: {{ .Values.vault.role | quote }}
      vault.hashicorp.com/agent-inject-secret-flask-secret-key: {{ .Values.vault.secretPath | quote }}
      vault.hashicorp.com/agent-inject-template-flask-secret-key: |
        {{`{{- with secret "secret/data/atmos-weather" -}}`}}
        {{`{{ .Data.data.flask_secret_key }}`}}
        {{`{{- end -}}`}}
    {{- end }}
```

The double-templating looks unusual because Helm must preserve the inner Vault template.

---

## 43. Enable Vault in `values.yaml`

Change:

```yaml
vault:
  enabled: false
```

to:

```yaml
vault:
  enabled: true
```

Lint.

```bash
helm lint helm/atmos-weather
```

Render.

```bash
helm template atmos-weather helm/atmos-weather --namespace weather-lab > /tmp/atmos-with-vault.yaml
```

Open.

```bash
code /tmp/atmos-with-vault.yaml
```

Search for:

```text
vault.hashicorp.com/agent-inject
```

Upgrade.

```bash
helm upgrade atmos-weather helm/atmos-weather --namespace weather-lab
```

Wait.

```bash
kubectl rollout status deployment/atmos-weather -n weather-lab
```

Prove the injected file exists without printing the secret.

```bash
kubectl exec deployment/atmos-weather -n weather-lab -c atmos-weather -- sh -c 'test -s /vault/secrets/flask-secret-key && echo "Vault secret file is present"'
```

Port-forward.

```bash
kubectl port-forward service/atmos-weather -n weather-lab 8080:80
```

Check health.

```bash
curl http://127.0.0.1:8080/healthz
```

You want:

```text
"secret_source": "vault-file"
```

Stop port forwarding.

Commit the non-secret Vault and Helm changes.

```bash
git add platform/vault helm/atmos-weather
```

```bash
git commit -m "Add Vault runtime secret injection"
```

```bash
git push
```

---

# Part XIII: Install Vault Secrets Operator and move the private-registry credential into Vault

## 44. Understand why the Agent Injector cannot solve image pulling

The container runtime needs Docker Hub credentials **before the application image can start**.

A Vault sidecar or init container inside that application pod cannot provide credentials for an image that has not yet been pulled.

The final path must therefore be:

```text
Vault
  |
  v
Vault Secrets Operator
  |
  v
Kubernetes Secret type kubernetes.io/dockerconfigjson
  |
  v
imagePullSecrets
  |
  v
private Docker Hub image
```

HashiCorp documents `VaultStaticSecret` specifically for `imagePullSecrets`.

Official references:

https://developer.hashicorp.com/vault/docs/deploy/kubernetes/vso/installation

https://developer.hashicorp.com/vault/docs/deploy/kubernetes/vso/examples

---

## 45. Create VSO installation configuration as code

Create:

```bash
mkdir -p platform/vso
```

Create:

```text
platform/vso/namespace.yaml
```

Type:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: vault-secrets-operator
```

Create:

```text
platform/vso/values.yaml
```

For this minimal lab, use:

```yaml
controller:
  manager:
    resources:
      requests:
        cpu: 50m
        memory: 64Mi
      limits:
        memory: 256Mi
```

Search the official chart.

```bash
helm search repo hashicorp/vault-secrets-operator
```

At the time this runbook was researched, the official chart version was:

```text
1.6.0
```

Inspect chart values.

```bash
helm show values hashicorp/vault-secrets-operator --version 1.6.0 > /tmp/vso-values.yaml
```

Render.

```bash
helm template vault-secrets-operator hashicorp/vault-secrets-operator --version 1.6.0 --namespace vault-secrets-operator --values platform/vso/values.yaml > /tmp/vso-rendered.yaml
```

Open.

```bash
code /tmp/vso-rendered.yaml
```

Create the namespace from code.

```bash
kubectl apply -f platform/vso/namespace.yaml
```

Install.

```bash
helm install vault-secrets-operator hashicorp/vault-secrets-operator --version 1.6.0 --namespace vault-secrets-operator --values platform/vso/values.yaml
```

Verify.

```bash
kubectl get pods -n vault-secrets-operator
```

Verify CRDs exist.

```bash
kubectl get crd | grep secrets.hashicorp.com
```

---

## 46. Create VSO authentication and synchronization objects as code

Create:

```text
platform/vso/dockerhub-pull.yaml
```

Type:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: vso-dockerhub
  namespace: weather-lab

---
apiVersion: secrets.hashicorp.com/v1beta1
kind: VaultConnection
metadata:
  name: vault
  namespace: weather-lab
spec:
  address: http://vault.vault.svc.cluster.local:8200

---
apiVersion: secrets.hashicorp.com/v1beta1
kind: VaultAuth
metadata:
  name: dockerhub
  namespace: weather-lab
spec:
  vaultConnectionRef: vault
  method: kubernetes
  mount: kubernetes

  kubernetes:
    role: dockerhub-vso
    serviceAccount: vso-dockerhub

---
apiVersion: secrets.hashicorp.com/v1beta1
kind: VaultStaticSecret
metadata:
  name: dockerhub-pull
  namespace: weather-lab
spec:
  vaultAuthRef: dockerhub
  type: kv-v2
  mount: secret
  path: dockerhub
  refreshAfter: 30s

  destination:
    name: dockerhub-pull
    create: true
    type: kubernetes.io/dockerconfigjson
```

Do not apply it until the Vault value exists.

---

## 47. Build a Docker config file from the read-only token without committing it

Create a private temporary directory.

```bash
mkdir -p .tmp
```

Set the username if needed.

```bash
export DOCKERHUB_USERNAME="YOUR_DOCKER_ID"
```

If the pull token is not already in this terminal, read it again.

```bash
read -s DOCKERHUB_PULL_TOKEN; export DOCKERHUB_PULL_TOKEN; echo
```

Create a temporary Docker config JSON with Python.

```bash
python3 -c 'import os,json,base64,pathlib; u=os.environ["DOCKERHUB_USERNAME"]; p=os.environ["DOCKERHUB_PULL_TOKEN"]; a=base64.b64encode(f"{u}:{p}".encode()).decode(); pathlib.Path(".tmp/dockerconfig.json").write_text(json.dumps({"auths":{"https://index.docker.io/v1/":{"username":u,"password":p,"auth":a}}}))'
```

Confirm only that the file exists.

```bash
test -s .tmp/dockerconfig.json && echo "temporary docker config created"
```

Do not print it.

Store that JSON as the special `.dockerconfigjson` field in Vault.

```bash
vault kv put secret/dockerhub .dockerconfigjson=@.tmp/dockerconfig.json
```

Remove the temporary file.

```bash
rm -f .tmp/dockerconfig.json
```

Unset the pull token from this shell.

```bash
unset DOCKERHUB_PULL_TOKEN
```

---

## 48. Apply the VSO resources

```bash
kubectl apply -f platform/vso/dockerhub-pull.yaml
```

Inspect the custom resources.

```bash
kubectl get vaultconnection,vaultauth,vaultstaticsecret -n weather-lab
```

Wait for VSO to create the destination Secret.

```bash
kubectl get secret dockerhub-pull -n weather-lab
```

Verify the Secret type.

```bash
kubectl get secret dockerhub-pull -n weather-lab -o jsonpath='{.type}'
```

Print a newline.

```bash
echo
```

Expected:

```text
kubernetes.io/dockerconfigjson
```

Do not decode or print the secret data.

---

## 49. Switch the Helm workload from the manual secret to the Vault-managed secret

Open:

```text
helm/atmos-weather/values.yaml
```

Change:

```yaml
imagePullSecret:
  name: dockerhub-pull-manual
```

to:

```yaml
imagePullSecret:
  name: dockerhub-pull
```

Lint.

```bash
helm lint helm/atmos-weather
```

Render.

```bash
helm template atmos-weather helm/atmos-weather --namespace weather-lab > /tmp/atmos-vso.yaml
```

Upgrade.

```bash
helm upgrade atmos-weather helm/atmos-weather --namespace weather-lab
```

Wait.

```bash
kubectl rollout status deployment/atmos-weather -n weather-lab
```

Delete the old temporary manual credential.

```bash
kubectl delete secret dockerhub-pull-manual -n weather-lab
```

Force a new pod so you prove the private image can still be pulled with only the Vault-managed credential.

```bash
kubectl rollout restart deployment/atmos-weather -n weather-lab
```

Wait.

```bash
kubectl rollout status deployment/atmos-weather -n weather-lab
```

Inspect the new pod.

```bash
kubectl get pods -n weather-lab -o wide
```

### What you have proved

Two different Vault patterns now exist:

```text
Vault Agent Injector
-> application runtime file secret

Vault Secrets Operator
-> Kubernetes dockerconfigjson Secret
-> imagePullSecrets
-> private image pull
```

Commit.

```bash
git add platform/vso helm/atmos-weather
```

```bash
git commit -m "Manage Docker Hub pull credential through Vault"
```

```bash
git push
```

---

# Part XIV: Create the minimal three-stage CI pipeline

## 50. Add GitHub repository secrets for Docker Hub

Open your GitHub repository.

Navigate:

```text
Settings -> Secrets and variables -> Actions -> New repository secret
```

Create:

```text
Name: DOCKERHUB_USERNAME
Value: your Docker ID
```

Create:

```text
Name: DOCKERHUB_TOKEN
Value: the Read & Write Docker Hub token
```

Do **not** put the Kubernetes read-only pull token into GitHub Actions. That token belongs in Vault.

---

## 51. Allow this training workflow to update desired state in Git

Navigate:

```text
Settings -> Actions -> General -> Workflow permissions
```

For this single-repository training pattern, choose:

```text
Read and write permissions
```

Save.

In a production repository you would normally introduce protected branches, pull requests, environments, and narrower promotion controls. This lab intentionally avoids that complexity.

---

## 52. Create CI Stage 1 only

Create:

```bash
mkdir -p .github/workflows
```

Create in VS Code:

```text
.github/workflows/ci.yml
```

Start with only this:

```yaml
name: atmos-ci

on:
  pull_request:

  push:
    branches:
      - main

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Check out repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"

      - name: Install dependencies
        run: pip install -r app/requirements.txt

      - name: Compile
        run: python -m compileall -q app

      - name: Run tests
        run: python -m unittest discover -s app/tests -v
```

Your VS Code GitHub Actions extension should help validate the structure.

Commit Stage 1.

```bash
git add .github/workflows/ci.yml
```

```bash
git commit -m "Add CI test stage"
```

```bash
git push
```

Open the Actions tab in GitHub.

Do not add Stage 2 until `test` is green.

---

## 53. Add CI Stage 2: build and push to private Docker Hub

Open:

```text
.github/workflows/ci.yml
```

Add this job under `test`:

```yaml
  build:
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

    needs:
      - test

    runs-on: ubuntu-latest

    steps:
      - name: Check out repository
        uses: actions/checkout@v7

      - name: Log in to Docker Hub
        run: echo "${{ secrets.DOCKERHUB_TOKEN }}" | docker login --username "${{ secrets.DOCKERHUB_USERNAME }}" --password-stdin

      - name: Build immutable image
        run: docker build --build-arg APP_VERSION="sha-${GITHUB_SHA}" --tag "${{ secrets.DOCKERHUB_USERNAME }}/atmos-weather:sha-${GITHUB_SHA}" .

      - name: Push immutable image
        run: docker push "${{ secrets.DOCKERHUB_USERNAME }}/atmos-weather:sha-${GITHUB_SHA}"
```

The dependency:

```yaml
needs:
  - test
```

means a failing test blocks image publication.

Commit.

```bash
git add .github/workflows/ci.yml
```

```bash
git commit -m "Build and publish immutable Docker image"
```

```bash
git push
```

Watch:

```text
test -> build
```

Open Docker Hub and verify the new `sha-...` tag exists.

---

## 54. Add CI Stage 3: update Git desired state

Add:

```yaml
  update-gitops:
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

    needs:
      - build

    runs-on: ubuntu-latest

    permissions:
      contents: write

    steps:
      - name: Check out repository
        uses: actions/checkout@v7

      - name: Update image tag
        run: sed -i "s|^  tag:.*|  tag: \"sha-${GITHUB_SHA}\"|" helm/atmos-weather/values.yaml

      - name: Show desired-state change
        run: git diff -- helm/atmos-weather/values.yaml

      - name: Configure Git identity
        run: git config user.name "github-actions[bot]" && git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

      - name: Commit desired state
        run: git add helm/atmos-weather/values.yaml && git diff --cached --check && (git diff --cached --quiet || git commit -m "gitops: deploy sha-${GITHUB_SHA}")

      - name: Push desired state
        run: git push
```

The final pipeline is:

```text
test
  |
  v
build
  |
  v
update-gitops
```

It does **not** run `kubectl apply`.

It does **not** run `helm upgrade`.

It does **not** run `argocd app sync`.

The CI system changes Git desired state.

Commit.

```bash
git add .github/workflows/ci.yml
```

```bash
git commit -m "Update GitOps desired state from CI"
```

```bash
git push
```

When the workflow completes, pull the bot-generated commit.

```bash
git pull --ff-only
```

Inspect history.

```bash
git log --oneline -8
```

Inspect the Helm tag.

```bash
grep -A3 '^image:' helm/atmos-weather/values.yaml
```

---

# Part XV: Hand application ownership from manual Helm to Argo CD

## 55. Remove the manually managed Helm release

Argo CD is about to manage the same chart.

Do not let local Helm CLI and Argo CD compete over the same application.

```bash
helm uninstall atmos-weather -n weather-lab
```

Verify the application resources disappear.

```bash
kubectl get deployment,service,pod -n weather-lab
```

Keep Vault, VSO, and the `dockerhub-pull` Secret.

---

# Part XVI: Install Argo CD manually, but keep the installation as code

## 56. Create an Argo CD directory

```bash
mkdir -p platform/argocd
```

Create:

```text
platform/argocd/namespace.yaml
```

Type:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: argocd
```

---

## 57. Vendor a pinned Argo CD installation manifest

At the time this runbook was researched, the current stable Argo CD release was:

```text
v3.5.3
```

Download that exact official manifest into the repository.

```bash
curl -fsSL https://raw.githubusercontent.com/argoproj/argo-cd/v3.5.3/manifests/install.yaml -o platform/argocd/install.yaml
```

Open it in VS Code before applying it.

```bash
code platform/argocd/install.yaml
```

The pinned file means your repository records what you installed instead of tracking the changing `stable` branch.

Official Argo CD Getting Started:

https://argo-cd.readthedocs.io/en/latest/getting_started/

Release reference:

https://github.com/argoproj/argo-cd/releases

---

## 58. Apply the Argo CD installation from the files in Git

Create namespace.

```bash
kubectl apply -f platform/argocd/namespace.yaml
```

Apply Argo CD server-side.

```bash
kubectl apply -n argocd --server-side --force-conflicts -f platform/argocd/install.yaml
```

Watch.

```bash
kubectl get pods -n argocd -w
```

Stop when ready.

Inspect.

```bash
kubectl get all -n argocd
```

---

## 59. Access Argo CD

Get the initial password.

```bash
argocd admin initial-password -n argocd
```

Start a port-forward.

```bash
kubectl port-forward service/argocd-server -n argocd 8443:443
```

Open:

```text
https://127.0.0.1:8443
```

Username:

```text
admin
```

Use the initial password.

The browser warning about a local self-signed certificate is expected in this lab.

From another terminal, log in with the CLI.

```bash
argocd login 127.0.0.1:8443 --username admin --password 'PASTE_INITIAL_PASSWORD' --insecure
```

Change the password if you want to practice the account workflow.

```bash
argocd account update-password
```

---

# Part XVII: Define the Argo CD Application as code

## 60. Create the Application manifest with manual sync first

Create:

```text
platform/argocd/atmos-weather.yaml
```

Replace `YOUR_GITHUB_USERNAME`.

Type:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: atmos-weather
  namespace: argocd

spec:
  project: default

  source:
    repoURL: https://github.com/YOUR_GITHUB_USERNAME/atmos-weather-gitops-lab.git
    targetRevision: main
    path: helm/atmos-weather

  destination:
    server: https://kubernetes.default.svc
    namespace: weather-lab

  syncPolicy:
    syncOptions:
      - CreateNamespace=true
```

Commit the Argo CD installation and Application definitions.

```bash
git add platform/argocd
```

```bash
git commit -m "Add Argo CD platform and application manifests"
```

```bash
git push
```

Apply the Application.

```bash
kubectl apply -f platform/argocd/atmos-weather.yaml
```

Inspect.

```bash
argocd app get atmos-weather
```

Before the first sync, `OutOfSync` is useful. Git declares the app, but the cluster does not yet match.

---

## 61. Perform one manual sync

```bash
argocd app sync atmos-weather
```

Watch rollout.

```bash
kubectl rollout status deployment/atmos-weather -n weather-lab
```

Inspect application state.

```bash
argocd app get atmos-weather
```

You want:

```text
Synced
Healthy
```

Prove the running image.

```bash
kubectl get deployment atmos-weather -n weather-lab -o jsonpath='{.spec.template.spec.containers[0].image}'
```

```bash
echo
```

Compare it to:

```text
helm/atmos-weather/values.yaml
```

---

## 62. Enable automated GitOps as code

Edit:

```text
platform/argocd/atmos-weather.yaml
```

Change `syncPolicy` to:

```yaml
  syncPolicy:
    automated:
      enabled: true
      prune: true
      selfHeal: true

    syncOptions:
      - CreateNamespace=true
```

Commit.

```bash
git add platform/argocd/atmos-weather.yaml
```

```bash
git commit -m "Enable Argo CD automated reconciliation"
```

```bash
git push
```

Apply the updated Argo CD Application definition.

```bash
kubectl apply -f platform/argocd/atmos-weather.yaml
```

Inspect.

```bash
argocd app get atmos-weather
```

### Meaning

`enabled: true` allows automatic synchronization.

`prune: true` allows resources deleted from desired state to be removed.

`selfHeal: true` allows Argo CD to correct live drift.

---

# Part XVIII: Run the complete ticket from source to runtime

## 63. Make a visible application change

Open:

```text
app/templates/index.html
```

Change one visible sentence.

Do not modify infrastructure.

---

## 64. Test locally before pushing

```bash
source .venv/bin/activate
```

```bash
python -m compileall -q app
```

```bash
python -m unittest discover -s app/tests -v
```

---

## 65. Commit and push

```bash
git add app/templates/index.html
```

```bash
git commit -m "Update ATMOS interface copy"
```

```bash
git push
```

Now watch:

```text
Git push
  |
  v
CI test
  |
  v
CI build
  |
  v
Docker Hub private sha-<commit>
  |
  v
CI updates Helm tag in Git
  |
  v
Argo CD notices desired-state change
  |
  v
Kubernetes rolls out exact private image
```

---

## 66. Pull the CI-generated GitOps commit locally

```bash
git pull --ff-only
```

Inspect.

```bash
git log --oneline -8
```

Inspect desired image.

```bash
grep -A3 '^image:' helm/atmos-weather/values.yaml
```

---

## 67. Prove Argo CD and Kubernetes converged

```bash
argocd app get atmos-weather
```

```bash
kubectl rollout status deployment/atmos-weather -n weather-lab
```

Ask Kubernetes for the exact image.

```bash
kubectl get deployment atmos-weather -n weather-lab -o jsonpath='{.spec.template.spec.containers[0].image}'
```

```bash
echo
```

The image should match the Helm value committed by CI.

---

## 68. Prove the final application and both secret paths

Port-forward.

```bash
kubectl port-forward service/atmos-weather -n weather-lab 8080:80
```

Health.

```bash
curl http://127.0.0.1:8080/healthz
```

You want:

```text
status = ok
version = sha-...
secret_source = vault-file
```

Open the browser.

```text
http://127.0.0.1:8080
```

You should see the polished ATMOS interface and your visible change.

In another terminal, verify the pull secret still exists and is the correct type.

```bash
kubectl get secret dockerhub-pull -n weather-lab -o jsonpath='{.type}'
```

```bash
echo
```

Stop port-forwarding.

---

# Part XIX: Deliberately create GitOps drift

## 69. Scale outside Git

Git says:

```yaml
replicaCount: 1
```

Create drift.

```bash
kubectl scale deployment/atmos-weather -n weather-lab --replicas=3
```

Watch.

```bash
kubectl get deployment atmos-weather -n weather-lab -w
```

Because Argo CD self-healing is enabled, desired state should eventually return the deployment toward the Git value.

Inspect:

```bash
argocd app get atmos-weather
```

The lesson is:

```text
kubectl changed live state
Git remained desired state
Argo CD reconciled live state
```

---

# Part XX: Troubleshoot by layer instead of randomly changing things

## 70. Application layer

```bash
python -m compileall -q app
```

```bash
python -m unittest discover -s app/tests -v
```

```bash
python app/app.py
```

---

## 71. Docker layer

```bash
docker image ls
```

```bash
docker ps -a
```

```bash
docker logs atmos-weather-local
```

---

## 72. Terraform/KIND layer

```bash
terraform -chdir=terraform validate
```

```bash
terraform -chdir=terraform state list
```

```bash
kubectl get nodes -o wide
```

---

## 73. Kubernetes layer

```bash
kubectl get pods -A
```

```bash
kubectl get events -n weather-lab --sort-by=.lastTimestamp
```

```bash
kubectl describe deployment atmos-weather -n weather-lab
```

```bash
kubectl describe pod -n weather-lab -l app=atmos-weather
```

```bash
kubectl logs deployment/atmos-weather -n weather-lab -c atmos-weather
```

---

## 74. Private image-pull layer

If you see `ImagePullBackOff`:

```bash
kubectl describe pod -n weather-lab -l app=atmos-weather
```

Check the Deployment's secret reference.

```bash
kubectl get deployment atmos-weather -n weather-lab -o jsonpath='{.spec.template.spec.imagePullSecrets[*].name}'
```

```bash
echo
```

Verify the destination Secret exists.

```bash
kubectl get secret dockerhub-pull -n weather-lab
```

Verify its type.

```bash
kubectl get secret dockerhub-pull -n weather-lab -o jsonpath='{.type}'
```

```bash
echo
```

Do not dump its data.

---

## 75. Helm layer

```bash
helm lint helm/atmos-weather
```

```bash
helm template atmos-weather helm/atmos-weather --namespace weather-lab
```

If Argo CD owns the app, do not casually run `helm upgrade`. Render for diagnosis, then change Git.

---

## 76. Vault layer

```bash
kubectl get pods -n vault
```

```bash
kubectl logs deployment/vault-agent-injector -n vault
```

```bash
vault status
```

```bash
vault auth list
```

```bash
vault policy read atmos-weather
```

```bash
vault read auth/kubernetes/role/atmos-weather
```

```bash
vault policy read dockerhub-pull
```

```bash
vault read auth/kubernetes/role/dockerhub-vso
```

---

## 77. VSO layer

```bash
kubectl get pods -n vault-secrets-operator
```

```bash
kubectl get vaultconnection,vaultauth,vaultstaticsecret -n weather-lab
```

```bash
kubectl describe vaultstaticsecret dockerhub-pull -n weather-lab
```

```bash
kubectl logs deployment/vault-secrets-operator-controller-manager -n vault-secrets-operator
```

If the exact Deployment name differs in your installed chart version, first list the Deployments.

```bash
kubectl get deployment -n vault-secrets-operator
```

---

## 78. GitHub Actions layer

For a test failure, reproduce it locally.

For a Docker Hub login/push failure, verify these repository secrets exist:

```text
DOCKERHUB_USERNAME
DOCKERHUB_TOKEN
```

For a Git push failure from the GitOps job, verify:

```text
Settings -> Actions -> General -> Workflow permissions -> Read and write
```

---

## 79. Argo CD layer

```bash
argocd app get atmos-weather
```

```bash
argocd app diff atmos-weather
```

```bash
kubectl get pods -n argocd
```

```bash
kubectl describe application atmos-weather -n argocd
```

---

# Part XXI: Clean teardown

## 80. Delete the Argo CD application

```bash
kubectl delete -f platform/argocd/atmos-weather.yaml
```

---

## 81. Remove Argo CD

```bash
kubectl delete -n argocd --ignore-not-found -f platform/argocd/install.yaml
```

```bash
kubectl delete -f platform/argocd/namespace.yaml
```

---

## 82. Remove VSO

```bash
helm uninstall vault-secrets-operator -n vault-secrets-operator
```

---

## 83. Remove Vault

```bash
helm uninstall vault -n vault
```

---

## 84. Destroy the KIND cluster through Terraform

```bash
terraform -chdir=terraform destroy
```

Confirm the destroy.

Verify the cluster is gone.

```bash
terraform -chdir=terraform state list
```

Your GitHub repository and Docker Hub repository remain.

---

# Part XXII: What you deliberately did not add

This lab intentionally does not include:

```text
SonarQube
Checkov
Trivy
Gitleaks
Kyverno
Prometheus
Grafana
Loki
Jaeger
Ingress
cert-manager
cloud IAM
external databases
HA Vault
multiple environments
separate GitOps repository
PR-based promotion
```

Those can be added later.

The important lifecycle is already present:

```text
source
-> local tests
-> local container validation
-> immutable private registry artifact
-> Terraform-created Kubernetes
-> private image authentication
-> raw Kubernetes
-> Helm
-> Vault runtime secret
-> Vault-managed image-pull secret
-> CI
-> Git desired state
-> Argo CD
-> Kubernetes runtime
-> verification
```

---

# Part XXIII: Knowledge check

You should be able to answer these without looking at the commands.

## Git and GitHub

What is the difference between your local repository and GitHub?

What is `origin`?

What did `git push -u origin main` establish?

Why did you create the repository in the GitHub console before adding the remote locally?

## Docker

Why did you locally run the image before pushing it?

Why does Kubernetes never use `atmos-weather:local` in this lab?

Why is `sha-<commit>` a stronger deployment identity than `latest`?

What is the difference between the Docker Hub push token and pull token?

## Terraform

What did `terraform init` do?

What did `terraform plan` show?

Which provider created the KIND cluster?

Why does Terraform own only the cluster in this lab?

What is the difference between Terraform configuration and Terraform state?

## Kubernetes

What is a Deployment?

What is a Service?

What is a ServiceAccount?

Why did the first private-image deployment enter `ImagePullBackOff`?

What does `imagePullSecrets` reference?

Why must that Secret be in the same namespace as the Pod?

## Helm

What did `helm create` generate?

What does `values.yaml` do?

What does `helm template` do?

Why did you render before installing?

What changed when Helm replaced the raw manifests?

## Vault

What does the application Vault policy allow?

How did the application authenticate to Vault without a hard-coded Vault token?

What did the Agent Injector create inside the pod?

Why is dev-mode Vault not production-safe?

## Vault Secrets Operator

Why can the Agent Injector not solve a private image pull?

What does VSO synchronize?

What Kubernetes Secret type is used for Docker registry credentials?

Why did the final Deployment reference `dockerhub-pull` instead of `dockerhub-pull-manual`?

## CI

What prevents `build` from running when tests fail?

What does the build job publish?

What does the GitOps job modify?

Why does CI not run `kubectl apply`?

## Argo CD

What did `OutOfSync` mean?

What did manual sync teach you?

What do automated sync, prune, and self-heal do?

Why is Git the desired-state authority?

---

# Part XXIV: Official documentation map

These are the documentation families this runbook is based on. Tool versions and interfaces change, so use the official source if a future screen or option differs.

## GitHub

Repository creation:

https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository

GitHub CLI authentication:

https://cli.github.com/manual/gh_auth_login

GitHub Actions workflow syntax:

https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax

Publishing Docker images:

https://docs.github.com/en/actions/tutorials/publish-packages/publish-docker-images

`GITHUB_TOKEN`:

https://docs.github.com/en/actions/concepts/security/github_token

## Docker

Docker Desktop:

https://docs.docker.com/desktop/

Create Docker Hub repository:

https://docs.docker.com/docker-hub/repos/create/

Docker Hub PATs:

https://docs.docker.com/security/access-tokens/personal-access-tokens/

## Terraform and KIND

Terraform install:

https://developer.hashicorp.com/terraform/install

Terraform Registry:

https://registry.terraform.io/

KIND provider:

https://registry.terraform.io/providers/tehcyx/kind/latest

KIND cluster resource:

https://registry.terraform.io/providers/tehcyx/kind/latest/docs/resources/cluster

## Kubernetes

kubectl installation:

https://kubernetes.io/docs/tasks/tools/

Services:

https://kubernetes.io/docs/concepts/services-networking/service/

Private images:

https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/

Port forwarding:

https://kubernetes.io/docs/tasks/access-application-cluster/port-forward-access-application-cluster/

## Helm

Installation:

https://helm.sh/docs/intro/install/

Chart template guide:

https://helm.sh/docs/chart_template_guide/

`helm template`:

https://helm.sh/docs/helm/helm_template/

## Vault

Install:

https://developer.hashicorp.com/vault/install

Kubernetes Helm deployment:

https://developer.hashicorp.com/vault/docs/deploy/kubernetes/helm/run

Agent Injector:

https://developer.hashicorp.com/vault/docs/deploy/kubernetes/injector/installation

Kubernetes authentication:

https://developer.hashicorp.com/vault/docs/auth/kubernetes

## Vault Secrets Operator

Installation:

https://developer.hashicorp.com/vault/docs/deploy/kubernetes/vso/installation

Vault source:

https://developer.hashicorp.com/vault/docs/deploy/kubernetes/vso/sources/vault

Examples including imagePullSecrets:

https://developer.hashicorp.com/vault/docs/deploy/kubernetes/vso/examples

## Argo CD

Getting started:

https://argo-cd.readthedocs.io/en/latest/getting_started/

Application specification:

https://argo-cd.readthedocs.io/en/latest/user-guide/application-specification/

Automated sync:

https://argo-cd.readthedocs.io/en/latest/user-guide/auto_sync/

Releases:

https://github.com/argoproj/argo-cd/releases

## Weather data

Open-Meteo forecast API:

https://open-meteo.com/en/docs

Open-Meteo geocoding:

https://open-meteo.com/en/docs/geocoding-api

---

# Final perspective

At the beginning, you had:

```text
app/
```

At the end, you personally created and understood:

```text
Git repository
GitHub repository
Dockerfile
private Docker Hub repository
immutable image tags
Terraform provider and cluster resource
KIND cluster
raw Kubernetes Deployment and Service
private imagePullSecrets
Helm chart
Vault
Kubernetes auth in Vault
Vault policies and roles
Vault Agent Injector
Vault Secrets Operator
Vault-managed dockerconfigjson Secret
GitHub Actions test/build/GitOps pipeline
Argo CD installation
Argo CD Application
manual sync
automated GitOps reconciliation
drift/self-healing
```

That is the purpose of the lab.

The weather application is the payload.

The engineering lifecycle is the lesson.
