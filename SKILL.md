---
name: terraform-builder
description: Build production-quality Terraform infrastructure code following established style guides and best practices. Use when creating new Terraform code, setting up Terraform projects, modules, or when user mentions building/creating infrastructure, terraform, HCL, terraform modules, or .tf files. Also use when reviewing or validating existing Terraform code against standards. Applies organizational standards using progressive disclosure - loads detailed references only as needed.
---

# Terraform Builder Skill

## Core Principle

**Build it right the first time** by applying organizational standards during code generation, not after. Use progressive disclosure to load only the references needed for each task.

## When to Use This Skill

**Auto-activates on**:
- Keywords: "terraform", "HCL", ".tf files", "terraform module", "terraform project"
- User requests for Terraform code creation or modification
- Terraform code review or validation requests
- Starting new Terraform projects or modules

**Manual activation**: `@terraform-builder`

---

## Workflow

### Step 1: Understand Requirements

Ask clarifying questions:
- **What infrastructure?** (compute, network, storage, database, etc.)
- **Which cloud provider?** (AWS, Azure, GCP, multi-cloud)
- **Environment?** (dev, staging, prod)
- **Security level?** (public internet, private only, compliance requirements)
- **Existing code?** (greenfield vs adding to existing Terraform project)
- **Module or root?** (standalone module vs root configuration)

### Step 2: Load Relevant References (Progressive Disclosure)

**⚠️ CRITICAL**: Do NOT load all references upfront. Load conditionally based on task needs.

#### Load `references/style-guide.md` when:
- ✅ Starting a **new project from scratch**
- ✅ Unsure about **overall code organization** patterns
- ✅ First time using this skill on a project
- ✅ Need to understand **file structure** decisions
- ❌ NOT needed for simple additions to existing code

#### Load `references/naming-conventions.md` when:
- ✅ Creating **any new resources** (always for naming)
- ✅ Unsure about variable/resource/module names
- ✅ User asks about naming standards
- ✅ Working across multiple cloud providers
- ❌ Can skip if following clear existing naming patterns

#### Load `references/terraform-patterns.md` when:
- ✅ Need **specific implementation examples** (for_each, locals, etc.)
- ✅ Deciding between **alternative approaches**
- ✅ Building **complex multi-resource** configurations
- ✅ Unsure how to structure locals vs variables
- ❌ NOT needed if following existing code patterns

#### Load `references/security-standards.md` when:
- ✅ Handling **secrets, passwords, API keys, certificates**
- ✅ Creating **IAM/RBAC policies** or roles
- ✅ Setting up **network security** (security groups, firewalls, NSGs)
- ✅ User mentions **security, compliance, encryption**
- ✅ Deploying to **production** environment
- ❌ NOT needed for basic development resources

#### Load `references/anti-patterns.md` when:
- ✅ **Validating code** before presenting to user
- ✅ About to use `count` instead of `for_each`
- ✅ About to create string booleans (`"yes"/"no"`)
- ✅ User asks **"is this the right approach?"**
- ✅ Code review or quality check requested
- ❌ NOT needed during initial code generation

#### Default Loading Strategy:

```
Simple task (add resource to existing code):
  → SKILL.md only (~2k words)

Medium task (create new module/component):
  → SKILL.md + naming-conventions.md + style-guide.md (~6.3k words)

Complex task (new project with security):
  → SKILL.md + style-guide + naming + security-standards (~8.4k words)

Validation/review:
  → Add anti-patterns.md to current context (~12k words)

NEVER load all references upfront (~15k words) ❌
```

### Step 3: Generate Code

Apply these **must-have standards** automatically (from memory/SKILL.md):

#### Type Safety
- ✅ Use `bool` for true/false, never `string` with "yes"/"no"
- ✅ Use `object()` for structured data, not separate variables
- ✅ Use `number` for numeric values
- ✅ Use `map(object())` for collections of structured data

#### No Magic Numbers
- ✅ Extract ALL constants to `locals_constants.tf`
- ✅ Examples: ports, IPs, zone numbers, SKUs, timeouts
- ✅ Give descriptive names: `health_probe_port` not just `8008`

#### DRY Principle
- ✅ Use `for_each` with locals for multiple similar resources
- ✅ Extract common attributes to reusable locals
- ✅ Never duplicate resource blocks

#### Validation
- ✅ Add validation blocks to all variables with constraints
- ✅ Provide clear error messages with examples

#### Security Baseline
- ✅ Mark sensitive variables: `sensitive = true`
- ✅ Enable encryption at rest and in transit
- ✅ Follow least privilege for IAM/RBAC
- ✅ Use network segmentation

#### Code Organization
- ✅ `locals_*.tf` - Configuration as data (what to create)
- ✅ `resource_*.tf` - Implementation (how to create)
- ✅ `variables.tf` - All inputs
- ✅ `outputs.tf` - All outputs

