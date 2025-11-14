# Terraform Security Standards

Security must be built into infrastructure from the start, not added later. Follow these standards for all Terraform projects.

## Core Security Principles

1. **Defense in Depth** - Multiple layers of security controls
2. **Least Privilege** - Minimum permissions necessary
3. **Zero Trust** - Never trust, always verify
4. **Encryption Everywhere** - At rest and in transit
5. **Secure by Default** - Safe configurations out of the box
6. **Fail Securely** - Errors should not expose vulnerabilities
7. **Audit Everything** - Comprehensive logging and monitoring

---

## Credential Management

### No Hardcoded Secrets

**Rule**: NEVER hardcode credentials, API keys, tokens, or certificates in code.

```hcl
# ❌ NEVER DO THIS
resource "azurerm_virtual_machine" "vm" {
  admin_password = "MyPassword123!"  # Hardcoded secret
}

resource "aws_db_instance" "database" {
  password = "P@ssw0rd"  # Exposed in code
}

# Database connection with embedded credentials
output "connection_string" {
  value = "Server=db.example.com;Uid=admin;Pwd=secret123"  # Credentials visible
}
```

### Correct Approaches

**Use Variables with Sensitive Flag**:
```hcl
# ✅ Variable marked sensitive
variable "admin_password" {
  description = "Administrator password (minimum 12 characters)"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.admin_password) >= 12
    error_message = "Password must be at least 12 characters"
  }
}

resource "azurerm_virtual_machine" "vm" {
  admin_password = var.admin_password  # From variable
}

# Mark sensitive outputs
output "connection_string" {
  description = "Database connection string"
  value       = "Server=${azurerm_mysql_server.db.fqdn};..."
  sensitive   = true  # Prevents display in logs
}
```

**Use Key Vault / Secrets Manager**:
```hcl
# ✅ Azure Key Vault
data "azurerm_key_vault_secret" "admin_password" {
  name         = "vm-admin-password"
  key_vault_id = data.azurerm_key_vault.kv.id
}

resource "azurerm_linux_virtual_machine" "vm" {
  admin_password = data.azurerm_key_vault_secret.admin_password.value
}

# ✅ AWS Secrets Manager
data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = "production/database/password"
}

resource "aws_db_instance" "database" {
  password = jsondecode(data.aws_secretsmanager_secret_version.db_password.secret_string)["password"]
}
```

**Use Environment Variables**:
```bash
# Set in environment, not in code
export TF_VAR_admin_password="SecurePassword123!"
terraform apply
```

### SSH Key Management

```hcl
# ✅ Use SSH keys, not passwords
resource "azurerm_linux_virtual_machine" "vm" {
  disable_password_authentication = true

  admin_ssh_key {
    username   = var.admin_username
    public_key = file("~/.ssh/id_rsa.pub")  # Or from variable
  }
}

# ✅ Generate keys with Terraform
resource "tls_private_key" "ssh" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "azurerm_linux_virtual_machine" "vm" {
  admin_ssh_key {
    username   = var.admin_username
    public_key = tls_private_key.ssh.public_key_openssh
  }
}

# Store private key securely
output "private_key" {
  description = "SSH private key for VM access"
  value       = tls_private_key.ssh.private_key_pem
  sensitive   = true
}
```

---

## Encryption Standards

### At-Rest Encryption

**Rule**: All data storage must be encrypted at rest.

