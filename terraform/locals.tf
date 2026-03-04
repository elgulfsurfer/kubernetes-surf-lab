locals {
  # Carve public subnets from the low range, private from offset 10
  # e.g. 10.0.0.0/24, 10.0.1.0/24, 10.0.2.0/24 (public)
  #      10.0.10.0/24, 10.0.11.0/24, 10.0.12.0/24 (private)
  public_subnet_cidrs  = [for i, _ in var.availability_zones : cidrsubnet(var.vpc_cidr, 8, i)]
  private_subnet_cidrs = [for i, _ in var.availability_zones : cidrsubnet(var.vpc_cidr, 8, i + 10)]

  # Resolved after the OIDC provider is created; referenced in IRSA trust policies
  oidc_provider_url = replace(aws_iam_openid_connect_provider.eks.url, "https://", "")
  oidc_provider_arn = aws_iam_openid_connect_provider.eks.arn

  common_tags = {
    Environment = "lab"
    ManagedBy   = "terraform"
    Cluster     = var.cluster_name
  }
}
