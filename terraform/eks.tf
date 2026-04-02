# ── EKS Cluster ───────────────────────────────────────────────────────────────

resource "aws_eks_cluster" "main" {
  name     = var.cluster_name
  role_arn = aws_iam_role.cluster.arn
  version  = var.cluster_version

  vpc_config {
    # Nodes live in private subnets; control plane ENIs span both for flexibility
    subnet_ids = concat(
      aws_subnet.private[*].id,
      aws_subnet.public[*].id,
    )

    # Public endpoint lets you run kubectl from your workstation.
    # Private endpoint means nodes reach the API server without leaving the VPC.
    endpoint_public_access  = true
    endpoint_private_access = true
  }

  tags = local.common_tags

  depends_on = [
    aws_iam_role_policy_attachment.cluster_eks_policy,
  ]
}

# ── Managed Node Group ────────────────────────────────────────────────────────

resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.cluster_name}-nodes"
  node_role_arn   = aws_iam_role.node_group.arn
  version         = var.cluster_version

  # Nodes in private subnets; internet traffic exits through NAT gateways
  subnet_ids = aws_subnet.private[*].id

  instance_types = [var.node_instance_type]

  scaling_config {
    desired_size = var.node_count
    min_size     = 1
    max_size     = var.node_count + 2
  }

  update_config {
    # Replace one node at a time during managed updates
    max_unavailable = 1
  }

  tags = local.common_tags

  depends_on = [
    aws_iam_role_policy_attachment.node_worker_policy,
    aws_iam_role_policy_attachment.node_cni_policy,
    aws_iam_role_policy_attachment.node_ecr_policy,
  ]
}
