# Terraform Builder Skill

A comprehensive skill for Claude Code that enables proactive Terraform development following established style guides and best practices.

## Purpose

**Build it right the first time.** This skill ensures Terraform code is created correctly from the start, eliminating the need for post-build analysis and remediation cycles.

## What This Skill Does

When activated, Claude will:

1. **Load organizational standards** before writing any code
2. **Apply best practices proactively** during code generation
3. **Validate compliance** against style guide requirements
4. **Generate complete project structure** with all supporting files
5. **Ensure security standards** are built in from the start

## Skill Structure

```
terraform-builder/
├── SKILL.md                          # Main skill instructions for Claude
├── README.md                         # This file (documentation for humans)
│
├── references/                       # Detailed standards and patterns
│   ├── style-guide.md               # Core Terraform style standards
│   ├── terraform-patterns.md        # HCL implementation patterns
│   ├── naming-conventions.md        # Terraform naming conventions
│   ├── security-standards.md        # Security requirements for Terraform
│   └── anti-patterns.md             # Common Terraform mistakes to avoid
│
├── assets/
│   ├── templates/                   # Starter templates
│   │   └── terraform/
│   │       ├── main.tf.template
│   │       ├── variables.tf.template
│   │       ├── outputs.tf.template
│   │       ├── versions.tf.template
│   │       └── locals_constants.tf.template
│   └── examples/                    # Reference Terraform implementations
│
└── scripts/
    ├── init_project.py              # Initialize new Terraform projects
    └── validate_structure.py        # Validate Terraform code against standards
```

## Installation

### For Claude Code Users

1. **Place skill in your skills directory**:
   ```bash
   cp -r terraform-builder ~/.claude/skills/
   ```

2. **Verify installation**:
   ```bash
   # In Claude Code
   /skills list
   # Should show "terraform-builder" in available skills
   ```

### For Development

1. **Clone or copy the skill directory**
2. **Review and customize standards** in `references/` directory
3. **Update templates** in `assets/templates/` to match your organization
4. **Test with sample projects**

## Usage

### Automatic Activation

The skill automatically activates when Claude detects:
- Keywords: "terraform", "HCL", ".tf files", "terraform module"
- User requests for Terraform code creation or modification
- Terraform code review or validation requests

### Manual Activation

```
@terraform-builder Create a new Azure Terraform module
```

### Example Workflow

**User**: "Create Terraform code for an Azure web application with database"

**Claude's Process** (automatic with this skill):

1. ✅ Asks clarifying questions about requirements
2. ✅ Loads relevant references based on task complexity (progressive disclosure)
3. ✅ Plans architecture following organizational patterns
4. ✅ Generates Terraform code with standards applied:
   - Native `bool` types (not string "yes"/"no")
   - Structured variables (not separate primitives)
   - Constants extracted (no magic numbers)
   - Security baseline (encryption, network segmentation)
   - Comprehensive documentation
5. ✅ Self-validates before presenting
6. ✅ Provides complete project structure

**Result**: Production-ready code that passes organizational standards on first generation.

## Key Features

### 1. Proactive Standards Application

- ✅ No string booleans - uses native `bool` type
- ✅ No magic numbers - extracted to `locals_constants.tf`
- ✅ Structured variables - uses `object()` for related data
- ✅ Comprehensive validation - all variables validated
- ✅ Security baseline - encryption, IAM, network segmentation
- ✅ Proper organization - locals pattern with separation of concerns

### 2. Complete Project Generation

Generates:
- Main infrastructure files
- Variable definitions with validation
- Organized outputs
- Constants file
- README.md with architecture overview
- terraform.tfvars.example
- .gitignore
- CONTRIBUTING.md
- Pre-commit hooks

### 3. Quality Validation

Built-in validation script checks:
- No magic numbers present
- Naming convention compliance
- Required documentation exists
- Security standards met
- No anti-patterns present

## Scripts

### Initialize New Project

```bash
python scripts/init_project.py \
  --name my-infrastructure \
  --tool terraform \
  --cloud azure \
  --template standard
```

Creates complete project structure with:
- Standard directory layout
- Template files customized for your project
- Git repository with initial commit
- Pre-commit hooks for validation

### Validate Existing Code

```bash
python scripts/validate_structure.py \
  --path ./terraform \
  --strict \
  --report validation-report.md
```

Checks:
- ✅ File structure compliance
- ✅ No magic numbers
- ✅ Naming conventions
- ✅ Documentation completeness
- ✅ Security standards
- ✅ Variable validation
- ✅ Output organization

**Exit codes**:
- `0` = All checks passed
- `1` = Validation failures found
- `2` = Invalid arguments or script error

## Customization

### For Your Organization

