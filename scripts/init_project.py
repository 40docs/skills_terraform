#!/usr/bin/env python3
"""
IaC Project Initialization Script

Creates a new Infrastructure as Code project with:
- Standard directory structure
- Template files
- Git repository with pre-commit hooks
- README with project-specific content
- Example configuration files

Usage:
    python init_project.py --name my-infrastructure --tool terraform --cloud azure
"""

import argparse
import sys
from pathlib import Path
from typing import Dict
import subprocess
import shutil

TEMPLATES_DIR = Path(__file__).parent.parent / "assets" / "templates"

class ProjectInitializer:
    def __init__(self, name: str, tool: str, cloud: str, template: str, output_dir: Path):
        self.name = name
        self.tool = tool
        self.cloud = cloud
        self.template = template
        self.output_dir = output_dir / name
        self.tool_dir = self.output_dir / tool

    def create_project(self) -> bool:
        """Create complete project structure."""
        try:
            print(f"🚀 Creating IaC project: {self.name}")
            print(f"   Tool: {self.tool}")
            print(f"   Cloud: {self.cloud}")
            print(f"   Template: {self.template}")
            print(f"   Location: {self.output_dir}\n")

            # Create directory structure
            self._create_directories()

            # Copy template files
            self._copy_templates()

            # Generate project files
            self._generate_readme()
            self._generate_gitignore()
            self._generate_contributing()

            # Initialize git
            self._init_git()

            # Setup pre-commit hooks
            self._setup_pre_commit_hooks()

            print(f"\n✅ Project created successfully at: {self.output_dir}")
            print(f"\nNext steps:")
            print(f"  1. cd {self.output_dir}")
            print(f"  2. Edit {self.tool}/terraform.tfvars (copy from .example)")
            print(f"  3. cd {self.tool} && terraform init")
            print(f"  4. Review and customize README.md")

            return True

        except Exception as e:
            print(f"❌ Error creating project: {e}", file=sys.stderr)
            return False

    def _create_directories(self):
        """Create project directory structure."""
        print("📁 Creating directory structure...")

        directories = [
            self.output_dir,
            self.tool_dir,
            self.tool_dir / "cloud-init",
            self.output_dir / "docs",
            self.output_dir / ".github" / "workflows",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"   Created: {directory.relative_to(self.output_dir.parent)}")

    def _copy_templates(self):
        """Copy template files from assets."""
        print("\n📄 Copying template files...")

        template_source = TEMPLATES_DIR / self.tool

        if not template_source.exists():
            print(f"   ⚠️  No templates found for {self.tool}, creating basic structure")
            self._create_basic_templates()
            return

        # Copy all template files
        for template_file in template_source.glob("**/*.template"):
            # Determine destination (remove .template extension)
            rel_path = template_file.relative_to(template_source)
            dest_file = self.tool_dir / str(rel_path).replace('.template', '')

            # Read template and substitute variables
            content = template_file.read_text()
            content = self._substitute_variables(content)

            # Write to destination
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            dest_file.write_text(content)

            print(f"   Created: {dest_file.relative_to(self.output_dir)}")

    def _substitute_variables(self, content: str) -> str:
        """Substitute template variables."""
        replacements = {
            '{{PROJECT_NAME}}': self.name,
            '{{CLOUD_PROVIDER}}': self.cloud,
            '{{CLOUD_PROVIDER_UPPER}}': self.cloud.upper(),
        }

        for key, value in replacements.items():
            content = content.replace(key, value)

        return content

    def _create_basic_templates(self):
        """Create basic template files when no templates exist."""
        # versions.tf
        versions_content = """terraform {
  required_version = ">= 1.5"

  required_providers {
    # Add your providers here
  }
}
"""
        (self.tool_dir / "versions.tf").write_text(versions_content)

        # variables.tf
        variables_content = f"""#####################################################################
# Project: {self.name}
# Required Variables
#####################################################################

variable "deployment_prefix" {{
  description = "Naming prefix for all deployed resources"
  type        = string

  validation {{
    condition     = can(regex("^[a-z0-9]{{3,10}}$", var.deployment_prefix))
    error_message = "deployment_prefix must be 3-10 lowercase alphanumeric characters"
  }}
}}

variable "location" {{
  description = "Cloud region for deployment"
  type        = string
}}

variable "environment" {{
  description = "Environment name (dev, staging, prod)"
  type        = string

  validation {{
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod"
  }}
}}

variable "tags" {{
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {{}}
}}
"""
        (self.tool_dir / "variables.tf").write_text(variables_content)

        # outputs.tf
        outputs_content = f"""###############################################################################
# Project: {self.name}
# Outputs
###############################################################################

# Add your outputs here
"""
        (self.tool_dir / "outputs.tf").write_text(outputs_content)

        # terraform.tfvars.example
        tfvars_example_content = f"""###############################################################################
# {self.name} - Example Configuration
###############################################################################

# Required Variables
deployment_prefix = "myapp"
location          = "eastus"  # Adjust for your cloud provider
environment       = "dev"

# Tags
tags = {{
  project     = "{self.name}"
  managed_by  = "terraform"
  environment = "dev"
}}
"""
        (self.tool_dir / "terraform.tfvars.example").write_text(tfvars_example_content)

        print("   Created basic Terraform files")

    def _generate_readme(self):
        """Generate project README."""
        print("\n📝 Generating README.md...")

        readme_content = f"""# {self.name}

Infrastructure as Code for {self.name} on {self.cloud.upper()}.

## 📋 Overview

<!-- TODO: Add project description -->

## 🏗️ Architecture

<!-- TODO: Add architecture diagram or description -->

## 📦 Prerequisites

- Terraform >= 1.5
- {self.cloud.upper()} account with appropriate permissions
- {self.cloud.upper()} CLI authenticated

## 🚀 Quick Start

1. **Configure variables**:
   ```bash
   cd {self.tool}
   cp terraform.tfvars.example terraform.tfvars
   vim terraform.tfvars  # Edit with your values
   ```

2. **Initialize Terraform**:
   ```bash
   terraform init
   ```

3. **Review planned changes**:
   ```bash
   terraform plan
   ```

4. **Deploy infrastructure**:
   ```bash
   terraform apply
   ```

## ⚙️ Configuration

See `{self.tool}/terraform.tfvars.example` for all available configuration options.

### Required Variables

- `deployment_prefix` - Unique prefix for resource names
- `location` - Cloud region for deployment
- `environment` - Environment name (dev, staging, prod)

### Optional Variables

<!-- TODO: Document optional variables -->

## 🔧 Common Operations

### View Outputs

```bash
cd {self.tool}
terraform output
```

### Update Infrastructure

```bash
cd {self.tool}
terraform plan
terraform apply
```

### Destroy Infrastructure

```bash
cd {self.tool}
terraform destroy
```

## 📚 Documentation

- [Architecture Decisions](docs/architecture.md) <!-- TODO: Create -->
- [Operational Runbooks](docs/runbooks.md) <!-- TODO: Create -->
- [Troubleshooting Guide](docs/troubleshooting.md) <!-- TODO: Create -->

## 🔐 Security

- All sensitive variables marked with `sensitive = true`
- Secrets stored in Key Vault / Secrets Manager
- Network segmentation enforced
- Encryption at rest and in transit enabled

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## 📞 Support

<!-- TODO: Add support contact information -->

## 📄 License

<!-- TODO: Add license information -->
"""

        (self.output_dir / "README.md").write_text(readme_content)
        print(f"   Created: README.md")

    def _generate_gitignore(self):
        """Generate .gitignore file."""
        print("\n🚫 Generating .gitignore...")

        gitignore_content = """# Terraform files
*.tfstate
*.tfstate.*
*.tfvars
!*.tfvars.example
.terraform/
.terraform.lock.hcl
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
*.log

# OS files
.DS_Store
Thumbs.db

# IDE files
.vscode/
.idea/
*.swp
*.swo
*~

# Backup files
*.bak
*.backup
"""

        (self.output_dir / ".gitignore").write_text(gitignore_content)
        print(f"   Created: .gitignore")

    def _generate_contributing(self):
        """Generate CONTRIBUTING.md file."""
        print("\n👥 Generating CONTRIBUTING.md...")

        contributing_content = f"""# Contributing to {self.name}

## Development Workflow

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Follow the coding standards below
   - Add tests for new functionality
   - Update documentation

3. **Validate your changes**:
   ```bash
   cd {self.tool}
   terraform fmt -recursive
   terraform validate
   python ../scripts/validate_structure.py --path .
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: description of your changes"
   ```

5. **Push and create pull request**:
   ```bash
   git push origin feature/your-feature-name
   ```

## Coding Standards

### File Organization

- `locals_*.tf` - Configuration as data
- `resource_*.tf` - Resource implementations
- `variables.tf` - All input variables
- `outputs.tf` - All outputs

### Naming Conventions

- Variables: `snake_case`
- Resources: `snake_case`
- Files: `snake_case.tf`
- Azure resources: `kebab-case`

### Best Practices

- ✅ Use native `bool` type for booleans
- ✅ Use `object()` for structured data
- ✅ Extract magic numbers to `locals_constants.tf`
- ✅ Use `for_each`, not `count`
- ✅ Add validation to all variables
- ✅ Mark sensitive variables appropriately
- ✅ Document all variables and outputs

### Security Requirements

- ❌ No hardcoded secrets
- ❌ No overly permissive security rules
- ✅ Encryption at rest and in transit
- ✅ Least privilege access
- ✅ Network segmentation

## Testing

### Local Testing

```bash
# Format code
terraform fmt -recursive

# Validate syntax
terraform validate

# Run structure validation
python scripts/validate_structure.py --path {self.tool}

# Security scan (if tfsec installed)
tfsec {self.tool}
```

### Before Committing

Run pre-commit hooks:
```bash
git add .
.git/hooks/pre-commit
```

## Pull Request Process

1. Ensure all tests pass
2. Update README.md with any changes
3. Update terraform.tfvars.example if variables changed
4. Request review from team members
5. Address review feedback
6. Squash commits before merging

## Commit Message Format

Use conventional commits:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Test changes
- `chore:` - Build/tooling changes

Example: `feat: add autoscaling configuration for web tier`

## Questions?

<!-- TODO: Add contact information for questions -->
"""

        (self.output_dir / "CONTRIBUTING.md").write_text(contributing_content)
        print(f"   Created: CONTRIBUTING.md")

    def _init_git(self):
        """Initialize git repository."""
        print("\n📦 Initializing git repository...")

        try:
            subprocess.run(
                ["git", "init"],
                cwd=self.output_dir,
                check=True,
                capture_output=True
            )
            print("   Git repository initialized")

            # Initial commit
            subprocess.run(
                ["git", "add", "."],
                cwd=self.output_dir,
                check=True,
                capture_output=True
            )

            subprocess.run(
                ["git", "commit", "-m", "Initial commit: IaC project structure"],
                cwd=self.output_dir,
                check=True,
                capture_output=True
            )
            print("   Initial commit created")

        except subprocess.CalledProcessError as e:
            print(f"   ⚠️  Warning: Could not initialize git: {e}")
        except FileNotFoundError:
            print("   ⚠️  Warning: git not found in PATH")

    def _setup_pre_commit_hooks(self):
        """Setup pre-commit hooks."""
        print("\n🪝 Setting up pre-commit hooks...")

        hooks_dir = self.output_dir / ".git" / "hooks"

        if not hooks_dir.exists():
            print("   ⚠️  Git hooks directory not found, skipping")
            return

        pre_commit_script = """#!/bin/bash
# Pre-commit hook for IaC validation

echo "🔍 Running pre-commit checks..."

# Check if terraform files changed
TF_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\\.tf$')

if [ -n "$TF_FILES" ]; then
    echo "📝 Terraform files changed, running validation..."

    # Format check
    echo "  Checking format..."
    terraform fmt -check -recursive terraform/ || {
        echo "❌ Terraform formatting check failed"
        echo "   Run: terraform fmt -recursive terraform/"
        exit 1
    }

    # Validate
    echo "  Validating syntax..."
    cd terraform && terraform validate || {
        echo "❌ Terraform validation failed"
        exit 1
    }
    cd ..

    # Run structure validation if script exists
    if [ -f "scripts/validate_structure.py" ]; then
        echo "  Checking structure..."
        python3 scripts/validate_structure.py --path terraform/ || {
            echo "❌ Structure validation failed"
            exit 1
        }
    fi
fi

echo "✅ Pre-commit checks passed"
exit 0
"""

        pre_commit_path = hooks_dir / "pre-commit"
        pre_commit_path.write_text(pre_commit_script)
        pre_commit_path.chmod(0o755)

        print("   Pre-commit hook installed")

def main():
    parser = argparse.ArgumentParser(
        description="Initialize a new IaC project with standard structure"
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Project name"
    )
    parser.add_argument(
        "--tool",
        default="terraform",
        choices=["terraform", "pulumi", "cloudformation"],
        help="IaC tool to use (default: terraform)"
    )
    parser.add_argument(
        "--cloud",
        default="azure",
        choices=["azure", "aws", "gcp"],
        help="Cloud provider (default: azure)"
    )
    parser.add_argument(
        "--template",
        default="standard",
        choices=["standard", "minimal", "enterprise"],
        help="Project template (default: standard)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("."),
        help="Output directory (default: current directory)"
    )

    args = parser.parse_args()

    # Validate name
    if not args.name.replace('-', '').replace('_', '').isalnum():
        print("❌ Error: Project name must be alphanumeric (hyphens and underscores allowed)", file=sys.stderr)
        return 2

    # Check if directory exists
    project_dir = args.output_dir / args.name
    if project_dir.exists():
        print(f"❌ Error: Directory already exists: {project_dir}", file=sys.stderr)
        return 2

    # Create project
    initializer = ProjectInitializer(
        args.name,
        args.tool,
        args.cloud,
        args.template,
        args.output_dir
    )

    success = initializer.create_project()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
