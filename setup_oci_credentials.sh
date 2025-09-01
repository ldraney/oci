#!/bin/bash

echo "==================================="
echo "OCI Credentials Setup Script"
echo "==================================="
echo ""
echo "This script will help you set up OCI credentials for API access."
echo ""

# Check current environment
echo "Current OCI environment variables:"
echo "  USER_OCID: ${OCI_USER_OCID:0:50}..."
echo "  TENANCY_OCID: ${OCI_TENANCY_OCID:0:50}..."
echo "  REGION: $OCI_REGION"
echo ""

# Create .oci directory if it doesn't exist
mkdir -p ~/.oci
chmod 700 ~/.oci

echo "Please provide the following information:"
echo ""

# Get private key
echo "1. OCI Private Key"
echo "   Paste your OCI API private key (including BEGIN/END lines):"
echo "   Press Ctrl+D when done:"
echo ""

cat > ~/.oci/oci_api_key.pem
chmod 600 ~/.oci/oci_api_key.pem

echo ""
echo "Private key saved to ~/.oci/oci_api_key.pem"
echo ""

# Get fingerprint
read -p "2. Enter your API key fingerprint (format: xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx): " fingerprint

# Add to bashrc if not already there
if ! grep -q "OCI_KEY_FILE" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# OCI API Credentials" >> ~/.bashrc
    echo "export OCI_KEY_FILE='$HOME/.oci/oci_api_key.pem'" >> ~/.bashrc
    echo "export OCI_FINGERPRINT='$fingerprint'" >> ~/.bashrc
    echo ""
    echo "Added OCI credentials to ~/.bashrc"
else
    echo "Updating existing OCI credentials in ~/.bashrc"
    sed -i '' "s|export OCI_KEY_FILE=.*|export OCI_KEY_FILE='$HOME/.oci/oci_api_key.pem'|" ~/.bashrc
    sed -i '' "s|export OCI_FINGERPRINT=.*|export OCI_FINGERPRINT='$fingerprint'|" ~/.bashrc
fi

# Source the updated bashrc
source ~/.bashrc

echo ""
echo "==================================="
echo "Setup Complete!"
echo "==================================="
echo ""
echo "Testing OCI connection..."
echo ""

# Test the connection
cd /Users/ldraney/namespaces/vanilla-oracle
poetry run python -c "
import os
import oci

config = {
    'user': os.getenv('OCI_USER_OCID'),
    'key_file': os.getenv('OCI_KEY_FILE'),
    'fingerprint': os.getenv('OCI_FINGERPRINT'),
    'tenancy': os.getenv('OCI_TENANCY_OCID'),
    'region': os.getenv('OCI_REGION', 'us-phoenix-1')
}

try:
    compute = oci.core.ComputeClient(config)
    instances = compute.list_instances(compartment_id=config['tenancy']).data
    print(f'✅ Success! Found {len(instances)} instances')
    for instance in instances:
        print(f'  - {instance.display_name}: {instance.lifecycle_state}')
except Exception as e:
    print(f'❌ Error: {str(e)}')
"

echo ""
echo "You can now use the vanilla-oracle namespace to manage OCI!"
echo ""
echo "Examples:"
echo "  cd ~/namespaces/vanilla-oracle"
echo "  poetry run python oci-control.py --list"
echo "  poetry run python oci-control.py --terminate <instance-id>"