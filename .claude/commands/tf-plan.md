# Terraform Plan with Review

Run terraform plan and provide a detailed review of changes.

## Arguments
- `$ARGUMENTS` - Additional terraform plan options (e.g., "-var-file=prod.tfvars")

## Instructions

1. Ensure working directory has Terraform code
2. Run terraform plan:
```bash
terraform plan -out=tfplan $ARGUMENTS
```

3. Analyze the plan output and provide:
   - Summary of resources to be created/modified/destroyed
   - Security implications of changes
   - Cost impact estimates (if infracost available)
   - Potential issues or concerns
   - Recommendations before apply

4. If the plan shows destructive changes, highlight them prominently and confirm user awareness.
