# Terraform Naming Conventions

Consistent naming improves code readability, maintainability, and team collaboration. Follow these conventions for all Terraform projects.

## Core Principles

1. **Descriptive** - Names should clearly indicate purpose
2. **Consistent** - Use same patterns throughout codebase
3. **Unambiguous** - Avoid abbreviations unless industry-standard
4. **Hierarchical** - Include context (deployment prefix, environment)
5. **Cloud-Compliant** - Follow cloud provider naming restrictions

## Terraform Resource Naming

### Format

```
resource_type "resource_name" {
  # Configuration
}
```

### Rules

**Resource Type**: Use Terraform's canonical resource type names
```hcl
✅ azurerm_virtual_network
✅ aws_vpc
✅ google_compute_network

❌ azurerm_vnet  # Use full name
❌ aws_virtual_private_cloud
```

**Resource Name** (Terraform identifier):
- Use singular form for single instances
- Use descriptive name matching purpose
- Use `snake_case`
- Avoid redundancy with resource type

```hcl
# ✅ Good - Clear and non-redundant
resource "azurerm_virtual_network" "vnet" { }
resource "azurerm_subnet" "web" { }
resource "azurerm_network_security_group" "app_tier" { }

# ❌ Bad - Redundant or unclear
resource "azurerm_virtual_network" "azurerm_virtual_network" { }
resource "azurerm_subnet" "subnet1" { }  # Not descriptive
resource "azurerm_network_security_group" "nsg" { }  # Too abbreviated
```

### for_each Resources

When using `for_each`, the key becomes the resource identifier:

```hcl
# Resource map key format: "${deployment_prefix}-${descriptive-name}"
locals {
  subnets = {
    "${var.deployment_prefix}-web-subnet" = { ... }
    "${var.deployment_prefix}-app-subnet" = { ... }
    "${var.deployment_prefix}-db-subnet"  = { ... }
  }
}

resource "azurerm_subnet" "subnet" {
  for_each = local.subnets
  # Reference: azurerm_subnet.subnet["mycompany-web-subnet"]
}
```

## Azure Resource Naming

### Naming Pattern

```
{deployment_prefix}-{resource_type}-{purpose}-{instance}
```

**Components**:
- `deployment_prefix`: Organization/project identifier (3-10 chars)
- `resource_type`: Abbreviated resource type (2-5 chars)
- `purpose`: Resource role or function
- `instance`: Instance identifier (optional, for multiples)

### Azure Resource Abbreviations

Based on Microsoft Cloud Adoption Framework:

| Resource Type | Abbreviation | Example |
|--------------|--------------|---------|
| Resource Group | rg | `myapp-rg` |
| Virtual Network | vnet | `myapp-vnet` |
| Subnet | snet | `myapp-snet-web` |
| Network Interface | nic | `myapp-nic-web01` |
| Public IP | pip | `myapp-pip-web01` |
| Network Security Group | nsg | `myapp-nsg-web` |
| Load Balancer | lb | `myapp-lb-external` |
| Virtual Machine | vm | `myapp-vm-web01` |
| Storage Account | st | `myappst` (no hyphens) |
| Key Vault | kv | `myapp-kv` |
| Log Analytics Workspace | log | `myapp-log` |
| Application Insights | appi | `myapp-appi` |
| Container Registry | cr | `myappcr` (no hyphens) |
| App Service | app | `myapp-app-web` |
| Function App | func | `myapp-func-api` |
| SQL Database | sqldb | `myapp-sqldb` |
| Cosmos DB | cosmos | `myapp-cosmos` |

### Examples

```hcl
# ✅ Good Azure resource names
locals {
  virtual_networks = {
    "${var.deployment_prefix}-vnet" = {
      name = "${var.deployment_prefix}-vnet"
    }
  }

  subnets = {
    "${var.deployment_prefix}-snet-web" = {
      name = "snet-web"
    }
    "${var.deployment_prefix}-snet-app" = {
      name = "snet-app"
    }
    "${var.deployment_prefix}-snet-data" = {
      name = "snet-data"
    }
  }

  virtual_machines = {
    "${var.deployment_prefix}-vm-web-01" = {
      name = "vm-web-01"
    }
    "${var.deployment_prefix}-vm-web-02" = {
      name = "vm-web-02"
    }
  }
}

# ❌ Bad - Inconsistent or unclear
locals {
  virtual_networks = {
    "vnet1" = {  # Missing prefix, non-descriptive
      name = "my-virtual-network"  # Too verbose
    }
  }

  subnets = {
    "subnet_for_web_servers" = {  # Inconsistent format
      name = "WebSubnet"  # Pascal case instead of kebab-case
    }
  }
}
```

