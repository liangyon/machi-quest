# Secret for JWT secret key
resource "random_password" "jwt_secret" {
  length  = 64
  special = true
}

resource "aws_secretsmanager_secret" "jwt_secret" {
  name        = "${var.environment}/${var.project_name}/app/jwt-secret"
  description = "JWT secret key for token signing"
  tags        = var.tags
}

resource "aws_secretsmanager_secret_version" "jwt_secret" {
  secret_id     = aws_secretsmanager_secret.jwt_secret.id
  secret_string = random_password.jwt_secret.result
}

# Secret for encryption key
resource "random_password" "encryption_key" {
  length  = 32
  special = false # Base64 compatible
}

resource "aws_secretsmanager_secret" "encryption_key" {
  name        = "${var.environment}/${var.project_name}/app/encryption-key"
  description = "Encryption key for sensitive data"
  tags        = var.tags
}

resource "aws_secretsmanager_secret_version" "encryption_key" {
  secret_id     = aws_secretsmanager_secret.encryption_key.id
  secret_string = random_password.encryption_key.result
}

# Store GitHub secrets (you'll need to update these with real values)
resource "aws_secretsmanager_secret" "github_client_id" {
  name        = "${var.environment}/${var.project_name}/github/client-id"
  description = "GitHub OAuth client ID"
  tags        = var.tags
}

resource "aws_secretsmanager_secret_version" "github_client_id" {
  secret_id     = aws_secretsmanager_secret.github_client_id.id
  secret_string = "REPLACEME" # Update after creation
}

resource "aws_secretsmanager_secret" "github_client_secret" {
  name        = "${var.environment}/${var.project_name}/github/client-secret"
  description = "GitHub OAuth client secret"
  tags        = var.tags
}

resource "aws_secretsmanager_secret_version" "github_client_secret" {
  secret_id     = aws_secretsmanager_secret.github_client_secret.id
  secret_string = "REPLACEME" # Update after creation
}
