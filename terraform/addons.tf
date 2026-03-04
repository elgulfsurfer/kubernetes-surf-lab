# EKS managed add-ons — omitting addon_version pins to track the latest
# version compatible with the cluster. Pin them (e.g. addon_version = "v1.x.x-eksbuild.y")
# once you're ready to lock the environment down.

resource "aws_eks_addon" "vpc_cni" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "vpc-cni"

  # IRSA not required; the node IAM role already has AmazonEKS_CNI_Policy
  tags = local.common_tags
}

resource "aws_eks_addon" "kube_proxy" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "kube-proxy"

  tags = local.common_tags
}

resource "aws_eks_addon" "coredns" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "coredns"

  tags = local.common_tags

  # CoreDNS needs running nodes to schedule its pods
  depends_on = [aws_eks_node_group.main]
}

resource "aws_eks_addon" "ebs_csi_driver" {
  cluster_name             = aws_eks_cluster.main.name
  addon_name               = "aws-ebs-csi-driver"
  service_account_role_arn = aws_iam_role.ebs_csi_driver.arn

  tags = local.common_tags

  depends_on = [aws_eks_node_group.main]
}