### Special Azure Naming Rules

**Storage Accounts**:
- 3-24 characters
- Lowercase letters and numbers only (no hyphens)
- Must be globally unique

```hcl
# ✅ Correct
name = "${var.deployment_prefix}${var.environment}st"  # "myappdevst"

# ❌ Invalid
name = "${var.deployment_prefix}-${var.environment}-st"  # Has hyphens
```

**Key Vaults**:
- 3-24 characters
- Alphanumerics and hyphens
- Must start with letter
- Must be globally unique

```hcl
# ✅ Correct
name = "${var.deployment_prefix}-${var.environment}-kv"  # "myapp-dev-kv"
```

## AWS Resource Naming

### Naming Pattern

```
{deployment_prefix}-{environment}-{resource_type}-{purpose}-{instance}
```

### AWS Resource Conventions

| Resource Type | Tag Key | Example Name |
|--------------|---------|--------------|
| VPC | Name | `myapp-prod-vpc` |
| Subnet | Name | `myapp-prod-subnet-public-1a` |
| Security Group | Name | `myapp-prod-sg-web` |
| EC2 Instance | Name | `myapp-prod-ec2-web-01` |
| RDS Instance | DBInstanceIdentifier | `myapp-prod-rds-main` |
| S3 Bucket | N/A (bucket name) | `myapp-prod-data` |
| IAM Role | RoleName | `myapp-prod-role-web-server` |
| Lambda Function | FunctionName | `myapp-prod-lambda-processor` |

### Examples

```hcl
# ✅ Good AWS resource names
locals {
  vpcs = {
    "${var.deployment_prefix}-${var.environment}-vpc" = {
      tags = {
        Name = "${var.deployment_prefix}-${var.environment}-vpc"
      }
    }
  }

  subnets = {
    "${var.deployment_prefix}-${var.environment}-subnet-public-1a" = {
      availability_zone = "us-east-1a"
      tags = {
        Name = "${var.deployment_prefix}-${var.environment}-subnet-public-1a"
        Tier = "public"
      }
    }
  }
}
```

## Variable Naming

### Format

```
{scope}_{detail}_{type}
```

### Rules

- Use `snake_case` consistently
- Descriptive full words (avoid abbreviations)
- Type suffix for collections or booleans
- Group related variables with common prefix

### Variable Types and Naming

**Boolean Variables**:
```hcl
# Prefix with: enable_, is_, has_, should_, allow_
variable "enable_monitoring" { type = bool }
variable "is_production" { type = bool }
variable "has_public_ip" { type = bool }
variable "should_backup" { type = bool }
variable "allow_ssh_access" { type = bool }

# ❌ Avoid
variable "monitoring" { type = bool }  # Unclear
variable "public_ip" { type = string, default = "yes" }  # String boolean
```

**String Variables**:
```hcl
variable "deployment_prefix" { type = string }
variable "admin_username" { type = string }
variable "location" { type = string }
variable "instance_type" { type = string }
```

**Number Variables**:
```hcl
variable "instance_count" { type = number }
variable "disk_size_gb" { type = number }
variable "backup_retention_days" { type = number }
variable "max_connections" { type = number }
```

**List Variables**:
```hcl
# Plural noun with _list suffix (if ambiguous)
variable "availability_zones" { type = list(string) }
variable "allowed_ip_ranges" { type = list(string) }
variable "admin_usernames" { type = list(string) }
```

**Map Variables**:
```hcl
# Plural noun or suffix with _map (if ambiguous)
variable "tags" { type = map(string) }
variable "subnet_configs" { type = map(object({...})) }
variable "instance_types" { type = map(string) }
variable "environment_config" { type = map(object({...})) }
```

**Object Variables**:
```hcl
# Singular noun with _config suffix
variable "database_config" {
  type = object({
    engine  = string
    version = string
    size    = string
  })
}

variable "network_config" {
  type = object({
    address_space = string
    dns_servers   = list(string)
  })
}
```

### Variable Organization

Group related variables in `variables.tf`:

