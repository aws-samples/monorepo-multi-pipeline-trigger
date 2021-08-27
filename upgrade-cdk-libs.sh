pip list --outdated --format=freeze --exclude-editable | grep cdk | awk '{print $1}' | xargs -n1 pip install -U
