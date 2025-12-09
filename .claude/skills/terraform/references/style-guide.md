# Terraform Style Guide

## Core Philosophy

**"Evidence > Assumptions | Code > Documentation | Efficiency > Verbosity"**

Terraform code should be:
- **Predictable** - Same inputs always produce same outputs
- **Maintainable** - Easy to understand and modify
- **Secure** - Safe by default, explicit when unsafe
- **Testable** - Can be validated before deployment
- **Documented** - Self-explanatory with clear explanations for complex logic

## Foundational Principles

### 1. Configuration as Data Pattern

**Principle**: Separate "what to create" (configuration) from "how to create it" (implementation).

**Implementation**:
- Define configurations in `locals_*.tf` files as structured maps
- Implement resources in `resource_*.tf` files using `for_each`
- Use descriptive keys: `"${var.deployment_prefix}-resource-name"`

**Benefits**:
- Single resource block handles multiple instances
- Configuration changes don't require code changes
- Easy to add/remove resources
- Clear separation of concerns

**Example**:
```hcl
# locals_network.tf - WHAT to create
locals {
  subnets = {
    "${var.deployment_prefix}-web" = {
      name             = "web-subnet"
      address_prefixes = ["10.0.1.0/24"]
      purpose          = "Web tier"
    }
    "${var.deployment_prefix}-app" = {
      name             = "app-subnet"
      address_prefixes = ["10.0.2.0/24"]
      purpose          = "Application tier"
    }
  }
}

# resource_subnet.tf - HOW to create it
resource "azurerm_subnet" "subnet" {
  for_each = local.subnets

  name                 = each.value.name
  resource_group_name  = each.value.resource_group_name
  virtual_network_name = each.value.virtual_network_name
  address_prefixes     = each.value.address_prefixes
}
```

### 2. DRY (Don't Repeat Yourself)

**Principle**: Every piece of knowledge should have a single, unambiguous representation.

**Apply DRY to**:
- Common resource attributes (resource_group_name, location)
- Repeated configurations (multiple VMs, subnets, NICs)
- Magic numbers and constants
- Validation logic
- Documentation

**Anti-pattern**:
```hcl
# ❌ Repetitive resource definitions
resource "azurerm_subnet" "web" {
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  # ...
}

resource "azurerm_subnet" "app" {
  resource_group_name = azurerm_resource_group.rg.name  # Repeated
  location            = azurerm_resource_group.rg.location  # Repeated
  # ...
}
```

**Best practice**:
```hcl
# ✅ Extract common attributes
locals {
  common_attributes = {
    resource_group_name = azurerm_resource_group.rg.name
    location            = azurerm_resource_group.rg.location
  }
}

# Use merge to apply common attributes
locals {
  subnets = {
    for name, config in var.subnet_configs :
    name => merge(local.common_attributes, config)
  }
}
```

### 3. Type Safety First

**Principle**: Use Terraform's type system to catch errors early.

**Rules**:
- ✅ Use `bool` for true/false conditions
- ✅ Use `number` for numeric values
- ✅ Use `object()` for structured data
- ✅ Use `map()` for collections with named keys
- ✅ Use `list()` for ordered collections
- ❌ Never use strings for boolean logic ("yes"/"no")
- ❌ Never use separate variables for related data

**Anti-pattern**:
```hcl
# ❌ String booleans
variable "deploy_feature" {
  type    = string
  default = "yes"
  validation {
    condition     = contains(["yes", "no"], var.deploy_feature)
    error_message = "Must be yes or no"
  }
}

# ❌ Primitive variables for structured data
variable "subnet1_name" { type = string }
variable "subnet1_prefix" { type = string }
variable "subnet1_gateway" { type = string }
```

**Best practice**:
```hcl
# ✅ Native boolean
variable "deploy_feature" {
  description = "Deploy optional feature component"
  type        = bool
  default     = true
}

# ✅ Structured data
variable "subnets" {
  description = "Subnet configurations"
  type = map(object({
    name             = string
    address_prefixes = list(string)
    gateway_address  = string
    purpose          = string
  }))

  validation {
    condition = alltrue([
      for subnet in var.subnets :
      can(cidrhost(subnet.address_prefixes[0], 1))
    ])
    error_message = "All address_prefixes must be valid CIDR blocks"
  }
}
```

