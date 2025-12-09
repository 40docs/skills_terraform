# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Claude Code Skill** for building production-quality Terraform infrastructure code. The skill enables proactive application of organizational standards during code generation rather than post-build remediation.

**Core Philosophy**: Build it right the first time using progressive disclosure - load detailed reference documentation only as needed to optimize context usage.

## Repository Structure

```
terraform-builder/
├── SKILL.md                    # Primary skill instructions (auto-loaded by Claude Code)
├── README.md                   # Human-facing documentation
├── references/                 # Detailed standards (loaded conditionally)
│   ├── style-guide.md         # Code organization patterns (~8k words)
│   ├── terraform-patterns.md  # HCL implementation patterns (~12k words)
│   ├── naming-conventions.md  # Terraform naming rules (~3k words)
│   ├── security-standards.md  # Security requirements (~10k words)
│   └── anti-patterns.md       # Common mistakes to avoid (~6k words)
├── assets/templates/terraform/ # Starter templates for new projects
├── scripts/
│   ├── init_project.py        # Initialize new Terraform projects
│   └── validate_structure.py  # Validate code against standards
```

## Key Architecture Concepts

### Progressive Disclosure Pattern

**Critical**: This skill uses progressive disclosure to optimize context window usage. Never load all reference files upfront.

**Loading Strategy**:
- **Simple tasks** (add resource): SKILL.md only (~3k words)
- **Medium tasks** (new module): SKILL.md + naming-conventions + style-guide (~14k words)
- **Complex tasks** (new project with security): SKILL.md + style-guide + naming + security-standards (~24k words)
- **Validation/review**: Add anti-patterns.md to current context

**Decision Tree**:
1. New project? → Load `style-guide.md`
2. Creating resources? → Load `naming-conventions.md`
3. Security/IAM/networking? → Load `security-standards.md`
4. Uncertain about implementation? → Load `terraform-patterns.md`
5. Ready to validate? → Load `anti-patterns.md`

### Core Terraform Patterns Enforced

**Type Safety**:
- Use native `bool` types, never string "yes"/"no"
- Use `object()` for structured data, not separate primitive variables
- Use `number` for numeric values
- Use `map(object())` for collections of structured data

**No Magic Numbers**:
- Extract ALL constants to `locals_constants.tf`
- Examples: ports (8008 → `local.health_probe_port`), IPs, zone numbers, SKUs
- Always provide descriptive names with comments

**DRY Principle**:
- Use `for_each` with locals for multiple similar resources
- Never duplicate resource blocks
- Pattern: `locals_*.tf` defines WHAT to create, `resource_*.tf` defines HOW

**Locals-Based Configuration Pattern**:
```hcl
# locals_network.tf - Configuration as data (WHAT to create)
locals {
  subnets = {
    "web" = { name = "web-subnet", prefix = "10.0.1.0/24" }
    "app" = { name = "app-subnet", prefix = "10.0.2.0/24" }
  }
}

# resource_subnet.tf - Implementation (HOW to create)
resource "azurerm_subnet" "subnet" {
  for_each = local.subnets
  name     = each.value.name
  # ...
}
```

**File Organization**:
- `locals_constants.tf` - Constants and magic numbers
- `locals_common.tf` - Shared reusable attributes
- `locals_<domain>.tf` - Domain-specific configurations (network, compute, etc.)
- `resource_<type>.tf` - Resource implementations
- `variables.tf` - All input variables
- `outputs.tf` - All outputs (organized by category)
- `data.tf` - Data source lookups
- `versions.tf` - Provider version constraints

## Development Commands

### Initialize New Terraform Project

```bash
python scripts/init_project.py \
  --name my-infrastructure \
  --tool terraform \
  --cloud azure \
  --template standard
```

Creates:
- Standard directory structure
- Template files from `assets/templates/terraform/`
- README with project-specific content
- Git repository with pre-commit hooks
- terraform.tfvars.example

### Validate Terraform Code

```bash
python scripts/validate_structure.py \
  --path ./terraform \
  --strict \
  --report validation-report.md
```

**Exit codes**:
- `0` - All checks passed
- `1` - Validation failures found
- `2` - Invalid arguments or script error

**Checks performed**:
- No magic numbers present
- Naming convention compliance
- Required documentation exists
- Security standards met (encryption, IAM, network segmentation)
- No anti-patterns present (no string booleans, no count for similar resources, etc.)
- Variable validation blocks present
- Sensitive values properly marked