```hcl
#####################################################################
# Required Variables
#####################################################################

variable "deployment_prefix" { }
variable "admin_username" { }
variable "admin_password" { }

#####################################################################
# Location and Environment
#####################################################################

variable "location" { }
variable "environment" { }
variable "tags" { }

#####################################################################
# Network Configuration
#####################################################################

variable "vnet_address_space" { }
variable "subnet_configs" { }
variable "enable_ddos_protection" { }

#####################################################################
# Compute Configuration
#####################################################################

variable "instance_type" { }
variable "instance_count" { }
variable "enable_accelerated_networking" { }

#####################################################################
# Deployment Control Flags
#####################################################################

variable "deploy_web_tier" { }
variable "deploy_app_tier" { }
variable "deploy_database" { }
```

## Local Values Naming

### Format

```
{scope}_{detail}
```

### Rules

- Use `snake_case`
- Descriptive names indicating content
- Plural for collections, singular for single values
- Prefix with purpose when needed

### Examples

```hcl
locals {
  # Single values
  resource_group_name = "${var.deployment_prefix}-rg"
  location           = coalesce(var.location, "canadacentral")
  vnet_name          = "${var.deployment_prefix}-vnet"

  # Collections (plural)
  subnets                = { ... }
  virtual_machines       = { ... }
  network_security_groups = { ... }
  load_balancers         = { ... }

  # Computed values
  subnet_start_octets = {
    for key, subnet in var.subnets :
    key => tonumber(split(".", subnet.start_address)[3])
  }

  # Common attributes
  common_resource_attributes = { ... }
  common_tags               = { ... }

  # Constants
  azure_wire_server_ip = "168.63.129.16"
  health_probe_port    = 8008
  availability_zones   = ["1", "2", "3"]
}
```

### Locals File Naming

```
locals_{purpose}.tf
```

**Standard Files**:
- `locals_constants.tf` - Constants and magic numbers
- `locals_common.tf` - Common reusable attributes
- `locals_network.tf` - Network resource configurations
- `locals_compute.tf` - Compute resource configurations
- `locals_security.tf` - Security resource configurations
- `locals_storage.tf` - Storage resource configurations
- `locals_database.tf` - Database resource configurations
- `locals_load_balancer.tf` - Load balancer configurations

## Output Naming

### Format

```
{resource_type}_{detail}
```

### Rules

- Use `snake_case`
- Descriptive and unambiguous
- Include resource type for clarity
- Group related outputs with common prefix
- Mark sensitive outputs explicitly

### Examples

```hcl
# ✅ Good output names
output "resource_group_name" {
  description = "Resource group name"
  value       = azurerm_resource_group.rg.name
}

output "virtual_network_id" {
  description = "Virtual network resource ID"
  value       = azurerm_virtual_network.vnet.id
}

output "subnet_ids" {
  description = "Map of subnet names to resource IDs"
  value       = { for k, v in azurerm_subnet.subnet : k => v.id }
}

output "vm_private_ip_addresses" {
  description = "Private IP addresses of virtual machines"
  value       = { for k, v in azurerm_linux_virtual_machine.vm : k => v.private_ip_address }
}

output "lb_public_ip_address" {
  description = "Load balancer public IP address"
  value       = azurerm_public_ip.lb_pip.ip_address
}

output "database_connection_string" {
  description = "Database connection string with credentials"
  value       = "Server=${azurerm_mysql_server.db.fqdn};..."
  sensitive   = true
}

# ❌ Bad - Unclear or inconsistent
output "rg" { }  # Too abbreviated
output "VirtualNetworkID" { }  # Wrong case
output "subnet_1_id" { }  # Non-descriptive
output "connection_info" { }  # Too vague
```

### Output Organization

Group outputs in `outputs.tf`:

```hcl
###############################################################################
# Resource Groups
###############################################################################

output "resource_group_name" { }
output "resource_group_id" { }

###############################################################################
# Network Resources
###############################################################################

output "virtual_network_id" { }
output "subnet_ids" { }
output "nsg_ids" { }

###############################################################################
# Compute Resources
###############################################################################

output "vm_ids" { }
output "vm_private_ips" { }
output "vm_public_ips" { }

###############################################################################
# Connection Information
###############################################################################

output "ssh_commands" { }
output "web_urls" { }
output "management_url" { }

###############################################################################
# Sensitive Outputs
###############################################################################

output "admin_password" { sensitive = true }
output "database_connection_string" { sensitive = true }
```

## Module Naming

### Directory Structure

```
modules/{module_name}/
```

### Rules

