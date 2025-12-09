# SageMaker VPC-Only Cleanup

Clean up AWS-managed SageMaker resources before terraform destroy.

## Arguments
- `$ARGUMENTS` - AWS region (e.g., "ca-central-1")

## Instructions

SageMaker creates resources that Terraform doesn't manage. These must be deleted manually:

### Step 1: Find EFS File Systems
```bash
aws efs describe-file-systems --region $ARGUMENTS \
  --query "FileSystems[?NumberOfMountTargets>\`0\`].[FileSystemId,Name]" \
  --output table
```

### Step 2: Delete Mount Targets
```bash
# Get mount targets
aws efs describe-mount-targets --file-system-id <fs-id> --region $ARGUMENTS \
  --query "MountTargets[].MountTargetId" --output text

# Delete each mount target
aws efs delete-mount-target --mount-target-id <fsmt-id> --region $ARGUMENTS
```

### Step 3: Wait and Delete EFS
```bash
# Wait 60 seconds for mount targets to fully delete
sleep 60
aws efs delete-file-system --file-system-id <fs-id> --region $ARGUMENTS
```

### Step 4: Delete AWS-Created Security Groups
Look for security groups named:
- `security-group-for-inbound-nfs-*`
- `security-group-for-outbound-nfs-*`

Delete all rules first, then delete the security groups.

### Step 5: Terraform Destroy
```bash
terraform destroy
```

Provide interactive guidance through each step, confirming resource IDs before deletion.
