Section 1 — Project overview
# MLOps CI/CD Demo

A Flask-based ML inference API demonstrating a complete GitHub Actions CI/CD pipeline with staging, production approval, image promotion, traceability, and rollback.

The pipeline follows the principle:

**Build once → Test in staging → Promote the same image → Approve → Deploy to production**

## Project Goal

This project demonstrates a Continuous Delivery workflow for a containerized Flask ML inference API.

The pipeline is designed to ensure that:

* Pull requests are tested before entering `main`.
* Every merge to `main` is automatically deployed to staging.
* The application image is built once for a specific commit.
* The exact same image is promoted to a release tag without rebuilding.
* Production deployments require manual approval.
* Production releases are traceable to a specific Git commit.
* Previous releases can be restored without rebuilding.
* Releases that have not passed staging are rejected.

Section 2 — Architecture:

## Pipeline Architecture

```text
Feature Branch
      |
      v
Pull Request
      |
      v
CI: Tests
      |
      v
Protected main
      |
      v
Build Docker Image
      |
      |  sha-<commit>
      v
GitHub Container Registry
      |
      v
Staging Deployment
      |
      v
/health Smoke Test
      |
      v
staging/smoke-test = success
      |
      v
Release Tag vX.Y.Z
      |
      v
Production Validation
      |
      +--> Commit is on main
      |
      +--> VERSION matches tag
      |
      +--> Staging passed for exact commit
      |
      v
Promote Existing Image
      |
      |  No rebuild
      v
Production Approval
      |
      v
Production Deployment
      |
      v
Production /health Verification
```

### Workflows

The repository contains three workflow responsibilities:

* **CI** — Runs tests for pull requests targeting `main`.
* **Staging** — Runs on pushes to `main`, builds and deploys the image to staging, then performs health and commit verification.
* **Production Release** — Runs for semantic version tags and manual rollback requests. It validates the release, promotes the existing image, waits for production approval, and deploys the selected version.


Section 3 — Docker image strategy:
## Docker Image Strategy

The pipeline uses immutable commit-based image tags during staging.

For a commit such as `e6613ca`, the image is tagged:

```text
ghcr.io/mubashirqamar015-bit/mlops-cd-demo:sha-e6613ca
```

For a release such as `v1.3.0`, the existing SHA image is promoted to:

```text
ghcr.io/mubashirqamar015-bit/mlops-cd-demo:1.3.0
```

The `latest` tag is also updated during promotion.

### Build Once, Promote Many

The staging workflow performs the Docker build:

```text
Git commit
    ↓
docker build
    ↓
sha-<short-commit>
    ↓
GHCR
```

The production workflow does **not** run `docker build`.

Instead, it promotes the existing SHA-tagged image:

```text
sha-<short-commit>
       ↓
   1.3.0
       ↓
    latest
```

This ensures that the artifact tested in staging is the same artifact promoted to production.

The production workflow verifies that the SHA image and release tag have the same image digest before deployment.

### Why SHA Tags Are Used

A commit-based tag provides traceability between source code and the container image.

For example:

```text
Commit:       e6613ca
SHA image:    sha-e6613ca
Application:  1.2.0
Git commit:   e6613ca
```

This makes it possible to identify exactly which source commit produced a running application.

Section 4 — Traceability:
## Application Traceability

The `/health` endpoint exposes deployment metadata:

```json
{
  "application_version": "1.3.0",
  "model_version": "model-8",
  "git_commit": "2824b1a",
  "status": "healthy"
}
```

The values are supplied to the Docker image during the build:

```text
APPLICATION_VERSION
GIT_COMMIT
```

The application version comes from the repository's `VERSION` file.

The Git commit is injected through a Docker build argument using the short commit SHA.

This allows a deployed container to be traced back to both its application release and source commit.


Section 5 — Release & Rollback:
## Release and Rollback Process

### Release v1.2.0

The initial production release used:

```text
Release:       v1.2.0
Git commit:    e6613ca
Model version: model-7
```

The commit passed staging before the release was promoted to production.

### Release v1.3.0

The application was then updated:

```text
Application version: 1.2.0 → 1.3.0
Model version:       model-7 → model-8
```

The change went through:

```text
Pull Request
    ↓
CI tests
    ↓
main
    ↓
Staging deployment
    ↓
Staging smoke test
    ↓
v1.3.0 release
    ↓
Production approval
    ↓
Production deployment
```

The production deployment reported:

```text
Application version: 1.3.0
Model version:       model-8
Git commit:          2824b1a
Status:              healthy
```

### Rollback to v1.2.0

After deploying v1.3.0, the production workflow was manually triggered with:

```text
release_tag: v1.2.0
```

The workflow validated the existing v1.2.0 release and deployed the existing `1.2.0` image.

No Docker image was rebuilt during the rollback.

Production was restored to:

```text
Application version: 1.2.0
Model version:       model-7
Git commit:          e6613ca
Status:              healthy
```

This demonstrates that a previous release can be restored using the existing container image rather than rebuilding the application.

Section 6 — Failed Release Safety Test:
## Failed Release Safety Test

An intentional invalid release was created to verify that production rejects commits that were not merged into `main`.

The test release used:

```text
Release tag:  v1.4.0
Git commit:   d163a86
```

The commit was created on a separate branch and was **not merged into `main`**. The tag was then pushed to GitHub to trigger the production workflow.

The production workflow rejected the release during:

```text
Verify commit is on main
```

The workflow failed with:

```text
Release commit is not on main
```

No production deployment occurred.

This confirms that the production pipeline prevents a tagged commit from being released when that commit is not part of the protected `main` branch.


Section 7 — GitHub Container Registry Access:

## GitHub Container Registry Access

Docker images are stored in GitHub Container Registry (GHCR).

The GitHub Actions workflows use the built-in `GITHUB_TOKEN` for registry authentication.

Staging requires:

```yaml
packages: write
```

This allows the staging workflow to push the SHA-tagged image to GHCR.

Production does not rebuild the image. It promotes the existing SHA-tagged image to the release version and `latest` using Docker Buildx.

The production EC2 server authenticates to GHCR during deployment using the GitHub Actions token passed securely over SSH.

No long-lived GHCR credentials are stored on the production server.
