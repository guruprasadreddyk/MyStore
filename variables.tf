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
