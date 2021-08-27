pip list --format freeze --exclude-editable --outdated | grep cdk | awk '{print $1}'
