pip list --exclude-editable --outdated | grep cdk | awk '{print $1}'