**Azure Storage**:
```hcl
# ✅ Managed Disk Encryption
resource "azurerm_managed_disk" "disk" {
  name                = "${var.deployment_prefix}-disk"
  resource_group_name = var.resource_group_name
  location            = var.location
  storage_account_type = "Premium_LRS"
  create_option       = "Empty"
  disk_size_gb        = 128

  encryption_settings {
    enabled = true  # Always enable

    disk_encryption_key {
      secret_url      = azurerm_key_vault_secret.disk_encryption_key.id
      source_vault_id = azurerm_key_vault.kv.id
    }
  }
}

# ✅ Storage Account Encryption
resource "azurerm_storage_account" "storage" {
  name                     = "${var.deployment_prefix}st"
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "GRS"

  # Encryption enabled by default, specify customer-managed keys
  customer_managed_key {
    key_vault_key_id          = azurerm_key_vault_key.storage_key.id
    user_assigned_identity_id = azurerm_user_assigned_identity.storage.id
  }
}

# ✅ SQL Database Transparent Data Encryption
resource "azurerm_mssql_database" "db" {
  name      = "${var.deployment_prefix}-sqldb"
  server_id = azurerm_mssql_server.server.id

  # TDE enabled by default, can specify customer-managed key
  transparent_data_encryption_key_vault_key_id = azurerm_key_vault_key.tde_key.id
}
```

**AWS Storage**:
```hcl
# ✅ EBS Volume Encryption
resource "aws_ebs_volume" "volume" {
  availability_zone = var.availability_zone
  size              = 100

  encrypted  = true  # Always enable
  kms_key_id = aws_kms_key.ebs.arn
}

# ✅ S3 Bucket Encryption
resource "aws_s3_bucket" "bucket" {
  bucket = "${var.deployment_prefix}-data"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "encryption" {
  bucket = aws_s3_bucket.bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3.arn
    }
    bucket_key_enabled = true
  }
}

# ✅ RDS Encryption
resource "aws_db_instance" "database" {
  identifier = "${var.deployment_prefix}-rds"

  storage_encrypted = true  # Always enable
  kms_key_id       = aws_kms_key.rds.arn
}
```

### In-Transit Encryption

**Rule**: All network traffic must be encrypted with TLS 1.2+.

```hcl
# ✅ HTTPS Only for Storage
resource "azurerm_storage_account" "storage" {
  name = "${var.deployment_prefix}st"
  # ...

  enable_https_traffic_only = true  # Enforce HTTPS
  min_tls_version          = "TLS1_2"  # Minimum TLS 1.2
}

# ✅ Application Gateway with SSL
resource "azurerm_application_gateway" "gateway" {
  name = "${var.deployment_prefix}-appgw"
  # ...

  ssl_policy {
    policy_type = "Predefined"
    policy_name = "AppGwSslPolicy20220101"  # Strong cipher suites
  }

  ssl_certificate {
    name     = "ssl-cert"
    data     = filebase64("${path.module}/certs/ssl-cert.pfx")
    password = var.ssl_certificate_password
  }
}

# ✅ AWS ALB with HTTPS
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.app.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"  # TLS 1.2+
  certificate_arn   = aws_acm_certificate.cert.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}

# ✅ Redirect HTTP to HTTPS
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.app.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}
```

---

## Network Security

### Network Segmentation

**Rule**: Segment networks by security level and function.

```hcl
# ✅ Three-tier architecture
locals {
  subnets = {
    # Public tier - Internet-facing resources
    "${var.deployment_prefix}-snet-public" = {
      name             = "snet-public"
      address_prefixes = ["10.0.1.0/24"]
      security_tier    = "public"
    }

    # Application tier - Internal applications
    "${var.deployment_prefix}-snet-app" = {
      name             = "snet-app"
      address_prefixes = ["10.0.2.0/24"]
      security_tier    = "internal"
    }

    # Data tier - Databases and sensitive data
    "${var.deployment_prefix}-snet-data" = {
      name             = "snet-data"
      address_prefixes = ["10.0.3.0/24"]
      security_tier    = "restricted"
    }

    # Management tier - Admin access only
    "${var.deployment_prefix}-snet-mgmt" = {
      name             = "snet-mgmt"
      address_prefixes = ["10.0.4.0/24"]
      security_tier    = "management"
    }
  }
}
```

### Network Security Groups / Security Groups

**Rule**: Apply least privilege - deny all by default, allow specific traffic.

