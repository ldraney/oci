# OCI Python Vanilla - Direct Oracle Cloud Control

Pure Python OCI SDK operations without frameworks or abstractions. Just raw cloud power.

## User Story

As a developer managing Oracle Cloud Infrastructure, I want to control OCI resources using simple Python scripts without complex frameworks, so that I can quickly launch, manage, and terminate cloud resources with full transparency and control.

## Acceptance Criteria

- [x] Launch Ubuntu 22.04 compute instances with one command
- [x] List all running instances across compartments  
- [x] Use existing VCN/subnet infrastructure (no complex setup)
- [x] Support both ARM (A1.Flex) and x86 shapes
- [x] Automatic SSH key configuration from ~/.ssh/id_rsa.pub
- [x] Get public IP and connection details immediately
- [x] Terminate instances by ID
- [x] Zero dependencies beyond OCI SDK
- [x] Environment-based configuration (no hardcoded secrets)
- [x] Clear error messages with actionable fixes

## Status

**Production Ready** - Successfully deployed Ubuntu 22.04 on OCI

## Quick Start

```bash
# Install OCI SDK
pip install oci

# Set environment variables (add to ~/.bashrc)
export OCI_USER_OCID="ocid1.user.oc1..xxxxx"
export OCI_FINGERPRINT="xx:xx:xx:xx:xx:xx"
export OCI_TENANCY_OCID="ocid1.tenancy.oc1..xxxxx"
export OCI_KEY_FILE="~/.oci/oci_api_key.pem"
export OCI_REGION="us-phoenix-1"

# Launch Ubuntu 22.04
python3 oci.py

# List instances
python3 oci.py --list

# Terminate instance
python3 oci.py --terminate <instance-id>
```

## Operations

### Launch Instance
```bash
make launch              # Launch Ubuntu 22.04 with defaults
make launch-small        # Launch with minimal resources (1 OCPU, 6GB)
make launch-large        # Launch with more resources (2 OCPU, 16GB)
```

### Manage Instances
```bash
make list               # Show all instances
make status ID=xxx      # Get instance details
make terminate ID=xxx   # Terminate specific instance
make clean-all         # Terminate ALL instances (careful!)
```

### Network Operations
```bash
make show-network      # Display VCN and subnet info
make show-ips         # List all public IPs
```

## Architecture

```
oci.py
├── Configuration (from environment)
├── Image Discovery (Ubuntu 22.04)
├── Network Selection (existing VCN/subnet)
├── Instance Launch (with SSH keys)
├── Status Monitoring (wait for RUNNING)
└── IP Retrieval (public access details)
```

## Features

- **Simple**: One Python file, no frameworks
- **Fast**: Launches instances in ~30 seconds
- **Flexible**: Supports all OCI shapes and images
- **Safe**: Uses existing network, no VCN creation
- **Transparent**: Clear output at every step

## Comparison with MCP Servers

| Feature | This Tool | Custom MCP | Official Oracle MCP |
|---------|-----------|------------|-------------------|
| Launch VMs | ✅ | ❌ | ❌ |
| Container Instances | ✅ | ✅ | ❌ |
| Object Storage | ✅ | ✅ | ❌ |
| Direct OCI Control | ✅ | Abstracted | Abstracted |
| Database Tools | ❌ | ❌ | ✅ |
| Pricing Info | ❌ | ❌ | ✅ |

## Environment Variables

Required:
- `OCI_USER_OCID` - Your user OCID
- `OCI_FINGERPRINT` - API key fingerprint  
- `OCI_TENANCY_OCID` - Tenancy OCID (used as compartment)
- `OCI_KEY_FILE` - Path to private key
- `OCI_REGION` - Region (default: us-phoenix-1)

## Troubleshooting

### 404 Not Authorized
- Using tenancy OCID as compartment ID
- Check IAM policies for compute access

### No Capacity
- Try different availability domain
- Use different shape (A1.Flex vs E4.Flex)

### SSH Connection Refused
- Wait 30-60 seconds after launch
- Check security list allows port 22

## License

MIT