**If uncertain about ANY pattern** → Load the relevant reference file.

### Step 4: Pre-Presentation Validation

Before showing code to user, mentally verify:

```
□ No hardcoded secrets (passwords, keys, tokens)
□ No magic numbers (all extracted to constants)
□ Proper types used (bool not string, object not primitives)
□ Validation blocks on constrained variables
□ Sensitive values marked appropriately
□ Security baseline met (encryption, least privilege)
□ Naming conventions followed
□ DRY principle applied (no duplicate blocks)
□ Documentation included (README, examples)
```

**If ANY box uncertain** → Load relevant reference to verify before presenting.

### Step 5: Generate Supporting Files

Always include:
- ✅ **README.md** - Architecture overview, quick start, troubleshooting
- ✅ **terraform.tfvars.example** - Documented example configuration
- ✅ **versions.tf** - Provider version constraints
- ✅ **.gitignore** - Exclude sensitive files (*.tfvars, .terraform/, *.tfstate)
- ✅ **CONTRIBUTING.md** (for team projects) - Development guidelines

---

## Decision Trees

### "Should I load more references?"

```
START
  ↓
Is this a NEW project?
  ├─ YES → Load style-guide.md (organization patterns)
  └─ NO → Continue
      ↓
      Am I creating NEW RESOURCES?
      ├─ YES → Load naming-conventions.md (naming rules)
      └─ NO → Continue
          ↓
          Does this involve SECURITY/IAM/NETWORKING?
          ├─ YES → Load security-standards.md
          └─ NO → Continue
              ↓
              Am I UNCERTAIN about implementation pattern?
              ├─ YES → Load terraform-patterns.md
              └─ NO → Continue
                  ↓
                  Ready to VALIDATE before presenting?
                  ├─ YES → Load anti-patterns.md
                  └─ NO → Proceed with SKILL.md only
```

### "Which pattern should I use?"

```
Multiple similar resources?
  → Use for_each with locals pattern
  → Load terraform-patterns.md if need examples

Conditional resource creation?
  → Use count = var.enabled ? 1 : 0
  → Use merge() for optional resource maps

Related configuration values?
  → Use object() type in variables
  → NOT separate primitive variables

Need to extract common attributes?
  → Create common_attributes in locals
  → Use merge(local.common, {...})
```

---

## 🚨 Red Flags (STOP and Load References)

### STOP - Load `anti-patterns.md` if about to:
- ❌ Use `count` for multiple similar resources (use `for_each`)
- ❌ Create `variable "deploy" { type = string, default = "yes" }` (use `bool`)
- ❌ Hardcode ports, IPs, SKUs, zone numbers (extract to constants)
- ❌ Make separate variables for related data (use `object()`)
- ❌ Duplicate resource blocks (use `for_each` with locals)
- ❌ Skip validation blocks on variables

### STOP - Load `security-standards.md` if dealing with:
- 🔐 Passwords, API keys, tokens, certificates
- 🔐 IAM roles, policies, permissions, RBAC
- 🔐 Security groups, firewalls, network ACLs
- 🔐 Encryption keys or data protection
- 🔐 Public internet access or exposed services
- 🔐 Production deployments

### STOP - Load `terraform-patterns.md` if uncertain about:
- ❓ How to structure locals vs variables
- ❓ When to use for_each vs count vs neither
- ❓ How to make resources conditional
- ❓ IP address allocation patterns
- ❓ Load balancer configuration patterns

---

## Usage Scenarios (Context Efficiency Examples)

### Scenario 1: "Create an S3 bucket for logs"
**Complexity**: Simple
**Context needs**: Naming, basic security

**Load**:
- SKILL.md (2k words) - workflow
- naming-conventions.md (2.2k words) - bucket naming rules
- security-standards.md (2.3k words) - encryption requirements

**Total**: ~6.5k words
**Result**: Efficient, loaded only what's needed for naming + basic security

---

### Scenario 2: "Add a VM to existing infrastructure"
**Complexity**: Simple (following existing patterns)
**Context needs**: Match existing patterns

**Load**:
- SKILL.md (2k words) - workflow

**Total**: ~2k words
**Result**: Match existing code patterns, minimal loading

---

### Scenario 3: "Create VPC with subnets, security groups, NAT gateway"
**Complexity**: Medium
**Context needs**: Organization, naming, security

**Load**:
- SKILL.md (2k words)
- style-guide.md (2.1k words) - organization patterns
- naming-conventions.md (2.2k words) - resource naming
- security-standards.md (2.3k words) - network security rules

**Total**: ~8.6k words
**Result**: Comprehensive but targeted, no wasted context

---

### Scenario 4: "Build complete 3-tier application infrastructure"
**Complexity**: High
**Context needs**: Everything except anti-patterns (save for validation)