```hcl
# ✅ Web tier NSG - Restrictive inbound rules
locals {
  nsg_rules_web = {
    # Allow HTTPS from internet
    "allow-https-inbound" = {
      priority                   = 100
      direction                  = "Inbound"
      access                     = "Allow"
      protocol                   = "Tcp"
      source_port_range          = "*"
      destination_port_range     = "443"
      source_address_prefix      = "Internet"
      destination_address_prefix = "*"
    }

    # Allow HTTP from internet (for redirect to HTTPS)
    "allow-http-inbound" = {
      priority                   = 110
      direction                  = "Inbound"
      access                     = "Allow"
      protocol                   = "Tcp"
      source_port_range          = "*"
      destination_port_range     = "80"
      source_address_prefix      = "Internet"
      destination_address_prefix = "*"
    }

    # Deny all other inbound
    "deny-all-inbound" = {
      priority                   = 4096
      direction                  = "Inbound"
      access                     = "Deny"
      protocol                   = "*"
      source_port_range          = "*"
      destination_port_range     = "*"
      source_address_prefix      = "*"
      destination_address_prefix = "*"
    }
  }

  # Data tier NSG - Only allow from app tier
  nsg_rules_data = {
    "allow-app-tier-sql" = {
      priority                   = 100
      direction                  = "Inbound"
      access                     = "Allow"
      protocol                   = "Tcp"
      source_port_range          = "*"
      destination_port_range     = "1433"
      source_address_prefix      = "10.0.2.0/24"  # App tier subnet
      destination_address_prefix = "*"
    }

    # Deny all other inbound
    "deny-all-inbound" = {
      priority                   = 4096
      direction                  = "Inbound"
      access                     = "Deny"
      protocol                   = "*"
      source_port_range          = "*"
      destination_port_range     = "*"
      source_address_prefix      = "*"
      destination_address_prefix = "*"
    }
  }
}

# ❌ Bad - Overly permissive
locals {
  nsg_rules_bad = {
    "allow-all" = {
      priority                   = 100
      direction                  = "Inbound"
      access                     = "Allow"
      protocol                   = "*"  # All protocols
      source_port_range          = "*"
      destination_port_range     = "*"  # All ports
      source_address_prefix      = "*"  # From anywhere
      destination_address_prefix = "*"
    }
  }
}
```

### Public IP Restrictions

**Rule**: Minimize public IP exposure, use NAT gateways and bastion hosts.

```hcl
# ✅ No public IPs on application VMs
resource "azurerm_linux_virtual_machine" "app" {
  for_each = local.app_vms

  name = each.value.name
  # ... configuration

  # No public IP assigned
}

# ✅ Bastion host for management access
resource "azurerm_bastion_host" "bastion" {
  name                = "${var.deployment_prefix}-bastion"
  location            = var.location
  resource_group_name = var.resource_group_name

  ip_configuration {
    name                 = "bastion-ipconfig"
    subnet_id            = azurerm_subnet.subnet["AzureBastionSubnet"].id
    public_ip_address_id = azurerm_public_ip.bastion_pip.id
  }
}

# ✅ NAT Gateway for outbound internet access
resource "azurerm_nat_gateway" "nat" {
  name                = "${var.deployment_prefix}-nat"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku_name            = "Standard"
}

resource "azurerm_subnet_nat_gateway_association" "nat_assoc" {
  subnet_id      = azurerm_subnet.subnet["snet-app"].id
  nat_gateway_id = azurerm_nat_gateway.nat.id
}
```

### Service Endpoints and Private Link

```hcl
# ✅ Use service endpoints for Azure PaaS
resource "azurerm_subnet" "app" {
  name = "snet-app"
  # ...

  service_endpoints = [
    "Microsoft.Sql",
    "Microsoft.Storage",
    "Microsoft.KeyVault"
  ]
}

# ✅ Restrict storage to specific subnets
resource "azurerm_storage_account_network_rules" "rules" {
  storage_account_id = azurerm_storage_account.storage.id

  default_action             = "Deny"  # Deny by default
  virtual_network_subnet_ids = [
    azurerm_subnet.subnet["snet-app"].id
  ]
  bypass = ["AzureServices"]
}

# ✅ Private endpoint for database
resource "azurerm_private_endpoint" "db" {
  name                = "${var.deployment_prefix}-db-pe"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = azurerm_subnet.subnet["snet-data"].id

  private_service_connection {
    name                           = "db-privateserviceconnection"
    private_connection_resource_id = azurerm_mysql_server.db.id
    is_manual_connection          = false
    subresource_names             = ["mysqlServer"]
  }
}
```

