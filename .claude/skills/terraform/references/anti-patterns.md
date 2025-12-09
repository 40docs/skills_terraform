# Terraform Anti-Patterns

Common mistakes to avoid when writing Terraform code. Each anti-pattern includes why it's problematic and the correct approach.

## Table of Contents

1. [Variable Anti-Patterns](#variable-anti-patterns)
2. [Resource Anti-Patterns](#resource-anti-patterns)
3. [Organization Anti-Patterns](#organization-anti-patterns)
4. [Security Anti-Patterns](#security-anti-patterns)
5. [Documentation Anti-Patterns](#documentation-anti-patterns)
6. [State Management Anti-Patterns](#state-management-anti-patterns)

---

## Variable Anti-Patterns

### 1. String Booleans

**Anti-Pattern**:
```hcl
variable "deploy_feature" {
  type    = string
  default = "yes"

  validation {
    condition     = contains(["yes", "no"], var.deploy_feature)
    error_message = "Must be 'yes' or 'no'"
  }
}

# Usage
resource "azurerm_resource" "example" {
  count = var.deploy_feature == "yes" ? 1 : 0
}
```

**Problems**:
- Not idiomatic Terraform
- Requires string comparison in conditionals
- Adds unnecessary validation complexity
- Prone to typos ("Yes", "YES", "y", "true")
- Harder to use in boolean expressions

**Correct Approach**:
```hcl
variable "deploy_feature" {
  description = "Deploy optional feature component"
  type        = bool
  default     = true
}

# Usage - cleaner and clearer
resource "azurerm_resource" "example" {
  count = var.deploy_feature ? 1 : 0
}
```

---

### 2. Primitive Variables for Structured Data

**Anti-Pattern**:
```hcl
# 21 separate variables for 7 subnets
variable "subnet1_name" { type = string, default = "web" }
variable "subnet1_prefix" { type = string, default = "10.0.1.0/24" }
variable "subnet1_start_address" { type = string, default = "10.0.1.5" }

variable "subnet2_name" { type = string, default = "app" }
variable "subnet2_prefix" { type = string, default = "10.0.2.0/24" }
variable "subnet2_start_address" { type = string, default = "10.0.2.5" }
# ... repeat 5 more times
```

**Problems**:
- No relationship enforcement between related values
- Easy to mismatch name/prefix/start_address
- Difficult to add/remove subnets
- Clutters variable file
- No structural validation possible

**Correct Approach**:
```hcl
variable "subnets" {
  description = "Subnet configurations"
  type = map(object({
    name              = string
    address_prefix    = string
    start_address     = string
    required_ip_count = number
    purpose           = string
  }))

  default = {
    web = {
      name              = "web-subnet"
      address_prefix    = "10.0.1.0/24"
      start_address     = "10.0.1.5"
      required_ip_count = 5
      purpose           = "Web tier servers"
    }
    app = {
      name              = "app-subnet"
      address_prefix    = "10.0.2.0/24"
      start_address     = "10.0.2.5"
      required_ip_count = 5
      purpose           = "Application tier servers"
    }
  }

  validation {
    condition = alltrue([
      for subnet in var.subnets :
      can(cidrhost(subnet.address_prefix, 10))
    ])
    error_message = "All subnets must have valid CIDR blocks with sufficient IPs"
  }
}
```

---

### 3. Missing Validation

**Anti-Pattern**:
```hcl
variable "ip_address" {
  type    = string
  default = "10.0.1.5"
  # No validation - accepts any string
}

variable "instance_count" {
  type    = number
  default = 2
  # Could be 0, negative, or absurdly large
}

variable "environment" {
  type    = string
  default = "dev"
  # Accepts typos like "prd", "produciton"
}
```

**Problems**:
- Runtime errors instead of plan-time errors
- Difficult to debug invalid configurations
- No guardrails for users
- Unexpected infrastructure state

**Correct Approach**:
```hcl
variable "ip_address" {
  description = "Static IP address for load balancer"
  type        = string

  validation {
    condition     = can(regex("^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}$", var.ip_address))
    error_message = "Must be a valid IPv4 address (e.g., 10.0.1.5)"
  }
}

variable "instance_count" {
  description = "Number of instances to create"
  type        = number
  default     = 2

  validation {
    condition     = var.instance_count >= 1 && var.instance_count <= 10
    error_message = "instance_count must be between 1 and 10"
  }
}

variable "environment" {
  description = "Deployment environment"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod"
  }
}
```

---

### 4. Poor Variable Descriptions

**Anti-Pattern**:
```hcl
variable "prefix" {
  type = string
}

variable "count" {
  type    = number
  default = 2
}

variable "enable" {
  type = bool
}
```

**Problems**:
- No context for what variable controls
- No examples of valid values
- No explanation of impact
- Difficult for team members to use

**Correct Approach**:
```hcl
variable "deployment_prefix" {
  description = <<-EOT
    Naming prefix for all deployed resources (3-10 characters).

    Used to create unique resource names across the deployment.
    Must be lowercase alphanumeric only.

    Examples: "myapp", "contoso", "project1"

    Impact: Changing this will recreate all resources.
  EOT
  type = string

  validation {
    condition     = can(regex("^[a-z0-9]{3,10}$", var.deployment_prefix))
    error_message = "deployment_prefix must be 3-10 lowercase alphanumeric characters"
  }
}

variable "web_server_count" {
  description = <<-EOT
    Number of web server instances to deploy (1-10).

    Instances are distributed across availability zones for HA.
    Minimum 2 recommended for production environments.

    Cost impact: Each instance incurs hourly compute charges.
  EOT
  type    = number
  default = 2

  validation {
    condition     = var.web_server_count >= 1 && var.web_server_count <= 10
    error_message = "web_server_count must be between 1 and 10"
  }
}

variable "enable_auto_scaling" {
  description = <<-EOT
    Enable automatic scaling based on CPU utilization.

    When enabled:
    - Scales up when CPU > 75% for 5 minutes
    - Scales down when CPU < 25% for 10 minutes
    - Min instances: web_server_count
    - Max instances: web_server_count * 3

    Requires: Application Insights enabled
  EOT
  type    = bool
  default = false
}
```

---

## Resource Anti-Patterns

### 5. Magic Numbers

**Anti-Pattern**:
```hcl
# Scattered throughout code
resource "azurerm_lb_probe" "probe" {
  port = 8008  # What is this?
}

resource "azurerm_virtual_machine" "vm" {
  zone = "1"  # Why zone 1?
}

# In cloud-init template
set dst 168.63.129.16 255.255.255.255  # Mystery IP

resource "azurerm_storage_account" "storage" {
  account_replication_type = "GRS"  # Why GRS?
}
```

**Problems**:
- No explanation of values
- Difficult to change consistently
- Easy to introduce errors when updating
- No single source of truth

**Correct Approach**:
```hcl
# locals_constants.tf
locals {
  # Azure Infrastructure Constants
  azure_wire_server_ip = "168.63.129.16"  # Azure metadata service for health probes

  # Health Probe Ports
  fortigate_health_port   = 8008  # FortiGate health check service
  fortiweb_http_port      = 8080  # FortiWeb HTTP health probe
  fortiweb_https_port     = 8443  # FortiWeb HTTPS health probe

  # Availability Zones
  availability_zones = ["1", "2", "3"]

  # Storage Replication
  storage_replication = {
    dev     = "LRS"   # Local redundancy for dev (cost-effective)
    staging = "GRS"   # Geo-redundancy for staging
    prod    = "GZRS"  # Geo-zone redundancy for production (highest availability)
  }
}

# Usage
resource "azurerm_lb_probe" "probe" {
  port = local.fortigate_health_port
}

resource "azurerm_virtual_machine" "vm" {
  zone = local.availability_zones[0]  # Primary zone
}

resource "azurerm_storage_account" "storage" {
  account_replication_type = local.storage_replication[var.environment]
}
```

---

### 6. Using count Instead of for_each

**Anti-Pattern**:
```hcl
variable "subnet_names" {
  type    = list(string)
  default = ["web", "app", "data"]
}

resource "azurerm_subnet" "subnet" {
  count = length(var.subnet_names)

  name                 = var.subnet_names[count.index]
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.0.${count.index + 1}.0/24"]
}
```

**Problems**:
- Removing first subnet renumbers all resources
- Resource addresses become: `azurerm_subnet.subnet[0]`, `[1]`, `[2]`
- Cannot target specific subnet by name in terraform commands
- List reordering causes resource recreation

**Example of Problem**:
```
# Remove "web" subnet from list
subnet_names = ["app", "data"]

# Terraform will:
# - Destroy azurerm_subnet.subnet[2] (was "data")
# - Destroy azurerm_subnet.subnet[1] (was "app")
# - Modify azurerm_subnet.subnet[0] (change from "web" to "app")
# - Create azurerm_subnet.subnet[1] (new "data")
```

**Correct Approach**:
```hcl
locals {
  subnets = {
    "${var.deployment_prefix}-web" = {
      name             = "web-subnet"
      address_prefixes = ["10.0.1.0/24"]
    }
    "${var.deployment_prefix}-app" = {
      name             = "app-subnet"
      address_prefixes = ["10.0.2.0/24"]
    }
    "${var.deployment_prefix}-data" = {
      name             = "data-subnet"
      address_prefixes = ["10.0.3.0/24"]
    }
  }
}

resource "azurerm_subnet" "subnet" {
  for_each = local.subnets

  name                 = each.value.name
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = each.value.address_prefixes
}

# Reference: azurerm_subnet.subnet["myapp-web"]
# Stable addresses, can remove any subnet safely
```

---

### 7. Inline Resource Repetition

**Anti-Pattern**:
```hcl
# Repeated resource definitions
resource "azurerm_virtual_machine" "web1" {
  name                = "web-vm-01"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  vm_size             = "Standard_F4s"
  # ... 50 lines of configuration
}

resource "azurerm_virtual_machine" "web2" {
  name                = "web-vm-02"
  resource_group_name = azurerm_resource_group.rg.name  # Repeated
  location            = azurerm_resource_group.rg.location  # Repeated
  vm_size             = "Standard_F4s"  # Repeated
  # ... 50 lines of nearly identical configuration
}

resource "azurerm_virtual_machine" "app1" {
  name                = "app-vm-01"
  resource_group_name = azurerm_resource_group.rg.name  # Repeated again
  location            = azurerm_resource_group.rg.location  # Repeated again
  vm_size             = "Standard_F8s"
  # ... similar configuration
}
```

**Problems**:
- Violates DRY principle
- Changes must be made in multiple places
- High risk of inconsistency
- Difficult to maintain

**Correct Approach**:
```hcl
# locals_compute.tf - Configuration as data
locals {
  virtual_machines = {
    "${var.deployment_prefix}-web-01" = {
      name    = "web-vm-01"
      vm_size = "Standard_F4s"
      role    = "web"
    }
    "${var.deployment_prefix}-web-02" = {
      name    = "web-vm-02"
      vm_size = "Standard_F4s"
      role    = "web"
    }
    "${var.deployment_prefix}-app-01" = {
      name    = "app-vm-01"
      vm_size = "Standard_F8s"
      role    = "app"
    }
  }
}

# resource_virtual_machine.tf - Single implementation
resource "azurerm_linux_virtual_machine" "vm" {
  for_each = local.virtual_machines

  name                = each.value.name
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  size                = each.value.vm_size
  # ... configuration applies to all VMs
}
```

---

### 8. Excessive depends_on Usage

**Anti-Pattern**:
```hcl
resource "azurerm_subnet" "app" {
  name                 = "app-subnet"
  virtual_network_name = azurerm_virtual_network.vnet.name  # Creates implicit dependency

  # Unnecessary explicit dependency
  depends_on = [
    azurerm_virtual_network.vnet,
    azurerm_resource_group.rg
  ]
}

resource "azurerm_network_interface" "nic" {
  subnet_id = azurerm_subnet.app.id  # Creates implicit dependency

  # Unnecessary - already implicit
  depends_on = [
    azurerm_subnet.app,
    azurerm_virtual_network.vnet,
    azurerm_resource_group.rg
  ]
}
```

**Problems**:
- Reduces Terraform's ability to parallelize
- Implicit dependencies are safer and more maintainable
- Over-specification makes refactoring harder
- Masks real dependency relationships

**Correct Approach**:
```hcl
# Use attribute references for implicit dependencies
resource "azurerm_subnet" "app" {
  name                 = "app-subnet"
  virtual_network_name = azurerm_virtual_network.vnet.name  # Implicit dependency
  # No depends_on needed
}

resource "azurerm_network_interface" "nic" {
  subnet_id = azurerm_subnet.app.id  # Implicit dependency
  # No depends_on needed
}

# Only use depends_on when implicit is not possible
resource "azurerm_linux_virtual_machine" "vm" {
  network_interface_ids = [azurerm_network_interface.nic.id]

  # Only when no attribute to reference
  depends_on = [
    azurerm_marketplace_agreement.agreement  # Can't reference attribute
  ]
}
```

---

## Organization Anti-Patterns

### 9. Mixing Configuration with Implementation

**Anti-Pattern**:
```hcl
# Everything in main.tf
resource "azurerm_subnet" "web" {
  name                 = "web-subnet"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.0.1.0/24"]  # Configuration mixed in
}

resource "azurerm_subnet" "app" {
  name                 = "app-subnet"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.0.2.0/24"]  # Configuration mixed in
}
# Repeat for 20 more subnets
```

**Problems**:
- Can't see all configurations at once
- Configuration scattered throughout resources
- Hard to add conditional resources
- No clear separation of concerns

**Correct Approach**:
```hcl
# locals_network.tf - WHAT to create (configuration)
locals {
  subnets = {
    "${var.deployment_prefix}-web" = {
      name             = "web-subnet"
      address_prefixes = ["10.0.1.0/24"]
    }
    "${var.deployment_prefix}-app" = {
      name             = "app-subnet"
      address_prefixes = ["10.0.2.0/24"]
    }
    # All subnet configurations visible together
  }
}

# resource_subnet.tf - HOW to create it (implementation)
resource "azurerm_subnet" "subnet" {
  for_each = local.subnets

  name                 = each.value.name
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = each.value.address_prefixes
}
```

---

### 10. Outputs Scattered Across Files

**Anti-Pattern**:
```hcl
# In resource_virtual_network.tf
output "vnet_id" {
  value = azurerm_virtual_network.vnet.id
}

# In resource_subnet.tf
output "subnet_ids" {
  value = [for s in azurerm_subnet.subnet : s.id]
}

# In resource_virtual_machine.tf
output "vm_ips" {
  value = [for vm in azurerm_linux_virtual_machine.vm : vm.private_ip_address]
}

# In resource_public_ip.tf
output "public_ips" {
  value = { for pip in azurerm_public_ip.pip : pip.name => pip.ip_address }
}
```

**Problems**:
- Outputs hard to find
- No logical organization
- Can't see all outputs at once
- No categorization

**Correct Approach**:
```hcl
# outputs.tf - ALL outputs in one organized file
###############################################################################
# Network Resources
###############################################################################

output "virtual_network_id" {
  description = "Virtual network resource ID"
  value       = azurerm_virtual_network.vnet[local.vnet_name].id
}

output "subnet_ids" {
  description = "Map of subnet names to resource IDs"
  value = {
    for key, subnet in azurerm_subnet.subnet :
    subnet.name => subnet.id
  }
}

###############################################################################
# Compute Resources
###############################################################################

output "vm_private_ip_addresses" {
  description = "Private IP addresses of virtual machines"
  value = {
    for key, vm in azurerm_linux_virtual_machine.vm :
    key => vm.private_ip_address
  }
}

output "vm_public_ip_addresses" {
  description = "Public IP addresses assigned to VMs"
  value = {
    for key, pip in azurerm_public_ip.vm_pip :
    key => pip.ip_address
  }
}

###############################################################################
# Connection Information
###############################################################################

output "ssh_commands" {
  description = "SSH commands to connect to VMs"
  value = {
    for key, vm in local.virtual_machines :
    key => "ssh ${var.admin_username}@${azurerm_public_ip.pip[key].ip_address}"
    if lookup(vm, "public_ip", false)
  }
}

###############################################################################
# Sensitive Outputs
###############################################################################

output "admin_password" {
  description = "Administrator password"
  value       = var.admin_password
  sensitive   = true
}
```

---

### 11. Inconsistent Naming

**Anti-Pattern**:
```hcl
# Inconsistent abbreviations and formats
variable "fgt_serial_console" { }     # Abbreviation
variable "fortiweb_serial_console" { }  # Full name
variable "dvwa_console" { }             # Different pattern

# Inconsistent resource keys
locals {
  vms = {
    "fgt-a" = { }           # Abbreviation
    "fortiweb-primary" = { }  # Full name
    "WorkloadVM" = { }        # Pascal case
    "app_server_01" = { }     # Snake case
  }
}

# Inconsistent file names
# fortigate_config.tf
# fortiweb-config.tf
# WorkloadConfiguration.tf
```

**Problems**:
- Confusing for team members
- Harder to search and find resources
- Looks unprofessional
- Increases cognitive load

**Correct Approach**:
```hcl
# Establish and follow consistent conventions

# Variables - snake_case, full words
variable "fortigate_serial_console_enabled" { }
variable "fortiweb_serial_console_enabled" { }
variable "workload_serial_console_enabled" { }

# Resource keys - kebab-case with prefix
locals {
  virtual_machines = {
    "${var.deployment_prefix}-fortigate-a"        = { }
    "${var.deployment_prefix}-fortiweb-primary"   = { }
    "${var.deployment_prefix}-workload-server-01" = { }
    "${var.deployment_prefix}-app-server-01"      = { }
  }
}

# File names - snake_case
# locals_fortigate.tf
# locals_fortiweb.tf
# locals_workload.tf
```

---

## Security Anti-Patterns

### 12. Hardcoded Secrets

**Anti-Pattern**:
```hcl
resource "azurerm_virtual_machine" "vm" {
  admin_username = "azureadmin"
  admin_password = "MyPassword123!"  # ❌ NEVER DO THIS
}

resource "aws_db_instance" "database" {
  username = "admin"
  password = "SuperSecret123"  # ❌ Exposed in code
}

# In outputs
output "connection_string" {
  value = "Server=db.example.com;Uid=admin;Pwd=P@ssw0rd"  # ❌ Credentials visible
}
```

**Correct Approach**: Use variables with sensitive flag, Key Vault, or environment variables:

```hcl
# ✅ Use sensitive variable
variable "admin_password" {
  description = "Administrator password (minimum 12 characters)"
  type        = string
  sensitive   = true  # Prevents display in logs

  validation {
    condition     = length(var.admin_password) >= 12
    error_message = "Password must be at least 12 characters"
  }
}

resource "azurerm_virtual_machine" "vm" {
  admin_password = var.admin_password  # From variable, not hardcoded
}

# ✅ Use Key Vault
data "azurerm_key_vault_secret" "admin_password" {
  name         = "vm-admin-password"
  key_vault_id = data.azurerm_key_vault.kv.id
}

resource "azurerm_linux_virtual_machine" "vm" {
  admin_password = data.azurerm_key_vault_secret.admin_password.value
}

# ✅ Mark sensitive outputs
output "connection_string" {
  description = "Database connection string"
  value       = "Server=${azurerm_mysql_server.db.fqdn};..."
  sensitive   = true  # Prevents display in logs
}
```

**Note**: For comprehensive security standards, see `references/security-standards.md`

---

### 13. Overly Permissive Security Rules

**Anti-Pattern**:
```hcl
locals {
  nsg_rules = {
    "allow-everything" = {
      priority                   = 100
      direction                  = "Inbound"
      access                     = "Allow"
      protocol                   = "*"  # All protocols
      source_port_range          = "*"  # All ports
      destination_port_range     = "*"  # All ports
      source_address_prefix      = "*"  # From anywhere
      destination_address_prefix = "*"
    }
  }
}
```

**Correct Approach**: Apply least privilege - deny all by default, allow specific traffic:

```hcl
# ✅ Web tier NSG - Restrictive rules
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
```

**Note**: For comprehensive network security guidance, see `references/security-standards.md`

---

## Documentation Anti-Patterns

### 14. No README or Outdated README

**Anti-Pattern**:
```
project/
├── main.tf
├── variables.tf
└── outputs.tf
# No README.md
```

Or:
```markdown
# Project

This is a Terraform project.

## Usage

Run terraform apply.
```

**Problems**:
- No onboarding for new team members
- No architecture documentation
- No deployment instructions
- Tribal knowledge required

**Correct Approach**:
```markdown
# Azure Web Application Infrastructure

Deploys a three-tier web application architecture on Azure with:
- Load balanced web tier (2-10 instances)
- Application tier with auto-scaling
- PostgreSQL database with HA
- Redis cache cluster
- Monitoring and alerting

## Architecture

[ASCII diagram or link to architecture diagram]

## Prerequisites

- Azure subscription with Contributor role
- Terraform >= 1.5
- Azure CLI authenticated (`az login`)
- SSH key pair for VM access

## Quick Start

1. Copy example configuration:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. Edit terraform.tfvars with your values:
   - deployment_prefix (required)
   - admin_username (required)
   - environment (required)

3. Deploy infrastructure:
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

4. Access application:
   ```bash
   terraform output application_url
   ```

## Configuration

See `terraform.tfvars.example` for all available options.

### Required Variables
- `deployment_prefix` - Unique prefix for resources (3-10 chars)
- `admin_username` - VM administrator username
- `environment` - dev | staging | prod

### Optional Variables
- `web_tier_count` - Number of web servers (default: 2)
- `enable_auto_scaling` - Enable autoscaling (default: true)
- `database_size` - Database SKU (default: GP_Gen5_2)

## Common Operations

### Scale web tier
```bash
# Edit terraform.tfvars
web_tier_count = 5

terraform apply
```

### View connection information
```bash
terraform output connection_info
```

### Destroy infrastructure
```bash
terraform destroy
```

## Troubleshooting

### Common Issues

**Issue**: "Marketplace agreement not accepted"
**Solution**: Run: `az vm image terms accept --publisher X --offer Y --plan Z`

**Issue**: "Insufficient IP addresses in subnet"
**Solution**: Increase subnet CIDR block or reduce instance count

## Architecture Decisions

- **Azure Load Balancer** instead of Application Gateway: Cost optimization for dev
- **PostgreSQL** instead of MySQL: Better JSON support required by application
- **Availability Zones**: Required for 99.99% SLA

## Maintenance

### Updating Dependencies

1. Check for provider updates: `terraform init -upgrade`
2. Review changelog: [provider changelog link]
3. Test in dev environment first
4. Update production

### Backup and Recovery

- Databases backed up daily with 7-day retention
- Backup restore procedure: [link to runbook]

## Support

- Team: platform-team@company.com
- On-call: [PagerDuty link]
- Documentation: [Confluence link]
```

---

### 15. No terraform.tfvars.example

**Anti-Pattern**:
```
project/
├── main.tf
├── variables.tf
├── outputs.tf
└── .gitignore  # Contains terraform.tfvars
# No example file - users don't know what to configure
```

**Correct Approach**:
```hcl
# terraform.tfvars.example
###############################################################################
# Required Variables - You MUST set these
###############################################################################

deployment_prefix = "myapp"       # 3-10 lowercase alphanumeric characters
admin_username    = "azureadmin"  # VM administrator username
environment       = "dev"         # dev | staging | prod

###############################################################################
# Network Configuration (Optional - defaults provided)
###############################################################################

# vnet_address_space = "10.0.0.0/16"  # Default

# Override subnet configuration
# subnets = {
#   web = {
#     name           = "web-subnet"
#     address_prefix = "10.0.1.0/24"
#     # ...
#   }
# }

###############################################################################
# Compute Configuration (Optional)
###############################################################################

# instance_type    = "Standard_F4s"  # Default
# web_server_count = 2                # Default: 2 (range: 1-10)

# Enable auto-scaling (requires Application Insights)
# enable_auto_scaling = true

###############################################################################
# Database Configuration (Optional)
###############################################################################

# database_sku          = "GP_Gen5_2"     # General Purpose, Gen5, 2 vCores
# backup_retention_days = 7               # Default
# enable_geo_redundancy = false           # Enable for production

###############################################################################
# Deployment Control (Optional)
###############################################################################

# deploy_bastion_host = true   # Deploy Azure Bastion for secure access
# deploy_monitoring   = true   # Deploy Application Insights and Log Analytics

###############################################################################
# Tags (Optional)
###############################################################################

# tags = {
#   cost_center = "engineering"
#   owner       = "platform-team"
#   project     = "web-app-platform"
# }
```

---

## State Management Anti-Patterns

### 16. No Remote State Backend

**Anti-Pattern**:
```hcl
# terraform.tf
terraform {
  required_version = ">= 1.5"
  # No backend configuration - state stored locally
}
```

**Problems**:
- State file not shared with team
- No state locking (concurrent runs corrupt state)
- No versioning or backup
- State contains secrets in plaintext locally

**Correct Approach**:
```hcl
# backend.tf
terraform {
  backend "azurerm" {
    resource_group_name  = "terraform-state-rg"
    storage_account_name = "tfstate${var.deployment_prefix}"
    container_name       = "tfstate"
    key                  = "production.tfstate"
    use_azuread_auth     = true  # Use Azure AD instead of access keys
  }
}

# Or AWS
terraform {
  backend "s3" {
    bucket         = "terraform-state-bucket"
    key            = "production/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true  # Encrypt state at rest
    dynamodb_table = "terraform-locks"  # State locking
  }
}
```

---

### 17. Committing terraform.tfvars to Git

**Anti-Pattern**:
```bash
# .gitignore is missing or incomplete
# Result: terraform.tfvars committed with secrets

git add terraform.tfvars
git commit -m "Add configuration"  # ❌ Exposes secrets in Git history
```

**Correct Approach**:
```bash
# .gitignore
# Terraform files
*.tfstate
*.tfstate.*
*.tfvars          # Exclude all .tfvars files
!*.tfvars.example # Except examples
.terraform/
crash.log
override.tf
override.tf.json
*_override.tf
*_override.tf.json

# Sensitive files
*.pem
*.key
*.crt
.env
```

---

## Summary: Quick Checklist

Before considering code complete, verify:

- [ ] No string booleans - use native `bool` type
- [ ] No separate variables for structured data - use `object()`
- [ ] All variables have validation rules
- [ ] No magic numbers - extracted to `locals_constants.tf`
- [ ] Using `for_each`, not `count`
- [ ] No repeated resource blocks - use locals pattern
- [ ] Minimal `depends_on` usage - prefer implicit dependencies
- [ ] Configuration separated from implementation
- [ ] All outputs in dedicated `outputs.tf`
- [ ] Consistent naming conventions throughout
- [ ] No hardcoded secrets
- [ ] No overly permissive security rules
- [ ] Comprehensive README.md exists
- [ ] terraform.tfvars.example provided
- [ ] Remote state backend configured
- [ ] .gitignore excludes sensitive files

**Remember**: These anti-patterns were identified from real production issues. Avoiding them saves significant remediation time.