- Use `kebab-case` for module directory names
- Descriptive names indicating purpose
- Organize by logical grouping (not resource type)

### Examples

```
modules/
├── network/              # VNet, subnets, NSGs, routes
├── compute/              # VMs, scale sets, availability sets
├── database/             # Databases and related config
├── load-balancer/        # Load balancers and health probes
├── security/             # Key vaults, security configs
├── monitoring/           # Log Analytics, App Insights
└── web-application/      # Complete web app stack
```

## Tag Naming

### Standard Tags

Every resource should include these tags:

```hcl
locals {
  common_tags = merge(
    var.tags,
    {
      # Required tags
      "managed-by"        = "terraform"
      "deployment-prefix" = var.deployment_prefix
      "environment"       = var.environment

      # Optional but recommended
      "cost-center"       = var.cost_center
      "owner"            = var.owner_email
      "project"          = var.project_name
      "created-date"     = formatdate("YYYY-MM-DD", timestamp())
    }
  )
}
```

### Tag Key Format

- Use `kebab-case` for tag keys
- Descriptive and standardized across organization
- Avoid special characters except hyphens

```hcl
# ✅ Good
tags = {
  "environment"       = "production"
  "cost-center"       = "engineering"
  "data-sensitivity"  = "confidential"
  "backup-required"   = "true"
}

# ❌ Bad
tags = {
  "Env"              = "prod"  # Abbreviated
  "CostCenter"       = "eng"   # Inconsistent case
  "data_sensitivity" = "conf"  # Underscore instead of hyphen
}
```

## File Naming

### Terraform Files

| File | Purpose |
|------|---------|
| `main.tf` | Module entry point (root) or primary resources |
| `variables.tf` | All input variables |
| `outputs.tf` | All outputs |
| `versions.tf` | Terraform and provider version constraints |
| `data.tf` | Data source lookups |
| `locals_*.tf` | Local value definitions by category |
| `resource_*.tf` | Resource implementations by type |
| `terraform.tfvars` | Variable values (gitignored) |
| `terraform.tfvars.example` | Example variable values |
| `.gitignore` | Git exclusions |
| `README.md` | Module documentation |
| `CONTRIBUTING.md` | Contribution guidelines |

### Cloud-Init Templates

```
cloud-init/{purpose}.tpl
```

Examples:
- `cloud-init/web-server.tpl`
- `cloud-init/database-server.tpl`
- `cloud-init/bastion-host.tpl`

## Naming Validation

### Length Constraints

Validate names meet cloud provider requirements:

```hcl
variable "deployment_prefix" {
  description = "Naming prefix for all deployed resources"
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9]{3,10}$", var.deployment_prefix))
    error_message = "deployment_prefix must be 3-10 lowercase alphanumeric characters"
  }
}

variable "storage_account_name" {
  description = "Storage account name (globally unique)"
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9]{3,24}$", var.storage_account_name))
    error_message = "storage_account_name must be 3-24 lowercase alphanumeric characters"
  }
}
```

### Character Restrictions

```hcl
variable "resource_name" {
  description = "Resource name"
  type        = string

  validation {
    condition = can(regex(
      "^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]$",
      var.resource_name
    ))
    error_message = "Must be 1-63 chars, alphanumeric and hyphens, start/end with alphanumeric"
  }
}
```

## Quick Reference

### Terraform Identifiers

| Type | Case | Example |
|------|------|---------|
| Resource Name | snake_case | `virtual_network` |
| Variable | snake_case | `deployment_prefix` |
| Local | snake_case | `resource_group_name` |
| Output | snake_case | `subnet_ids` |
| Module Directory | kebab-case | `load-balancer` |
| File Name | snake_case | `locals_network.tf` |

### Azure Resource Names

| Type | Case | Pattern |
|------|------|---------|
| Most Resources | kebab-case | `{prefix}-{type}-{purpose}` |
| Storage Account | lowercase no hyphens | `{prefix}{purpose}st` |
| VM Computer Name | lowercase | `{prefix}vm{instance}` |

### AWS Resource Names

| Type | Case | Pattern |
|------|------|---------|
| Most Resources | kebab-case | `{prefix}-{env}-{type}-{purpose}` |
| S3 Bucket | lowercase | `{prefix}-{env}-{purpose}` |
| IAM Role | PascalCase or kebab | `{Prefix}{Purpose}Role` |

---

**Remember**: Consistency is more important than the specific convention chosen. Once adopted, apply uniformly across all projects.
