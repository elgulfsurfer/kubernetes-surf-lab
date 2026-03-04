variable "region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-west-2"
}

variable "cluster_name" {
  description = "Name of the EKS cluster, used as a prefix for all resources"
  type        = string
  default     = "k8s-lab"
}

variable "cluster_version" {
  description = "Kubernetes version for the EKS cluster"
  type        = string
  default     = "1.32"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of AZs to spread subnets and NAT gateways across"
  type        = list(string)
  default     = ["us-west-2a", "us-west-2b", "us-west-2c"]
}

variable "node_instance_type" {
  description = "EC2 instance type for EKS worker nodes"
  type        = string
  default     = "t3.medium"
}

variable "node_count" {
  description = "Desired number of worker nodes"
  type        = number
  default     = 3
}

variable "lbc_version" {
  description = "AWS Load Balancer Controller version used to pin the IAM policy download"
  type        = string
  default     = "v2.7.2"
}
