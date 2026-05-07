variable "lambda_role_name" {
  type    = string
  default = "lambda_exec_role_guru"
}

variable "api_name" {
  type    = string
  default = "API_Services_Guru"
}

variable "frontend_bucket_prefix" {
  type    = string
  default = "ecommerce-frontend-guru"
}

variable "sns_topic_name" {
  type    = string
  default = "order-notifications-guru"
}

variable "sqs_queue_name" {
  type    = string
  default = "order-processing-queue-guru"
}

variable "aws_region" {
  type        = string
  default     = "ap-southeast-1"
  description = "AWS region for all resources"
}

variable "aws_profile" {
  type        = string
  default     = "idp-sbx-trn-lab-01"
  description = "AWS CLI profile to use for deployment"
}

variable "notification_email" {
  type        = string
  default     = "guruprasad.reddy@idp.com"
  description = "Email address for SNS order notifications (admin)"
}

variable "auth0_audience" {
  type        = string
  default     = "https://api.mystore.com"
  description = "Auth0 API audience identifier"
}

# ── Auth0 M2M credentials ─────────────────────────────────────────────────────
variable "auth0_domain" {
  type        = string
  default     = "dev-sjgq3v6pvbgxs6mb.us.auth0.com"
  description = "Auth0 tenant domain"
}

variable "auth0_m2m_client_id" {
  type        = string
  default     = ""
  description = "Auth0 M2M application Client ID"
  sensitive   = true
}

variable "auth0_m2m_client_secret" {
  type        = string
  default     = ""
  description = "Auth0 M2M application Client Secret"
  sensitive   = true
}

variable "razorpay_key_id" {
  type        = string
  default     = ""
  description = "Razorpay Key ID (test or live)"
  sensitive   = true
}

variable "razorpay_key_secret" {
  type        = string
  default     = ""
  description = "Razorpay Key Secret (test or live)"
  sensitive   = true
}

variable "smtp_user" {
  type        = string
  default     = ""
  description = "Gmail address used to send transactional emails"
  sensitive   = true
}

variable "smtp_password" {
  type        = string
  default     = ""
  description = "Gmail App Password (not your regular Gmail password)"
  sensitive   = true
}

variable "smtp_from" {
  type        = string
  default     = ""
  description = "Display name + address shown in From field, e.g. 'MyStore <you@gmail.com>'"
}