---

## Identity and Access Management

### Least Privilege

**Rule**: Grant minimum permissions required for function.

```hcl
# ✅ Azure - Role-based access control
resource "azurerm_role_assignment" "vm_contributor" {
  scope                = azurerm_resource_group.rg.id
  role_definition_name = "Virtual Machine Contributor"  # Specific role
  principal_id         = azurerm_user_assigned_identity.vm_identity.principal_id
}

# ✅ AWS - Specific IAM policy
resource "aws_iam_role_policy" "app_policy" {
  name = "${var.deployment_prefix}-app-policy"
  role = aws_iam_role.app_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = [
          "${aws_s3_bucket.app_data.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.app_config.arn
        ]
      }
    ]
  })
}

# ❌ Bad - Overly broad permissions
resource "aws_iam_role_policy" "bad_policy" {
  policy = jsonencode({
    Statement = [{
      Effect   = "Allow"
      Action   = "*"  # All actions
      Resource = "*"  # All resources
    }]
  })
}
```

### Managed Identities

**Rule**: Use managed identities instead of service principals with secrets.

```hcl
# ✅ Azure - User-assigned managed identity
resource "azurerm_user_assigned_identity" "vm_identity" {
  name                = "${var.deployment_prefix}-vm-identity"
  location            = var.location
  resource_group_name = var.resource_group_name
}

resource "azurerm_linux_virtual_machine" "vm" {
  name = "${var.deployment_prefix}-vm"
  # ...

  identity {
    type = "UserAssigned"
    identity_ids = [
      azurerm_user_assigned_identity.vm_identity.id
    ]
  }
}

# Grant Key Vault access to identity
resource "azurerm_key_vault_access_policy" "vm_kv_access" {
  key_vault_id = azurerm_key_vault.kv.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_user_assigned_identity.vm_identity.principal_id

  secret_permissions = [
    "Get",
    "List"
  ]
}

# ✅ AWS - IAM role for EC2 instance
resource "aws_iam_role" "ec2_role" {
  name = "${var.deployment_prefix}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.deployment_prefix}-ec2-profile"
  role = aws_iam_role.ec2_role.name
}

resource "aws_instance" "app" {
  ami           = var.ami_id
  instance_type = var.instance_type

  iam_instance_profile = aws_iam_instance_profile.ec2_profile.name
}
```

---

## Logging and Monitoring

### Comprehensive Logging

**Rule**: Enable logging for all security-relevant resources.

```hcl
# ✅ Azure - Log Analytics workspace
resource "azurerm_log_analytics_workspace" "logs" {
  name                = "${var.deployment_prefix}-log"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "PerGB2018"
  retention_in_days   = 90  # Compliance requirement
}

# Enable diagnostic settings for NSG
resource "azurerm_monitor_diagnostic_setting" "nsg_logs" {
  for_each = local.network_security_groups

  name                       = "${each.key}-diagnostics"
  target_resource_id         = azurerm_network_security_group.nsg[each.key].id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.logs.id

  enabled_log {
    category = "NetworkSecurityGroupEvent"
  }

  enabled_log {
    category = "NetworkSecurityGroupRuleCounter"
  }
}

# Enable VM boot diagnostics
resource "azurerm_linux_virtual_machine" "vm" {
  name = "${var.deployment_prefix}-vm"
  # ...

  boot_diagnostics {
    storage_account_uri = azurerm_storage_account.diagnostics.primary_blob_endpoint
  }
}

# ✅ AWS - CloudWatch logging
resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "/aws/application/${var.deployment_prefix}"
  retention_in_days = 90
  kms_key_id       = aws_kms_key.logs.arn  # Encrypt logs
}

# VPC Flow Logs
resource "aws_flow_log" "vpc_flow_log" {
  vpc_id          = aws_vpc.main.id
  traffic_type    = "ALL"
  iam_role_arn    = aws_iam_role.flow_log_role.arn
  log_destination = aws_cloudwatch_log_group.flow_logs.arn
}
```

