# Initialize New Terraform Project

Initialize a new Terraform project using the terraform-builder skill.

## Arguments
- `$ARGUMENTS` - Project name and options (e.g., "my-project --cloud aws --template standard")

## Instructions

Run the project initialization script:

```bash
python .claude/skills/terraform/scripts/init_project.py --name $ARGUMENTS
```

If no arguments provided, use interactive mode to gather:
1. Project name
2. Cloud provider (aws, azure, gcp)
3. Template type (minimal, standard, enterprise)

After initialization:
1. Navigate to the new project directory
2. Copy `terraform.tfvars.example` to `terraform.tfvars`
3. Configure required variables
4. Run `terraform init`
