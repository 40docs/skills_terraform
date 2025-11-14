#!/usr/bin/env python3
"""
IaC Structure Validation Script

Validates Infrastructure as Code against organizational standards:
- No magic numbers
- Naming convention compliance
- Required documentation present
- Security standards met
- Anti-patterns absent

Exit codes:
  0 = All checks passed
  1 = Validation failures found
  2 = Invalid arguments or script error
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import json

class ValidationResult:
    def __init__(self, check_name: str, passed: bool, message: str, file_path: str = "", line_number: int = 0):
        self.check_name = check_name
        self.passed = passed
        self.message = message
        self.file_path = file_path
        self.line_number = line_number

    def __repr__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        location = f" [{self.file_path}:{self.line_number}]" if self.file_path else ""
        return f"{status}: {self.check_name}{location}\n  {self.message}"

class IaCValidator:
    def __init__(self, path: Path, strict: bool = False):
        self.path = path
        self.strict = strict
        self.results: List[ValidationResult] = []
        self.tf_files: List[Path] = []

    def run_all_checks(self) -> bool:
        """Run all validation checks. Returns True if all passed."""
        print(f"🔍 Validating IaC structure at: {self.path}\n")

        # Discover Terraform files
        self.tf_files = list(self.path.glob("**/*.tf"))
        if not self.tf_files:
            self.results.append(ValidationResult(
                "File Discovery",
                False,
                f"No Terraform files found in {self.path}"
            ))
            return False

        print(f"Found {len(self.tf_files)} Terraform files\n")

        # Run checks
        self.check_file_structure()
        self.check_magic_numbers()
        self.check_string_booleans()
        self.check_naming_conventions()
        self.check_documentation()
        self.check_security_standards()
        self.check_variable_validation()
        self.check_output_organization()

        # Calculate results
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed

        print(f"\n{'='*80}")
        print(f"VALIDATION SUMMARY")
        print(f"{'='*80}")
        print(f"Total checks: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"{'='*80}\n")

        # Print failures
        if failed > 0:
            print("FAILURES:\n")
            for result in self.results:
                if not result.passed:
                    print(result)
                    print()

        return failed == 0

    def check_file_structure(self):
        """Check for required files and organization."""
        required_files = {
            "README.md": "Project documentation",
            "variables.tf": "Variable declarations",
            "outputs.tf": "Output definitions",
            "versions.tf": "Provider versions (or provider.tf)",
            ".gitignore": "Git exclusions"
        }

        for filename, description in required_files.items():
            file_exists = (self.path / filename).exists()

            # Allow provider.tf as alternative to versions.tf
            if filename == "versions.tf" and not file_exists:
                file_exists = (self.path / "provider.tf").exists()

            self.results.append(ValidationResult(
                f"Required File: {filename}",
                file_exists,
                f"{description} {'found' if file_exists else 'MISSING'}"
            ))

        # Check for locals_constants.tf
        constants_file = (self.path / "locals_constants.tf").exists()
        self.results.append(ValidationResult(
            "Constants File",
            constants_file,
            "locals_constants.tf found" if constants_file else "locals_constants.tf MISSING - magic numbers may be present"
        ))

    def check_magic_numbers(self):
        """Check for magic numbers in code."""
        # Known magic numbers to look for
        magic_patterns = [
            (r'\bport\s*=\s*(\d+)', "Port number"),
            (r'\bzone\s*=\s*"(\d+)"', "Availability zone"),
            (r'168\.63\.129\.16', "Azure Wire Server IP"),
            (r'\bdisk_size_gb\s*=\s*(\d+)', "Disk size"),
        ]

        constants_file = self.path / "locals_constants.tf"
        has_constants_file = constants_file.exists()

        for tf_file in self.tf_files:
            # Skip constants file itself
            if tf_file.name == "locals_constants.tf":
                continue

            content = tf_file.read_text()
            lines = content.split('\n')

            for i, line in enumerate(lines, 1):
                # Skip comments
                if line.strip().startswith('#'):
                    continue

                for pattern, description in magic_patterns:
                    matches = re.finditer(pattern, line)
                    for match in matches:
                        # Check if it's referencing a local constant
                        if 'local.' in line:
                            continue

                        self.results.append(ValidationResult(
                            "Magic Number",
                            False,
                            f"{description} hardcoded: {match.group()} - Should be in locals_constants.tf",
                            str(tf_file.relative_to(self.path)),
                            i
                        ))

    def check_string_booleans(self):
        """Check for string boolean anti-pattern."""
        for tf_file in self.tf_files:
            content = tf_file.read_text()
            lines = content.split('\n')

            for i, line in enumerate(lines, 1):
                # Look for validation with "yes"/"no" pattern
                if re.search(r'contains\(\s*\[\s*"yes"\s*,\s*"no"\s*\]', line):
                    self.results.append(ValidationResult(
                        "String Boolean",
                        False,
                        'String boolean detected - Use type = bool instead of "yes"/"no"',
                        str(tf_file.relative_to(self.path)),
                        i
                    ))

                # Look for string type with boolean-like validation
                if re.search(r'contains\(\s*\[\s*"true"\s*,\s*"false"\s*\]', line):
                    self.results.append(ValidationResult(
                        "String Boolean",
                        False,
                        'String boolean detected - Use type = bool instead of "true"/"false" strings',
                        str(tf_file.relative_to(self.path)),
                        i
                    ))

    def check_naming_conventions(self):
        """Check naming conventions compliance."""
        # Check variable names (should be snake_case)
        for tf_file in self.tf_files:
            if tf_file.name != "variables.tf":
                continue

            content = tf_file.read_text()

            # Find variable blocks
            var_pattern = r'variable\s+"([^"]+)"'
            variables = re.findall(var_pattern, content)

            for var_name in variables:
                # Check for camelCase or PascalCase
                if re.search(r'[A-Z]', var_name):
                    self.results.append(ValidationResult(
                        "Variable Naming",
                        False,
                        f'Variable "{var_name}" not in snake_case',
                        str(tf_file.relative_to(self.path))
                    ))

                # Check for single letter or too short
                if len(var_name) < 3:
                    self.results.append(ValidationResult(
                        "Variable Naming",
                        False,
                        f'Variable "{var_name}" too short (< 3 chars)',
                        str(tf_file.relative_to(self.path))
                    ))

        # Check resource names
        for tf_file in self.tf_files:
            content = tf_file.read_text()

            # Find resource blocks
            resource_pattern = r'resource\s+"[^"]+"\s+"([^"]+)"'
            resources = re.findall(resource_pattern, content)

            for res_name in resources:
                # Check for camelCase or PascalCase
                if re.search(r'[A-Z]', res_name):
                    self.results.append(ValidationResult(
                        "Resource Naming",
                        False,
                        f'Resource "{res_name}" not in snake_case',
                        str(tf_file.relative_to(self.path))
                    ))

    def check_documentation(self):
        """Check documentation quality."""
        readme = self.path / "README.md"

        if not readme.exists():
            self.results.append(ValidationResult(
                "README.md",
                False,
                "README.md not found"
            ))
            return

        content = readme.read_text().lower()

        # Check for required sections
        required_sections = [
            ("prerequisites", "Prerequisites section"),
            ("quick start", "Quick Start or Getting Started section"),
            ("configuration", "Configuration section"),
        ]

        for keyword, description in required_sections:
            found = keyword in content
            self.results.append(ValidationResult(
                f"README: {description}",
                found,
                f"{description} {'found' if found else 'MISSING in README.md'}"
            ))

        # Check for terraform.tfvars.example
        example_file = self.path / "terraform.tfvars.example"
        self.results.append(ValidationResult(
            "Example Configuration",
            example_file.exists(),
            "terraform.tfvars.example " + ("found" if example_file.exists() else "MISSING")
        ))

    def check_security_standards(self):
        """Check security standards compliance."""
        for tf_file in self.tf_files:
            content = tf_file.read_text()
            lines = content.split('\n')

            for i, line in enumerate(lines, 1):
                # Check for hardcoded secrets
                if re.search(r'(password|secret|key)\s*=\s*"[^$]', line, re.IGNORECASE):
                    # Exclude var.password references
                    if not re.search(r'var\.|data\.', line):
                        self.results.append(ValidationResult(
                            "Hardcoded Secret",
                            False,
                            "Possible hardcoded secret detected - Use variables or Key Vault",
                            str(tf_file.relative_to(self.path)),
                            i
                        ))

                # Check for overly permissive security rules
                if 'source_address_prefix' in line and '"*"' in line:
                    if 'allow' in content[max(0, content.find(line) - 200):content.find(line)].lower():
                        self.results.append(ValidationResult(
                            "Overly Permissive Security Rule",
                            False,
                            "Security rule allows traffic from anywhere (*) - Use specific CIDR blocks",
                            str(tf_file.relative_to(self.path)),
                            i
                        ))

        # Check for sensitive flag on sensitive variables
        variables_file = self.path / "variables.tf"
        if variables_file.exists():
            content = variables_file.read_text()

            # Find password/secret variables
            sensitive_vars = re.findall(r'variable\s+"([^"]*(?:password|secret|key)[^"]*)".*?}', content, re.DOTALL | re.IGNORECASE)

            for var_name in sensitive_vars:
                # Check if marked sensitive
                var_block_match = re.search(rf'variable\s+"{var_name}".*?}}', content, re.DOTALL)
                if var_block_match:
                    var_block = var_block_match.group()
                    has_sensitive = 'sensitive' in var_block and 'true' in var_block

                    self.results.append(ValidationResult(
                        "Sensitive Variable",
                        has_sensitive,
                        f'Variable "{var_name}" {"is" if has_sensitive else "NOT"} marked sensitive'
                    ))

    def check_variable_validation(self):
        """Check that variables have validation rules."""
        variables_file = self.path / "variables.tf"

        if not variables_file.exists():
            return

        content = variables_file.read_text()

        # Find all variable blocks
        var_blocks = re.findall(r'variable\s+"([^"]+)".*?}', content, re.DOTALL)

        for var_name in var_blocks:
            # Get the variable block
            var_match = re.search(rf'variable\s+"{var_name}".*?}}', content, re.DOTALL)
            if var_match:
                var_block = var_match.group()

                # Skip if has default = ... (some defaults don't need validation)
                has_validation = 'validation' in var_block
                has_default = re.search(r'default\s*=', var_block)

                # Required variables (no default) should have validation
                if not has_default and not has_validation:
                    self.results.append(ValidationResult(
                        "Variable Validation",
                        False,
                        f'Required variable "{var_name}" lacks validation block',
                        "variables.tf"
                    ))

    def check_output_organization(self):
        """Check that outputs are organized in dedicated file."""
        outputs_file = self.path / "outputs.tf"

        # Check if outputs.tf exists
        if not outputs_file.exists():
            self.results.append(ValidationResult(
                "Output Organization",
                False,
                "outputs.tf not found - outputs may be scattered"
            ))
            return

        # Check for outputs in other files
        for tf_file in self.tf_files:
            if tf_file.name == "outputs.tf":
                continue

            content = tf_file.read_text()
            if re.search(r'^\s*output\s+"', content, re.MULTILINE):
                self.results.append(ValidationResult(
                    "Output Organization",
                    False,
                    f"Output found in {tf_file.name} - should be in outputs.tf",
                    str(tf_file.relative_to(self.path))
                ))

    def generate_report(self, report_path: Path):
        """Generate markdown report of validation results."""
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)

        report = f"""# IaC Validation Report