### Running Tests

```bash
# Run validation on all Terraform in current directory
python scripts/validate_structure.py --path .

# Strict mode (fail on warnings)
python scripts/validate_structure.py --path . --strict

# Generate markdown report
python scripts/validate_structure.py --path . --report report.md
```

## Working with This Skill

### Modifying Reference Documentation

When updating standards in `references/`:
1. **Test the change** - Ensure examples compile and follow the pattern
2. **Update related files** - Keep style-guide, patterns, and anti-patterns in sync
3. **Update templates** - Reflect changes in `assets/templates/terraform/`
4. **Update validation** - Add checks in `validate_structure.py` if needed

### Adding New Templates

To add cloud-specific templates:
1. Create directory: `assets/templates/terraform-aws/` or `terraform-gcp/`
2. Add resource templates following existing pattern
3. Update `init_project.py` to handle new cloud provider
4. Test initialization: `python scripts/init_project.py --cloud aws --template standard`

### Customizing for Organizations

**Critical files to customize**:
- `references/style-guide.md` - Your code organization conventions
- `references/naming-conventions.md` - Your naming standards
- `references/security-standards.md` - Your security requirements
- `assets/templates/terraform/*.template` - Your boilerplate code
- `scripts/validate_structure.py` - Your validation rules

## Pre-Presentation Validation Checklist

Before presenting Terraform code to users, verify:

```
□ No hardcoded secrets (passwords, keys, tokens)
□ No magic numbers (all extracted to locals_constants.tf)
□ Proper types used (bool not string, object not primitives)
□ Validation blocks on constrained variables
□ Sensitive values marked with sensitive = true
□ Security baseline met (encryption, least privilege, network segmentation)
□ Naming conventions followed (from naming-conventions.md)
□ DRY principle applied (no duplicate resource blocks)
□ for_each used instead of count for similar resources
□ Documentation included (README.md, terraform.tfvars.example)
```

## Common Anti-Patterns to Avoid

**Red flags** (if you encounter these, STOP and load `anti-patterns.md`):
- ❌ `count` for multiple similar resources → Use `for_each`
- ❌ `variable "deploy" { type = string, default = "yes" }` → Use `bool`
- ❌ Hardcoded ports, IPs, SKUs → Extract to `locals_constants.tf`
- ❌ Separate variables for related data → Use `object()` type
- ❌ Duplicate resource blocks → Use `for_each` with locals
- ❌ Missing validation blocks → Add validation with clear error messages

## Skill Activation

**Auto-activates on keywords**: "terraform", "HCL", ".tf files", "terraform module", "terraform project"

**Manual activation**: `@terraform-builder`

When activated, the skill:
1. Asks clarifying questions (cloud provider, environment, security level)
2. Loads relevant references based on task complexity (progressive disclosure)
3. Generates code with standards applied proactively
4. Self-validates before presenting
5. Provides complete project structure with supporting files

## Python Scripts Architecture

### init_project.py

**Purpose**: Bootstrap new Terraform projects with organizational standards baked in

**Key functions**:
- `create_directories()` - Creates standard directory structure
- `copy_templates()` - Copies and customizes template files
- `generate_readme()` - Creates project-specific README
- `init_git()` - Initializes git with pre-commit hooks

### validate_structure.py

**Purpose**: Validate Terraform code against organizational standards

**Key classes**:
- `ValidationResult` - Individual check result
- `IaCValidator` - Main validation orchestrator

**Validation categories**:
- Magic number detection
- Naming convention compliance
- Security standards verification
- Anti-pattern detection
- Documentation completeness

## Context Efficiency Guidelines

**Total reference word count**: ~44k words

**Efficient usage**:
- Load SKILL.md by default (always needed)
- Load naming-conventions.md when creating ANY resources
- Load style-guide.md for NEW projects or organization questions
- Load terraform-patterns.md when uncertain about implementation
- Load security-standards.md for security/IAM/networking tasks
- Load anti-patterns.md during validation phase only

**Example**: Simple S3 bucket creation only needs ~16k words (SKILL + naming + security), not full 44k.

## Success Criteria

Code generated with this skill should:
- ✅ Pass `validate_structure.py` without errors
- ✅ Require zero or minimal remediation
- ✅ Follow organizational patterns consistently
- ✅ Be production-ready and secure by default
- ✅ Include comprehensive documentation
- ✅ Use context efficiently via progressive disclosure
