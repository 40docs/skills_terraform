# Validate Terraform Code

Validate Terraform code against the skill's standards and best practices.

## Arguments
- `$ARGUMENTS` - Path to Terraform directory (defaults to current directory)

## Instructions

Run validation in two phases:

### Phase 1: Terraform Native Validation
```bash
cd ${ARGUMENTS:-.}
terraform init -backend=false
terraform validate
terraform fmt -check -recursive
```

### Phase 2: Skill Standards Validation
```bash
python .claude/skills/terraform/scripts/validate_structure.py \
  --path ${ARGUMENTS:-.} \
  --strict \
  --report validation-report.md
```

### Phase 3: Security Scanning (if checkov available)
```bash
checkov -d ${ARGUMENTS:-.} --framework terraform
```

Report findings with:
- File organization issues
- Naming convention violations
- Anti-pattern detections
- Security concerns
- Suggested fixes
