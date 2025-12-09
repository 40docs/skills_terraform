# Terraform Implementation Patterns

This document provides concrete implementation patterns for common Terraform scenarios, extracted from production codebases.

## Table of Contents

1. [Locals-Based Configuration Pattern](#locals-based-configuration-pattern)
2. [Conditional Resource Deployment](#conditional-resource-deployment)
3. [Common Attributes Pattern](#common-attributes-pattern)
4. [IP Address Management](#ip-address-management)
5. [Load Balancer Patterns](#load-balancer-patterns)
6. [High Availability Patterns](#high-availability-patterns)
7. [Cloud-Init Template Patterns](#cloud-init-template-patterns)
8. [Output Organization](#output-organization)
9. [Variable Transformation](#variable-transformation)
10. [Module Composition](#module-composition)

---

## Locals-Based Configuration Pattern

### Pattern Overview

Separate configuration (what) from implementation (how) using locals and for_each.

### Implementation

```hcl
# ============================================================================
# locals_network.tf - Configuration Layer
# ============================================================================

locals {
  # Define what to create as data
  subnets = {
    "${var.deployment_prefix}-web" = {
      name                 = "web-subnet"
      resource_group_name  = local.resource_group_name
      virtual_network_name = local.vnet_name
      address_prefixes     = ["10.0.1.0/24"]
      service_endpoints    = ["Microsoft.Sql"]
      nsg_id              = azurerm_network_security_group.nsg["web"].id
    }

    "${var.deployment_prefix}-app" = {
      name                 = "app-subnet"
      resource_group_name  = local.resource_group_name
      virtual_network_name = local.vnet_name
      address_prefixes     = ["10.0.2.0/24"]
      service_endpoints    = ["Microsoft.Storage"]
      nsg_id              = azurerm_network_security_group.nsg["app"].id
    }

    "${var.deployment_prefix}-data" = {
      name                 = "data-subnet"
      resource_group_name  = local.resource_group_name
      virtual_network_name = local.vnet_name
      address_prefixes     = ["10.0.3.0/24"]
      service_endpoints    = ["Microsoft.Sql", "Microsoft.Storage"]
      nsg_id              = azurerm_network_security_group.nsg["data"].id
    }
  }
}

# ============================================================================
# resource_subnet.tf - Implementation Layer
# ============================================================================

resource "azurerm_subnet" "subnet" {
  for_each = local.subnets

  name                 = each.value.name
  resource_group_name  = each.value.resource_group_name
  virtual_network_name = each.value.virtual_network_name
  address_prefixes     = each.value.address_prefixes
  service_endpoints    = each.value.service_endpoints
}

resource "azurerm_subnet_network_security_group_association" "nsg_association" {
  for_each = local.subnets

  subnet_id                 = azurerm_subnet.subnet[each.key].id
  network_security_group_id = each.value.nsg_id
}
```

### Benefits

- ✅ All subnet configurations visible in one place
- ✅ Easy to add/remove subnets
- ✅ Single resource block handles all instances
- ✅ Configuration changes don't require code changes
- ✅ Clear separation between data and logic

### When to Use

- Multiple resources of the same type
- Configuration needs to be dynamic or conditional
- Resource definitions share common structure
- Want to enable/disable resources via variables

---

## Conditional Resource Deployment

### Pattern: Merge with Ternary

Use `merge()` with ternary operators for optional components.

```hcl
# ============================================================================
# locals_web_tier.tf - Always deployed
# ============================================================================

locals {
  web_vms = {
    "${var.deployment_prefix}-web-01" = {
      name     = "web-01"
      vm_size  = "Standard_F4s"
      subnet   = "web"
      # ... configuration
    }
  }
}

# ============================================================================
# locals_app_tier.tf - Conditionally deployed
# ============================================================================

locals {
  app_vms = var.deploy_app_tier ? {
    "${var.deployment_prefix}-app-01" = {
      name     = "app-01"
      vm_size  = "Standard_F8s"
      subnet   = "app"
      # ... configuration
    }
    "${var.deployment_prefix}-app-02" = {
      name     = "app-02"
      vm_size  = "Standard_F8s"
      subnet   = "app"
      # ... configuration
    }
  } : {}  # Empty map when not deployed
}

# ============================================================================
# locals_compute.tf - Merge all components
# ============================================================================

locals {
  virtual_machines = merge(
    local.web_vms,      # Always included
    local.app_vms,      # Empty map if deploy_app_tier = false
    local.db_vms        # Empty map if deploy_db_tier = false
  )
}

# ============================================================================
# resource_virtual_machine.tf - Single implementation
# ============================================================================

resource "azurerm_linux_virtual_machine" "vm" {
  for_each = local.virtual_machines

  name                = each.value.name
  resource_group_name = each.value.resource_group_name
  size                = each.value.vm_size
  # ... rest of configuration
}
```

### Advanced: Conditional with Count

```hcl
# For resources that don't work well with for_each
locals {
  optional_resource_count = var.deploy_feature ? 1 : 0
}

resource "azurerm_resource" "optional" {
  count = local.optional_resource_count

  # Configuration
}

# Reference: azurerm_resource.optional[0] when count = 1
```

---

## Common Attributes Pattern

### Problem

Resource group name and location repeated in every resource definition.

### Solution

Extract common attributes to reusable locals.

```hcl
# ============================================================================
# locals_common.tf
# ============================================================================

locals {
  # Foundational resources
  resource_group_name = "${var.deployment_prefix}-rg"
  location           = coalesce(var.location, "canadacentral")
  vnet_name          = coalesce(var.vnet_name, "${var.deployment_prefix}-vnet")

  # Common resource attributes
  common_resource_attributes = {
    resource_group_name = azurerm_resource_group.rg[local.resource_group_name].name
    location            = azurerm_resource_group.rg[local.resource_group_name].location
  }

  # Common tags
  common_tags = merge(
    var.tags,
    {
      managed_by = "terraform"
      deployment = var.deployment_prefix
      created_at = timestamp()
    }
  )
}

# ============================================================================
# locals_network.tf - Using common attributes
# ============================================================================

locals {
  virtual_networks = {
    local.vnet_name = merge(
      local.common_resource_attributes,  # Includes resource_group_name, location
      {
        name          = local.vnet_name
        address_space = [var.vnet_address_prefix]
        tags          = local.common_tags
      }
    )
  }

  subnets = {
    for key, config in var.subnet_configs :
    "${var.deployment_prefix}-${key}" => merge(
      local.common_resource_attributes,  # Reuse common attributes
      {
        name                 = config.name
        virtual_network_name = azurerm_virtual_network.vnet[local.vnet_name].name
        address_prefixes     = [config.address_prefix]
        tags                = local.common_tags
      }
    )
  }
}
```

### Benefits

- Change resource group reference once, applies everywhere
- Consistent location across all resources
- Centralized tag management
- Reduced code duplication

---

## IP Address Management

### Sequential IP Allocation Pattern

Allocate IPs sequentially from a start address for HA pairs.

```hcl
# ============================================================================
# variables.tf
# ============================================================================

variable "subnets" {
  description = "Subnet configurations with sequential IP allocation"
  type = map(object({
    name              = string
    address_prefix    = string
    start_address     = string  # First usable IP in sequence
    required_ip_count = number  # How many IPs needed
  }))

  default = {
    external = {
      name              = "external-subnet"
      address_prefix    = "10.0.1.0/24"
      start_address     = "10.0.1.4"
      required_ip_count = 2  # Device A + Device B
    }
  }
}

# ============================================================================
# locals_compute.tf
# ============================================================================

locals {
  # Extract last octet from start address
  subnet_start_octets = {
    for key, subnet in var.subnets :
    key => tonumber(split(".", subnet.start_address)[3])
  }

  # Generate sequential IPs
  network_interfaces = {
    # Device A - Uses start address
    "${var.deployment_prefix}-device-a-nic1" = {
      name               = "device-a-nic1"
      subnet_id          = azurerm_subnet.subnet["external"].id
      private_ip_address = var.subnets["external"].start_address
      # ...
    }

    # Device B - Start address + 1
    "${var.deployment_prefix}-device-b-nic1" = {
      name               = "device-b-nic1"
      subnet_id          = azurerm_subnet.subnet["external"].id
      private_ip_address = cidrhost(
        var.subnets["external"].address_prefix,
        local.subnet_start_octets["external"] + 1
      )
      # ...
    }
  }
}
```

### Load Balancer Static IP Pattern

```hcl
locals {
  load_balancers = {
    "${var.deployment_prefix}-internal-lb" = {
      name = "internal-lb"
      frontend_ip_configurations = [{
        name                          = "internal-frontend"
        subnet_id                     = azurerm_subnet.subnet["internal"].id
        private_ip_address           = var.subnets["internal"].start_address
        private_ip_address_allocation = "Static"
      }]
    }
  }
}
```

### IP Validation Pattern

```hcl
variable "start_address" {
  description = "Starting IP address for sequential allocation"
  type        = string

  validation {
    condition = can(regex(
      "^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}$",
      var.start_address
    ))
    error_message = "start_address must be a valid IPv4 address (e.g., 10.0.1.5)"
  }

  validation {
    condition     = can(cidrhost(var.subnet_prefix, tonumber(split(".", var.start_address)[3])))
    error_message = "start_address must be within subnet_prefix range"
  }
}
```

---

## Load Balancer Patterns

### Complete Load Balancer with HA Port

```hcl
# ============================================================================
# locals_load_balancer.tf
# ============================================================================

locals {
  load_balancers = {
    # Internal LB for backend traffic
    "${var.deployment_prefix}-internal-lb" = {
      name                = "internal-lb"
      sku                 = "Standard"
      resource_group_name = local.common_resource_attributes.resource_group_name
      location            = local.common_resource_attributes.location

      frontend_ip_configuration = [{
        name                          = "internal-frontend"
        subnet_id                     = azurerm_subnet.subnet["internal"].id
        private_ip_address           = var.subnets["internal"].start_address
        private_ip_address_allocation = "Static"
      }]
    }

    # External LB for public traffic
    "${var.deployment_prefix}-external-lb" = {
      name                = "external-lb"
      sku                 = "Standard"
      resource_group_name = local.common_resource_attributes.resource_group_name
      location            = local.common_resource_attributes.location

      frontend_ip_configuration = [{
        name                 = "external-frontend"
        public_ip_address_id = azurerm_public_ip.pip["external-lb-pip"].id
      }]
    }
  }

  # Backend address pools
  lb_backend_pools = {
    "${var.deployment_prefix}-internal-backend" = {
      name            = "internal-backend"
      loadbalancer_id = azurerm_lb.lb["${var.deployment_prefix}-internal-lb"].id
    }
    "${var.deployment_prefix}-external-backend" = {
      name            = "external-backend"
      loadbalancer_id = azurerm_lb.lb["${var.deployment_prefix}-external-lb"].id
    }
  }

  # Health probes
  lb_probes = {
    "${var.deployment_prefix}-internal-probe" = {
      name                = "health-probe"
      protocol            = "Tcp"
      port                = local.health_probe_port
      interval_in_seconds = 5
      number_of_probes    = 2
      loadbalancer_id     = azurerm_lb.lb["${var.deployment_prefix}-internal-lb"].id
    }
  }

  # Load balancing rules
  lb_rules = {
    # HA Port rule - All traffic on all ports
    "${var.deployment_prefix}-internal-ha-ports" = {
      name                           = "ha-ports"
      protocol                       = "All"
      frontend_port                  = 0
      backend_port                   = 0
      frontend_ip_configuration_name = "internal-frontend"
      backend_address_pool_id        = azurerm_lb_backend_address_pool.pool["${var.deployment_prefix}-internal-backend"].id
      probe_id                       = azurerm_lb_probe.probe["${var.deployment_prefix}-internal-probe"].id
      loadbalancer_id               = azurerm_lb.lb["${var.deployment_prefix}-internal-lb"].id
      enable_floating_ip            = true  # Required for HA Port
      load_distribution             = "Default"  # 5-tuple hash
    }

    # Specific port rules for external LB
    "${var.deployment_prefix}-external-https" = {
      name                           = "https"
      protocol                       = "Tcp"
      frontend_port                  = 443
      backend_port                   = 443
      frontend_ip_configuration_name = "external-frontend"
      backend_address_pool_id        = azurerm_lb_backend_address_pool.pool["${var.deployment_prefix}-external-backend"].id
      probe_id                       = azurerm_lb_probe.probe["${var.deployment_prefix}-external-probe"].id
      loadbalancer_id               = azurerm_lb.lb["${var.deployment_prefix}-external-lb"].id
      enable_floating_ip            = false
    }
  }

  # NAT rules for management access
  lb_nat_rules = {
    "${var.deployment_prefix}-ssh-device-a" = {
      name                           = "ssh-device-a"
      protocol                       = "Tcp"
      frontend_port                  = 50022
      backend_port                   = 22
      frontend_ip_configuration_name = "external-frontend"
      loadbalancer_id               = azurerm_lb.lb["${var.deployment_prefix}-external-lb"].id
    }
    "${var.deployment_prefix}-ssh-device-b" = {
      name                           = "ssh-device-b"
      protocol                       = "Tcp"
      frontend_port                  = 50023
      backend_port                   = 22
      frontend_ip_configuration_name = "external-frontend"
      loadbalancer_id               = azurerm_lb.lb["${var.deployment_prefix}-external-lb"].id
    }
  }
}

# ============================================================================
# Resource implementations
# ============================================================================

resource "azurerm_lb" "lb" {
  for_each = local.load_balancers

  name                = each.value.name
  location            = each.value.location
  resource_group_name = each.value.resource_group_name
  sku                 = each.value.sku

  dynamic "frontend_ip_configuration" {
    for_each = each.value.frontend_ip_configuration

    content {
      name                          = frontend_ip_configuration.value.name
      subnet_id                     = lookup(frontend_ip_configuration.value, "subnet_id", null)
      private_ip_address           = lookup(frontend_ip_configuration.value, "private_ip_address", null)
      private_ip_address_allocation = lookup(frontend_ip_configuration.value, "private_ip_address_allocation", "Dynamic")
      public_ip_address_id         = lookup(frontend_ip_configuration.value, "public_ip_address_id", null)
    }
  }
}

resource "azurerm_lb_backend_address_pool" "pool" {
  for_each = local.lb_backend_pools

  name            = each.value.name
  loadbalancer_id = each.value.loadbalancer_id
}

resource "azurerm_lb_probe" "probe" {
  for_each = local.lb_probes

  name                = each.value.name
  protocol            = each.value.protocol
  port                = each.value.port
  interval_in_seconds = each.value.interval_in_seconds
  number_of_probes    = each.value.number_of_probes
  loadbalancer_id     = each.value.loadbalancer_id
}

resource "azurerm_lb_rule" "rule" {
  for_each = local.lb_rules

  name                           = each.value.name
  protocol                       = each.value.protocol
  frontend_port                  = each.value.frontend_port
  backend_port                   = each.value.backend_port
  frontend_ip_configuration_name = each.value.frontend_ip_configuration_name
  backend_address_pool_ids       = [each.value.backend_address_pool_id]
  probe_id                       = each.value.probe_id
  loadbalancer_id               = each.value.loadbalancer_id
  enable_floating_ip            = each.value.enable_floating_ip
  load_distribution             = lookup(each.value, "load_distribution", "Default")
}

resource "azurerm_lb_nat_rule" "nat" {
  for_each = local.lb_nat_rules

  name                           = each.value.name
  protocol                       = each.value.protocol
  frontend_port                  = each.value.frontend_port
  backend_port                   = each.value.backend_port
  frontend_ip_configuration_name = each.value.frontend_ip_configuration_name
  resource_group_name            = local.common_resource_attributes.resource_group_name
  loadbalancer_id               = each.value.loadbalancer_id
}

# Associate NICs with backend pools
resource "azurerm_network_interface_backend_address_pool_association" "nic_pool" {
  for_each = {
    for key, nic in local.network_interfaces :
    key => nic if lookup(nic, "backend_pool_id", null) != null
  }

  network_interface_id    = azurerm_network_interface.nic[each.key].id
  ip_configuration_name   = "ipconfig1"
  backend_address_pool_id = each.value.backend_pool_id
}
```

---

## High Availability Patterns

### Active-Active HA with Priority

```hcl
# ============================================================================
# locals_ha_cluster.tf
# ============================================================================

locals {
  ha_config = {
    device_a = {
      priority          = 255  # Higher priority (primary)
      ha_group_id      = 1
      ha_cluster_ip    = var.subnets["ha"].start_address
      availability_zone = var.use_availability_zones ? "1" : null
    }
    device_b = {
      priority          = 1    # Lower priority (secondary)
      ha_group_id      = 1
      ha_cluster_ip    = var.subnets["ha"].start_address
      availability_zone = var.use_availability_zones ? "2" : null
    }
  }

  virtual_machines = {
    for device, config in local.ha_config :
    "${var.deployment_prefix}-${device}" => {
      name              = device
      size              = var.instance_type
      zone              = config.availability_zone
      ha_priority       = config.priority
      ha_group_id       = config.ha_group_id
      # Cloud-init will configure HA using these values
      custom_data = base64encode(templatefile(
        "${path.module}/cloud-init/ha-device.tpl",
        {
          var_ha_priority    = config.priority
          var_ha_group_id    = config.ha_group_id
          var_ha_cluster_ip  = config.ha_cluster_ip
        }
      ))
    }
  }
}
```

### Availability Zones vs Availability Sets

```hcl
# ============================================================================
# variables.tf
# ============================================================================

variable "availability_option" {
  description = "High availability deployment option"
  type        = string
  default     = "availability_zones"

  validation {
    condition = contains([
      "availability_zones",
      "availability_set",
      "none"
    ], var.availability_option)
    error_message = "Must be: availability_zones, availability_set, or none"
  }
}

# ============================================================================
# locals_compute.tf
# ============================================================================

locals {
  # Create availability set if needed
  availability_sets = var.availability_option == "availability_set" ? {
    "${var.deployment_prefix}-avset" = {
      name                         = "ha-availability-set"
      resource_group_name          = local.common_resource_attributes.resource_group_name
      location                     = local.common_resource_attributes.location
      platform_fault_domain_count  = 2
      platform_update_domain_count = 5
      managed                      = true
    }
  } : {}

  # Assign zones or availability set
  virtual_machines = {
    for key, vm in local.base_vms :
    key => merge(vm, {
      # Zones for active-active
      zone = var.availability_option == "availability_zones" ? (
        contains(["device-a"], vm.name) ? "1" : "2"
      ) : null

      # Availability set ID
      availability_set_id = var.availability_option == "availability_set" ? (
        azurerm_availability_set.avset["${var.deployment_prefix}-avset"].id
      ) : null
    })
  }
}
```

---

## Cloud-Init Template Patterns

### Structured Template with Variables

```hcl
# ============================================================================
# locals_compute.tf
# ============================================================================

locals {
  virtual_machines = {
    "${var.deployment_prefix}-web-01" = {
      name = "web-01"
      # ...

      custom_data = base64encode(templatefile(
        "${path.module}/cloud-init/web-server.tpl",
        {
          # Prefix all template variables with var_ to distinguish from Terraform vars
          var_hostname          = "web-01"
          var_admin_username    = var.admin_username
          var_app_environment   = var.environment
          var_database_endpoint = azurerm_mysql_server.db.fqdn
          var_backend_api_url   = local.backend_api_url
        }
      ))
    }
  }
}
```

```yaml
# ============================================================================
# cloud-init/web-server.tpl
# ============================================================================

#cloud-config

# Set hostname
hostname: ${var_hostname}
fqdn: ${var_hostname}.internal.local

# Create admin user
users:
  - name: ${var_admin_username}
    sudo: ALL=(ALL) NOPASSWD:ALL
    shell: /bin/bash
    ssh_authorized_keys:
      - ${var_admin_ssh_key}

# Install packages
packages:
  - nginx
  - certbot
  - python3-certbot-nginx

# Write configuration files
write_files:
  - path: /etc/nginx/conf.d/app.conf
    content: |
      upstream backend {
        server ${var_backend_api_url};
      }

      server {
        listen 80;
        server_name _;

        location /api/ {
          proxy_pass http://backend;
          proxy_set_header Host $host;
        }
      }

  - path: /etc/environment
    content: |
      APP_ENVIRONMENT=${var_app_environment}
      DATABASE_ENDPOINT=${var_database_endpoint}

# Run commands
runcmd:
  - systemctl enable nginx
  - systemctl start nginx
  - echo "Web server configured successfully" >> /var/log/cloud-init-complete.log
```

---

## Output Organization

### Structured Output Pattern

```hcl
# ============================================================================
# outputs.tf
# ============================================================================

###############################################################################
# Resource Groups
###############################################################################

output "resource_groups" {
  description = "Resource group details (debug)"
  value       = var.debug_outputs ? azurerm_resource_group.rg : null
}

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
# Public IPs and Connection Information
###############################################################################

output "public_ip_addresses" {
  description = "Public IP addresses for external access"
  value = {
    for key, pip in azurerm_public_ip.pip :
    key => pip.ip_address
  }
}

output "connection_information" {
  description = "Connection details for deployed resources"
  value = {
    ssh_commands = {
      for name, vm in local.virtual_machines :
      name => "ssh ${var.admin_username}@${azurerm_public_ip.pip["${name}-pip"].ip_address}"
      if lookup(vm, "public_ip", false)
    }

    web_urls = {
      for name, vm in local.virtual_machines :
      name => "https://${azurerm_public_ip.pip["${name}-pip"].ip_address}"
      if lookup(vm, "web_server", false)
    }

    management_urls = {
      load_balancer = "https://${azurerm_public_ip.pip["external-lb-pip"].ip_address}:8443"
    }
  }
}

###############################################################################
# Sensitive Outputs
###############################################################################

output "database_connection_string" {
  description = "Database connection string with credentials"
  sensitive   = true
  value       = "Server=${azurerm_mysql_server.db.fqdn};Database=${var.database_name};Uid=${var.admin_username};Pwd=${var.admin_password};"
}

###############################################################################
# Deployment Summary
###############################################################################

output "deployment_summary" {
  description = "Summary of deployed resources"
  value = {
    deployment_prefix    = var.deployment_prefix
    location            = local.common_resource_attributes.location
    resource_group_name = local.common_resource_attributes.resource_group_name
    vm_count            = length(local.virtual_machines)
    subnet_count        = length(local.subnets)
    deployed_features = {
      web_tier    = length(local.web_vms) > 0
      app_tier    = length(local.app_vms) > 0
      database    = var.deploy_database
      monitoring  = var.deploy_monitoring
    }
  }
}
```

---

## Variable Transformation

### Transform Simple Input to Complex Structure

```hcl
# ============================================================================
# variables.tf - Simple user inputs
# ============================================================================

variable "web_server_count" {
  description = "Number of web servers to deploy"
  type        = number
  default     = 2
}

variable "web_server_size" {
  description = "VM size for web servers"
  type        = string
  default     = "Standard_F4s"
}

# ============================================================================
# locals_compute.tf - Transform to structured configuration
# ============================================================================

locals {
  # Generate web server configurations from count
  web_vms = {
    for i in range(var.web_server_count) :
    "${var.deployment_prefix}-web-${format("%02d", i + 1)}" => {
      name     = "web-${format("%02d", i + 1)}"
      vm_size  = var.web_server_size
      zone     = tostring((i % 3) + 1)  # Distribute across zones
      subnet   = "web-subnet"
      nsg      = "web-nsg"
      role     = "web-server"
      index    = i

      # Progressive configuration
      backend_pool = i < 2 ? "primary-pool" : "secondary-pool"
      priority     = i == 0 ? "primary" : "secondary"
    }
  }
}
```

### Environment-Specific Configuration

```hcl
# ============================================================================
# locals_environment.tf
# ============================================================================

locals {
  # Environment-specific sizing
  environment_config = {
    dev = {
      vm_size            = "Standard_F2s"
      enable_monitoring  = false
      backup_retention   = 7
      enable_autoscale   = false
    }
    staging = {
      vm_size            = "Standard_F4s"
      enable_monitoring  = true
      backup_retention   = 14
      enable_autoscale   = true
    }
    prod = {
      vm_size            = "Standard_F8s"
      enable_monitoring  = true
      backup_retention   = 30
      enable_autoscale   = true
    }
  }

  # Select configuration based on environment variable
  current_config = local.environment_config[var.environment]

  # Apply to resources
  virtual_machines = {
    for key, vm in local.base_vm_config :
    key => merge(vm, {
      vm_size = local.current_config.vm_size
    })
  }
}
```

---

## Module Composition

### Root Module Calling Child Modules

```hcl
# ============================================================================
# main.tf - Root module
# ============================================================================

module "network" {
  source = "./modules/network"

  deployment_prefix   = var.deployment_prefix
  location           = var.location
  resource_group_name = azurerm_resource_group.rg.name
  vnet_address_space = var.vnet_address_space
  subnet_configs     = var.subnet_configs
  tags               = local.common_tags
}

module "compute" {
  source = "./modules/compute"

  deployment_prefix   = var.deployment_prefix
  location           = var.location
  resource_group_name = azurerm_resource_group.rg.name

  # Pass outputs from network module
  subnet_ids = module.network.subnet_ids
  nsg_ids    = module.network.nsg_ids

  # VM configurations
  vm_configs = var.vm_configs
  tags       = local.common_tags

  depends_on = [module.network]
}

module "database" {
  source = "./modules/database"
  count  = var.deploy_database ? 1 : 0

  deployment_prefix   = var.deployment_prefix
  location           = var.location
  resource_group_name = azurerm_resource_group.rg.name

  # Pass network information
  subnet_id           = module.network.subnet_ids["database"]
  allowed_subnets     = [module.network.subnet_ids["app"]]

  # Database configuration
  database_config = var.database_config
  admin_username  = var.admin_username
  admin_password  = var.admin_password
  tags           = local.common_tags
}
```

### Module with Conditional Outputs

```hcl
# ============================================================================
# modules/compute/outputs.tf
# ============================================================================

output "vm_ids" {
  description = "Map of VM names to resource IDs"
  value = {
    for key, vm in azurerm_linux_virtual_machine.vm :
    key => vm.id
  }
}

output "vm_private_ips" {
  description = "Map of VM names to private IP addresses"
  value = {
    for key, vm in azurerm_linux_virtual_machine.vm :
    key => vm.private_ip_address
  }
}

output "vm_public_ips" {
  description = "Map of VM names to public IP addresses (if assigned)"
  value = {
    for key, vm in azurerm_linux_virtual_machine.vm :
    key => azurerm_public_ip.pip[key].ip_address
    if lookup(local.virtual_machines[key], "assign_public_ip", false)
  }
}

output "lb_backend_pool_ids" {
  description = "Load balancer backend pool IDs for external association"
  value = {
    for key, pool in azurerm_lb_backend_address_pool.pool :
    key => pool.id
  }
}
```

---

**Remember**: These patterns are proven in production. Use them as templates and adapt to your specific requirements while maintaining the core principles.
