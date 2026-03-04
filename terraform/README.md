# Terraform — EKS Lab

This folder uses Terraform to provision a production-style EKS cluster on AWS. If you've never used Terraform before, read this first.

---

## What is Terraform?

Terraform is an "infrastructure as code" tool. Instead of clicking around the AWS console, you describe your infrastructure in `.tf` files and Terraform figures out what to create, update, or delete to match that description.

The core workflow is three commands:

```bash
terraform init     # Download the AWS provider plugin (do this once)
terraform plan     # Preview what will be created/changed — nothing is built yet
terraform apply    # Actually build it in AWS
```

To tear everything down:

```bash
terraform destroy
```

---

## File Structure

```
terraform/
├── versions.tf               # Terraform version requirements and provider declarations
├── variables.tf              # All input variables and their defaults
├── terraform.tfvars.example  # Example values — copy to terraform.tfvars to use
├── terraform.tfvars          # Your actual values (git-ignored, never commit this)
├── locals.tf                 # Computed/derived values reused across files
├── vpc.tf                    # Networking — VPC, subnets, NAT gateways, route tables
├── eks.tf                    # EKS cluster and worker node group
├── iam.tf                    # IAM roles and permissions for the cluster and add-ons
├── addons.tf                 # EKS managed add-ons (VPC CNI, CoreDNS, kube-proxy, EBS CSI)
├── outputs.tf                # Values printed after apply (cluster name, endpoint, etc.)
└── .terraform/               # Downloaded provider plugins — auto-generated, git-ignored
```

---

## File-by-File Explanation

### `versions.tf`
Tells Terraform which version of itself and which providers (plugins) to use. This project uses:
- **AWS provider** — talks to the AWS API to create resources
- **TLS provider** — reads the EKS OIDC certificate fingerprint
- **HTTP provider** — fetches the Load Balancer Controller IAM policy from GitHub at plan time

### `variables.tf`
Defines all the knobs you can turn. Each variable has a name, type, description, and default value. You override defaults in `terraform.tfvars`.

Key variables:
| Variable | Default | What it controls |
|---|---|---|
| `region` | `us-west-2` | AWS region |
| `cluster_name` | `k8s-lab` | Name prefix for all resources |
| `cluster_version` | `1.32` | Kubernetes version |
| `node_instance_type` | `t3.medium` | EC2 size for worker nodes |
| `node_count` | `3` | Number of worker nodes |

### `terraform.tfvars` / `terraform.tfvars.example`
`terraform.tfvars` is where you set your actual values, overriding the defaults in `variables.tf`. It is **git-ignored** so secrets never end up in source control. Use `terraform.tfvars.example` as a starting template.

### `locals.tf`
Locals are computed values derived from variables — think of them like constants you calculate once and reuse. This file computes:
- Subnet CIDR ranges for public and private subnets across each availability zone
- The OIDC provider URL/ARN used for IAM role bindings (IRSA)
- A `common_tags` map applied to every resource

### `vpc.tf`
Creates all the AWS networking:
- **VPC** — your private network in AWS
- **Public subnets** — one per availability zone; resources here get a public IP (used for load balancers)
- **Private subnets** — one per AZ; worker nodes live here with no direct public access
- **Internet Gateway** — allows public subnets to reach the internet
- **NAT Gateways** — allows private subnets to make outbound internet requests (e.g., pull container images) without being publicly reachable; one per AZ for high availability
- **Route tables** — rules that direct traffic through the right gateway

### `eks.tf`
Creates the Kubernetes cluster itself:
- **EKS Cluster** — the Kubernetes control plane, managed by AWS
- **Node Group** — the EC2 instances that run your workloads (worker nodes), placed in private subnets

### `iam.tf`
Creates all the AWS IAM roles and permissions. AWS services need permission to act on your behalf:
- **Cluster role** — lets the EKS control plane manage AWS resources
- **Node group role** — lets worker nodes pull images from ECR, use the CNI networking plugin, etc.
- **OIDC provider** — enables IRSA (IAM Roles for Service Accounts), which lets individual Kubernetes pods assume IAM roles without storing credentials
- **EBS CSI driver role** — lets the EBS storage driver create/attach volumes
- **Load Balancer Controller role** — lets the LBC create ALBs/NLBs when you create a Kubernetes Ingress

### `addons.tf`
Installs EKS managed add-ons — software that runs inside the cluster and is kept up to date by AWS:
- **vpc-cni** — assigns real VPC IP addresses to pods
- **kube-proxy** — handles internal cluster networking rules
- **coredns** — DNS resolution inside the cluster
- **aws-ebs-csi-driver** — allows Kubernetes to provision EBS volumes as persistent storage

### `outputs.tf`
After `terraform apply`, Terraform prints these values. Useful for wiring up kubectl and other tools:
- Cluster name and API endpoint
- VPC and subnet IDs
- IAM role ARNs for the add-ons
- A ready-to-run `aws eks update-kubeconfig` command

---

## Getting Started

1. **Install prerequisites**
   ```bash
   brew install terraform awscli
   ```

2. **Configure AWS credentials**
   ```bash
   aws sso login --profile <your-profile>
   ```

3. **Set your variables**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   ```

4. **Initialize and apply**
   ```bash
   terraform init
   terraform plan    # Review what will be created
   terraform apply   # Type "yes" to confirm
   ```

5. **Connect kubectl to the cluster**
   ```bash
   # Terraform prints this command after apply — copy and run it:
   aws eks update-kubeconfig --region us-west-2 --name k8s-lab
   ```

6. **Tear it down when done** (to avoid AWS charges)
   ```bash
   terraform destroy
   ```

---

## What NOT to commit

The `.gitignore` already handles this, but as a reminder — never commit:
- `terraform.tfvars` — may contain account-specific or sensitive values
- `terraform.tfstate` / `terraform.tfstate.backup` — contains the full state of your infrastructure including sensitive data
- `.terraform/` — downloaded provider binaries, large and auto-generated