### 4. No Magic Numbers

**Principle**: All constants should be named and documented.

**Extract to `locals_constants.tf`**:
- Cloud provider service IPs (Azure Wire Server: 168.63.129.16)
- Standard ports (HTTP: 80, HTTPS: 443, SSH: 22)
- Health check ports (custom probe ports)
- Availability zones (1, 2, 3)
- Storage SKUs (Standard_LRS, Premium_LRS)
- Marketplace identifiers
- Timeout values
- Retry counts

**Anti-pattern**:
```hcl
# ❌ Magic numbers scattered throughout code
resource "azurerm_lb_probe" "probe" {
  port = 8008  # What is this port?
}

resource "azurerm_virtual_machine" "vm" {
  zone = "1"  # Why zone 1?
}

set dst 168.63.129.16 255.255.255.255  # What is this IP?
```

**Best practice**:
```hcl
# ✅ locals_constants.tf
locals {
  # Azure Infrastructure Constants
  azure_wire_server_ip = "168.63.129.16"  # Azure metadata/health probe service

  # Health Probe Ports
  fortigate_health_port = 8008  # FortiGate health check service

  # Availability Zones
  availability_zones = ["1", "2", "3"]

  # Storage SKUs
  storage_sku = {
    standard = "Standard_LRS"
    premium  = "Premium_LRS"
  }
}

# Usage
resource "azurerm_lb_probe" "probe" {
  port = local.fortigate_health_port
}

resource "azurerm_virtual_machine" "vm" {
  zone = local.availability_zones[0]
}
```

### 5. Explicit Over Implicit

**Principle**: Make intentions clear and behavior predictable.

**Guidelines**:
- Explicit dependencies over implicit when order matters
- Explicit types in variable definitions
- Explicit validation rules for inputs
- Explicit provider version constraints
- Explicit attribute references over string interpolation

**Example**:
```hcl
# ✅ Explicit type
variable "instance_count" {
  description = "Number of instances to create (1-10)"
  type        = number
  default     = 2

  validation {
    condition     = var.instance_count >= 1 && var.instance_count <= 10
    error_message = "instance_count must be between 1 and 10"
  }
}

# ✅ Explicit provider versions
terraform {
  required_version = ">= 1.5, < 2.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"  # Allow minor updates, not major
    }
  }
}

# ✅ Explicit dependency
resource "azurerm_virtual_machine" "vm" {
  # Explicit reference creates implicit dependency
  subnet_id = azurerm_subnet.subnet[each.key].id

  # Only use depends_on when implicit dependencies insufficient
  depends_on = [
    azurerm_marketplace_agreement.agreement
  ]
}
```

## File Organization

### Standard Structure

```
project-root/
├── README.md                      # Architecture overview, usage guide
├── versions.tf                    # Terraform and provider versions
├── variables.tf                   # All input variables
├── outputs.tf                     # All outputs (organized by category)
├── data.tf                        # Data source lookups
├── locals_constants.tf            # Constants and magic numbers
├── locals_common.tf               # Common reusable attributes
├── locals_<component>.tf          # Component-specific configurations
├── resource_<type>.tf             # Resource implementations
├── terraform.tfvars.example       # Documented example configuration
├── .gitignore                     # Exclude sensitive files
└── CONTRIBUTING.md                # Maintenance and contribution guide
```

### File Naming Conventions

- `locals_*.tf` - Configuration as data (prefix indicates content)
- `resource_*.tf` - Resource implementations (prefix indicates resource type)
- `data.tf` - All data sources (single file unless >100 lines)
- `outputs.tf` - All outputs (single file, organized with comments)
- `variables.tf` - All variables (single file, organized by category)

### File Organization Rules

1. **One concern per locals file**:
   - `locals_network.tf` - Network resources only
   - `locals_compute.tf` - Compute resources only
   - `locals_security.tf` - Security resources only

2. **Generic resource files**:
   - Single `resource_virtual_machine.tf` for ALL VMs
   - Use `for_each = local.virtual_machines`
   - Never create `resource_web_vm.tf`, `resource_app_vm.tf`