### Security Monitoring

```hcl
# ✅ Azure Security Center
resource "azurerm_security_center_subscription_pricing" "security_center" {
  tier          = "Standard"  # Enable advanced threat protection
  resource_type = "VirtualMachines"
}

# ✅ AWS GuardDuty
resource "aws_guardduty_detector" "security" {
  enable = true

  datasources {
    s3_logs {
      enable = true
    }
    kubernetes {
      audit_logs {
        enable = true
      }
    }
  }
}
```

---

## Compliance and Governance

### Azure Policy

```hcl
# ✅ Enforce encryption
resource "azurerm_policy_assignment" "require_encryption" {
  name                 = "require-storage-encryption"
  scope                = azurerm_resource_group.rg.id
  policy_definition_id = "/providers/Microsoft.Authorization/policyDefinitions/404c3081-a854-4457-ae30-26a93ef643f9"

  parameters = jsonencode({
    effect = {
      value = "Deny"
    }
  })
}
```

### AWS Config Rules

```hcl
# ✅ Ensure encrypted volumes
resource "aws_config_config_rule" "encrypted_volumes" {
  name = "encrypted-volumes"

  source {
    owner             = "AWS"
    source_identifier = "ENCRYPTED_VOLUMES"
  }

  depends_on = [aws_config_configuration_recorder.main]
}
```

### Resource Tagging for Governance

```hcl
locals {
  required_tags = {
    "environment"      = var.environment
    "data-classification" = var.data_classification  # Public, Internal, Confidential, Restricted
    "compliance-scope" = var.compliance_scope  # PCI, HIPAA, SOC2, etc.
    "cost-center"      = var.cost_center
    "owner"           = var.owner_email
    "backup-required" = var.backup_required
  }
}
```

---

## Security Checklist

Before deploying infrastructure, verify:

### Credentials
- [ ] No hardcoded secrets in code
- [ ] Sensitive variables marked with `sensitive = true`
- [ ] Sensitive outputs marked appropriately
- [ ] Secrets stored in Key Vault / Secrets Manager
- [ ] SSH keys used instead of passwords
- [ ] Strong password policies enforced (12+ chars, complexity)

### Encryption
- [ ] All storage encrypted at rest
- [ ] Customer-managed keys where required
- [ ] HTTPS/TLS enforced for all traffic
- [ ] Minimum TLS 1.2 configured
- [ ] SSL certificates properly managed

### Network Security
- [ ] Network segmentation implemented
- [ ] NSG/Security Group rules follow least privilege
- [ ] Public IPs minimized
- [ ] Bastion host / jump box for admin access
- [ ] Service endpoints / Private Link configured
- [ ] DDoS protection enabled for public endpoints

### Identity & Access
- [ ] Least privilege IAM/RBAC policies
- [ ] Managed identities used instead of service principals
- [ ] MFA required for privileged accounts
- [ ] Role assignments scoped appropriately
- [ ] Service accounts have minimal permissions

### Logging & Monitoring
- [ ] Diagnostic logging enabled for all resources
- [ ] Centralized log collection configured
- [ ] Log retention meets compliance requirements
- [ ] Security monitoring enabled (Security Center, GuardDuty)
- [ ] Alerts configured for security events

### Compliance
- [ ] Required tags applied to all resources
- [ ] Azure Policy / AWS Config rules enforced
- [ ] Compliance-specific controls implemented
- [ ] Data residency requirements met
- [ ] Audit trail enabled

---

**Remember**: Security is not optional. Every resource must meet these minimum standards before deployment.
