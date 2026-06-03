# ─── API Gateway Access Logs ──────────────────────────────────────────────────

resource "aws_cloudwatch_log_group" "api_access_logs" {
  name              = "/aws/apigateway/${var.api_name}/access-logs"
  retention_in_days = 30
}