**Path**: {self.path}
**Date**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

- **Total Checks**: {len(self.results)}
- **Passed**: {passed} ✅
- **Failed**: {failed} ❌
- **Pass Rate**: {(passed / len(self.results) * 100):.1f}%

## Results

"""

        # Group by check type
        by_type = {}
        for result in self.results:
            check_type = result.check_name.split(':')[0]
            if check_type not in by_type:
                by_type[check_type] = []
            by_type[check_type].append(result)

        for check_type, results in sorted(by_type.items()):
            report += f"\n### {check_type}\n\n"
            for result in results:
                status = "✅" if result.passed else "❌"
                location = f" `{result.file_path}:{result.line_number}`" if result.file_path else ""
                report += f"{status} **{result.check_name}**{location}  \n{result.message}\n\n"

        report_path.write_text(report)
        print(f"📄 Report saved to: {report_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Validate IaC structure against organizational standards"
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=Path("."),
        help="Path to Terraform code (default: current directory)"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict mode (all warnings become failures)"
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Generate markdown report at specified path"
    )

    args = parser.parse_args()

    # Validate path exists
    if not args.path.exists():
        print(f"❌ Error: Path does not exist: {args.path}", file=sys.stderr)
        return 2

    # Run validation
    validator = IaCValidator(args.path, args.strict)

    try:
        all_passed = validator.run_all_checks()

        # Generate report if requested
        if args.report:
            validator.generate_report(args.report)

        return 0 if all_passed else 1

    except Exception as e:
        print(f"❌ Validation error: {e}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())