**Load**:
- SKILL.md (2k words)
- style-guide.md (2.1k words)
- terraform-patterns.md (2.7k words)
- naming-conventions.md (2.2k words)
- security-standards.md (2.3k words)

**Total**: ~11.3k words
**Validation pass**: Add anti-patterns.md (3.6k) → ~15k total

**Result**: All references relevant, loaded as needed through workflow

---

### ❌ WRONG Approach: "Create S3 bucket" → Load everything
**Loads**: All references (15k words)
**Problem**: 9k words wasted on irrelevant patterns, anti-patterns, complex examples
**Impact**: Less context for conversation, slower processing

---

## Quick Standards Reference

### Must Always Apply (No Exceptions)

**Type Safety**:
```hcl
✅ variable "enabled" { type = bool }
❌ variable "enabled" { type = string, default = "yes" }

✅ variable "subnet" { type = object({ name = string, cidr = string }) }
❌ variable "subnet_name" { type = string }
   variable "subnet_cidr" { type = string }
```

**No Magic Numbers**:
```hcl
❌ port = 8008
✅ port = local.health_probe_port  # From locals_constants.tf

locals {
  health_probe_port = 8008  # FortiGate health check service
}
```

**DRY with for_each**:
```hcl
❌ resource "azurerm_subnet" "web" { ... }
   resource "azurerm_subnet" "app" { ... }

✅ locals {
     subnets = { web = {...}, app = {...} }
   }
   resource "azurerm_subnet" "subnet" {
     for_each = local.subnets
   }
```

**Validation**:
```hcl
✅ variable "location" {
     type = string
     validation {
       condition     = contains(["eastus", "westus"], var.location)
       error_message = "Must be eastus or westus"
     }
   }
```

**Security**:
```hcl
✅ variable "admin_password" { sensitive = true }
✅ encryption_enabled = true
✅ min_tls_version = "TLS1_2"
```

---

## File Organization Pattern

```
module/
├── versions.tf              # Terraform and provider versions
├── variables.tf             # All input variables
├── outputs.tf               # All outputs (organized by category)
├── data.tf                  # Data source lookups
│
├── locals_constants.tf      # Constants and magic numbers
├── locals_common.tf         # Common reusable attributes
├── locals_network.tf        # Network resource configurations
├── locals_compute.tf        # Compute resource configurations
│
├── resource_virtual_network.tf    # VNet/VPC implementation
├── resource_subnet.tf              # Subnet implementation
├── resource_virtual_machine.tf    # VM/Instance implementation
│
├── terraform.tfvars.example # Example configuration
├── .gitignore               # Exclude sensitive files
└── README.md                # Documentation
```

---

## Scripts

### Initialize New Project
```bash
python scripts/init_project.py \
  --name my-infrastructure \
  --tool terraform \
  --cloud azure \
  --template standard
```

Creates:
- Standard directory structure
- Template files from `assets/templates/`
- README with project-specific content
- Git repository with pre-commit hooks
- Example configuration files

### Validate Code Quality
```bash
python scripts/validate_structure.py \
  --path ./terraform \
  --strict \
  --report validation-report.md
```

Checks:
- No magic numbers
- Naming convention compliance
- Required documentation
- Security standards
- Anti-patterns absent

**Exit codes**: 0 (pass), 1 (fail), 2 (error)

---

## Integration with Existing Projects

When adding to existing codebase:

1. **Read existing patterns first** - Match their style
2. **Load style-guide.md** only if patterns are unclear
3. **Match naming conventions** from existing code
4. **Apply standards incrementally** - Don't force immediate refactor
5. **Document deviations** if existing code uses different patterns

---

## Common Questions

### "How do I know which references to load?"

Follow the decision tree above. Start with SKILL.md only, load references when:
- Starting new project → style-guide.md
- Creating resources → naming-conventions.md
- Need implementation examples → terraform-patterns.md
- Security-related → security-standards.md
- Validation time → anti-patterns.md

### "Can I load multiple references at once?"

Yes! For complex tasks, load multiple relevant references. Example:
- New secure application → style-guide + naming + security-standards
- But still NOT all references unnecessarily

### "What if I load the wrong reference?"

No problem. If you realize mid-task you need a different reference, load it then. Progressive disclosure means loading AS NEEDED, not all upfront.

---

## Success Criteria

Code generated with this skill should:
- ✅ Pass validation script without errors
- ✅ Require zero or minimal remediation
- ✅ Follow organizational patterns consistently
- ✅ Be production-ready and secure by default
- ✅ Include comprehensive documentation
- ✅ Use context efficiently (load only what's needed)

---

**Remember**:
- **SKILL.md** = Navigation (when to load what)
- **References** = Comprehensive details (loaded as needed)
- **Progressive disclosure** = Context efficiency = Better results

Load references conditionally, not preemptively.