3. **Aggregation pattern**:
   ```hcl
   # locals_compute.tf - Aggregates component locals
   locals {
     virtual_machines = merge(
       local.web_vms,
       local.app_vms,
       local.db_vms
     )
   }
   ```

## Variable Design Standards

### Variable Declaration Template

```hcl
variable "name" {
  description = "Clear description with context and purpose. Include valid value examples."
  type        = <appropriate_type>
  default     = <sensible_default_or_omit>
  sensitive   = true|false  # Mark sensitive data
  nullable    = false       # Explicit about null handling

  validation {
    condition     = <validation_expression>
    error_message = <<-EOT
      Clear error with:
      - What's wrong
      - Valid examples
      - Why it matters
    EOT
  }
}
```

### Variable Naming

**Format**: `<purpose>_<detail>_<type>`

**Examples**:
- `deployment_prefix` - Prefix for resource names
- `admin_username` - Administrator username
- `subnet_address_prefix` - CIDR block for subnet
- `enable_public_access` - Boolean flag
- `instance_type_map` - Map of instance types by environment

**Rules**:
- Use full words, not abbreviations (unless industry standard)
- Use snake_case consistently
- Boolean variables start with `enable_`, `is_`, `has_`, `should_`
- Collections use plural nouns
- Single items use singular nouns

### Variable Types

**Use structured types for related data**:

```hcl
# ✅ Good - Single structured variable
variable "database_config" {
  description = "Database configuration"
  type = object({
    engine         = string
    version        = string
    instance_class = string
    storage_gb     = number
    multi_az       = bool
    backup_retention_days = number
  })

  validation {
    condition     = var.database_config.storage_gb >= 20
    error_message = "Database storage must be at least 20GB"
  }
}

# ❌ Bad - Separate primitive variables
variable "database_engine" { type = string }
variable "database_version" { type = string }
variable "database_instance_class" { type = string }
variable "database_storage_gb" { type = number }
variable "database_multi_az" { type = string }  # String boolean!
```

### Validation Rules

**Every variable with constraints must have validation**:

```hcl
variable "location" {
  description = "Azure region for deployment"
  type        = string

  validation {
    condition = contains([
      "canadacentral",
      "canadaeast",
      "eastus",
      "westus2",
      "westeurope"
    ], var.location)
    error_message = "Location must be one of: canadacentral, canadaeast, eastus, westus2, westeurope"
  }
}

variable "ip_address" {
  description = "Static IP address"
  type        = string

  validation {
    condition     = can(regex("^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}$", var.ip_address))
    error_message = "Must be a valid IPv4 address (e.g., 10.0.1.5)"
  }
}
```

## Resource Standards

### Use for_each, Not count

**Principle**: `for_each` provides stable resource addresses.

```hcl
# ✅ Preferred - Stable addresses
resource "azurerm_subnet" "subnet" {
  for_each = local.subnets

  name                 = each.value.name
  resource_group_name  = each.value.resource_group_name
  virtual_network_name = each.value.virtual_network_name
  address_prefixes     = each.value.address_prefixes
}

# ❌ Avoid - Unstable addresses
resource "azurerm_subnet" "subnet" {
  count = length(var.subnet_names)

  name = var.subnet_names[count.index]
  # If you remove first subnet, all addresses shift
}
```

### Implicit Dependencies

**Prefer attribute references over explicit depends_on**:

```hcl
# ✅ Good - Implicit dependency
resource "azurerm_network_interface" "nic" {
  subnet_id = azurerm_subnet.subnet["web"].id  # Creates implicit dependency
}

# ❌ Only when necessary
resource "azurerm_virtual_machine" "vm" {
  network_interface_ids = [azurerm_network_interface.nic.id]

  # Only use depends_on for non-resource dependencies
  depends_on = [
    azurerm_marketplace_agreement.agreement  # No attribute to reference
  ]
}
```

### Dynamic Blocks

**Use for optional or repeated nested blocks**:

```hcl
resource "azurerm_linux_virtual_machine" "vm" {
  # ...

  dynamic "plan" {
    for_each = var.use_marketplace_image ? [1] : []

    content {
      name      = var.marketplace_plan.name
      publisher = var.marketplace_plan.publisher
      product   = var.marketplace_plan.product
    }
  }
}
```

## Documentation Standards

### README.md Requirements

Every IaC project must include:

1. **Project Overview** - What infrastructure is created
2. **Architecture Diagram** - Visual representation
3. **Prerequisites** - Required tools, accounts, permissions
4. **Quick Start** - Minimal steps to deploy
5. **Configuration** - How to customize
6. **Common Operations** - Day 2 operations guide
7. **Troubleshooting** - Known issues and solutions

### Variable Documentation

```hcl
variable "instance_type" {
  description = <<-EOT
    Azure VM size for compute instances.

    Common options:
    - Standard_F4s: 4 vCPUs, 8 GB RAM (development/testing)
    - Standard_F8s: 8 vCPUs, 16 GB RAM (production)
    - Standard_F16s: 16 vCPUs, 32 GB RAM (high performance)

    See: https://docs.microsoft.com/azure/virtual-machines/sizes
  EOT
  type    = string
  default = "Standard_F4s"
}
```

### Code Comments

**Comment the "why", not the "what"**:

```hcl
# ✅ Good - Explains reasoning
locals {
  # Use sequential IP allocation from start address to ensure
  # predictable addressing for HA pair configuration
  fortigate_a_ip = var.subnet_start_address
  fortigate_b_ip = cidrhost(var.subnet_prefix, tonumber(split(".", var.subnet_start_address)[3]) + 1)
}

# ❌ Bad - States the obvious
locals {
  # FortiGate A IP address
  fortigate_a_ip = var.subnet_start_address
}
```

## Security Standards

### Sensitive Data Handling

```hcl
# ✅ Mark sensitive variables
variable "admin_password" {
  description = "Administrator password"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.admin_password) >= 12
    error_message = "Password must be at least 12 characters"
  }
}

# ✅ Mark sensitive outputs
output "database_connection_string" {
  description = "Database connection string with credentials"
  value       = "..."
  sensitive   = true
}

# ❌ Never hardcode secrets
resource "azurerm_virtual_machine" "vm" {
  admin_password = "HardcodedPassword123!"  # NEVER DO THIS
}
```

### Encryption Requirements

**All data must be encrypted**:

```hcl
# At rest
resource "azurerm_managed_disk" "disk" {
  encryption_settings {
    enabled = true
  }
}

# In transit
resource "azurerm_storage_account" "storage" {
  enable_https_traffic_only = true
  min_tls_version          = "TLS1_2"
}
```

## Quality Checklist

Before considering code complete:

- [ ] No magic numbers (all extracted to locals_constants.tf)
- [ ] Variables use appropriate types (no string booleans)
- [ ] Related variables grouped into objects
- [ ] All variables have validation rules
- [ ] Sensitive data marked appropriately
- [ ] Resources use for_each, not count
- [ ] Common attributes extracted to locals
- [ ] Implicit dependencies used correctly
- [ ] Documentation complete (README, examples)
- [ ] Security standards applied
- [ ] Outputs organized and documented
- [ ] Code follows DRY principle
- [ ] Naming conventions followed

## Modern Terraform Features

**Use current Terraform capabilities**:

### Preconditions (1.2+)
```hcl
resource "azurerm_subnet" "subnet" {
  for_each = local.subnets

  lifecycle {
    precondition {
      condition     = can(cidrhost(each.value.address_prefixes[0], 10))
      error_message = "Subnet ${each.key} must have at least 10 available IPs"
    }
  }
}
```

### Check Blocks (1.5+)
```hcl
check "health_check" {
  data "http" "health" {
    url = "https://${azurerm_public_ip.lb_ip.ip_address}/health"
  }

  assert {
    condition     = data.http.health.status_code == 200
    error_message = "Load balancer health check failed"
  }
}
```

### Moved Blocks
```hcl
moved {
  from = azurerm_subnet.old_name
  to   = azurerm_subnet.new_name
}
```

---

**Remember**: This style guide represents organizational standards. When in doubt, prioritize:
1. Security
2. Maintainability
3. Simplicity
4. Performance