1. **Update references/** to match your standards:
   - Edit `style-guide.md` with your conventions
   - Customize `naming-conventions.md` for your naming rules
   - Update `security-standards.md` with your requirements

2. **Modify templates** in `assets/templates/`:
   - Add your organization's boilerplate
   - Include required provider configurations
   - Add standard tags and metadata

3. **Extend validation** in `scripts/validate_structure.py`:
   - Add organization-specific checks
   - Customize severity levels
   - Add custom patterns to detect

### For Specific Cloud Providers

Templates support:
- **Azure** (primary examples with azurerm provider)
- **AWS** (commented examples with aws provider)
- **GCP** (basic support with google provider)
- **Multi-cloud** (patterns for managing multiple providers)

To add cloud-specific templates:
1. Create `assets/templates/terraform-aws/` or `terraform-gcp/`
2. Add cloud-specific Terraform resource templates
3. Update `init_project.py` to handle new cloud providers

## Reference Materials

### Core Documents

- **[SKILL.md](SKILL.md)** - Instructions for Claude (how the skill works)
- **[references/style-guide.md](references/style-guide.md)** - Core style standards
- **[references/terraform-patterns.md](references/terraform-patterns.md)** - Implementation patterns
- **[references/naming-conventions.md](references/naming-conventions.md)** - Naming rules
- **[references/security-standards.md](references/security-standards.md)** - Security requirements
- **[references/anti-patterns.md](references/anti-patterns.md)** - What to avoid

### Key Concepts

#### Locals-Based Configuration Pattern
```hcl
# locals_network.tf - WHAT to create
locals {
  subnets = {
    "web" = { name = "web-subnet", prefix = "10.0.1.0/24" }
    "app" = { name = "app-subnet", prefix = "10.0.2.0/24" }
  }
}

# resource_subnet.tf - HOW to create
resource "azurerm_subnet" "subnet" {
  for_each = local.subnets
  name     = each.value.name
  # ...
}
```

#### No Magic Numbers
```hcl
# ❌ Bad
port = 8008  # What is this?

# ✅ Good
# locals_constants.tf
locals {
  health_probe_port = 8008  # FortiGate health check service
}

# Usage
port = local.health_probe_port
```

#### Native Boolean Types
```hcl
# ❌ Bad
variable "deploy" {
  type = string
  validation {
    condition = contains(["yes", "no"], var.deploy)
  }
}

# ✅ Good
variable "deploy_feature" {
  type    = bool
  default = true
}
```

## Success Criteria

Code generated with this skill should:

- ✅ Pass organizational code review on first submission
- ✅ Require zero or minimal remediation
- ✅ Meet security compliance requirements
- ✅ Follow established architectural patterns
- ✅ Be maintainable by team members
- ✅ Scale appropriately for production use
- ✅ Include comprehensive documentation

## Comparison: Before vs After

### Before This Skill

**User**: "Create Terraform for Azure VMs"

**Claude** (without skill):
```hcl
# Basic approach - requires significant remediation

variable "deploy" { type = string, default = "yes" }  # ❌ String boolean

resource "azurerm_virtual_machine" "vm1" {
  name = "vm-1"
  size = "Standard_F4s"  # ❌ Not environment-aware
  # ... repeated for each VM
}

resource "azurerm_virtual_machine" "vm2" {
  name = "vm-2"
  size = "Standard_F4s"  # ❌ Duplicate code
  # ...
}

# port = 8008  # ❌ Magic number
# Missing: validation, constants, documentation
```

**Result**: Requires extensive remediation before production use.

### After This Skill

**User**: "Create Terraform for Azure VMs"

**Claude** (with iac-builder skill):
```hcl
# Loads standards automatically
# Applies best practices proactively

variable "deploy_feature" { type = bool, default = true }  # ✅ Native bool

# locals_constants.tf
locals {
  health_probe_port = 8008  # ✅ Documented constant
  instance_types = {
    dev  = "Standard_B2s"
    prod = "Standard_F4s"
  }  # ✅ Environment-aware
}

# locals_compute.tf - Configuration as data
locals {
  virtual_machines = {
    "vm-01" = { size = local.instance_types[var.environment] }
    "vm-02" = { size = local.instance_types[var.environment] }
  }  # ✅ DRY principle
}

# resource_virtual_machine.tf - Single implementation
resource "azurerm_linux_virtual_machine" "vm" {
  for_each = local.virtual_machines  # ✅ for_each pattern
  # ... with validation, security baseline, documentation
}
```

**Result**: Production-ready code, zero remediation needed.

## Troubleshooting

### Skill Not Activating

**Problem**: Claude doesn't automatically apply Terraform standards

**Solutions**:
1. Verify skill is in correct directory: `~/.claude/skills/terraform-builder/`
2. Manually activate: `@terraform-builder`
3. Use trigger keywords: "terraform", "HCL", ".tf files", "terraform module"

### Validation Script Errors

**Problem**: `validate_structure.py` fails to run

**Solutions**:
1. Ensure Python 3.7+ installed: `python3 --version`
2. Make script executable: `chmod +x scripts/validate_structure.py`
3. Check path argument: `--path ./terraform`

### Standards Don't Match Organization

**Problem**: Generated code doesn't match your org's standards

**Solutions**:
1. Customize `references/style-guide.md` with your conventions
2. Update templates in `assets/templates/` with your boilerplate
3. Modify validation script to check your specific requirements

## Contributing

To improve this skill:

1. **Identify new anti-patterns** from production issues
2. **Extract patterns** from successful implementations
3. **Update reference docs** with new standards
4. **Add validation checks** for new requirements
5. **Test with real projects** before committing changes

## Support

- **Issues**: Report problems or suggest improvements
- **Documentation**: See `references/` directory for detailed standards
- **Examples**: Check `assets/examples/` for reference implementations

## License

<!-- Add your license information -->

---

**Remember**: The goal is to build infrastructure code right the first time, every time.
