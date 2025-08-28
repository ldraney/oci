# Claude Context - OCI Python Vanilla

This project provides direct Oracle Cloud Infrastructure control through vanilla Python scripts. No frameworks, no abstractions, just raw OCI SDK power.

## Project Overview

**Purpose**: Launch and manage OCI compute instances with simple Python commands

**Key Files**:
- `oci.py` - Main script that handles all OCI operations
- `Makefile` - User-friendly commands for common operations
- `README.md` - User story, acceptance criteria, and documentation

## Common Tasks

### Launch an Ubuntu Server
```bash
make launch  # Creates Ubuntu 22.04 with defaults (1 OCPU, 6GB RAM)
```

### Check What's Running
```bash
make list    # Shows all instances with their IDs and IPs
```

### Connect to Instance
```bash
make ssh ID=<instance-id>  # SSH directly using instance ID
```

### Clean Up
```bash
make terminate ID=<instance-id>  # Remove specific instance
```

## How the Makefile Works

The Makefile provides a clean interface to the Python script:

1. **Launch targets** (`launch`, `launch-small`, `launch-large`)
   - Call `oci.py` with different resource configurations
   - Handle shape and size parameters

2. **Management targets** (`list`, `status`, `terminate`)
   - Wrap Python script calls with safety checks
   - Require confirmation for destructive operations

3. **Utility targets** (`test`, `ssh`, `show-ips`)
   - Test environment setup
   - Extract IPs from instance data
   - Provide SSH shortcuts

## Architecture Decisions

1. **Why Vanilla Python?**
   - MCP servers (both custom and official) can't create compute instances
   - Direct OCI SDK gives full control
   - One file, no dependencies beyond `oci` package

2. **Why Use Tenancy as Compartment?**
   - Avoids compartment permission issues
   - Simplifies configuration
   - Works with default IAM policies

3. **Network Strategy**
   - Uses existing VCN/subnet (doesn't create new ones)
   - Assumes purelabsourcing-vcn exists
   - Assigns public IPs automatically

## Testing Approach

Run `make test` to verify:
- OCI SDK installation
- Environment variables set correctly
- Key file exists
- API connectivity works

## Common Issues and Solutions

### Launch Fails with 404
- Script uses tenancy OCID as compartment
- Existing VCN/subnet must exist
- Check IAM policies allow compute operations

### No Capacity Error
- Try different shape (A1.Flex vs E4.Flex)
- Some shapes have regional limits
- ARM instances often have better availability

### SSH Connection Refused
- Wait 30-60 seconds after launch
- Security list must allow port 22
- Check instance has public IP

## Environment Requirements

Must have these in `~/.bashrc`:
```bash
export OCI_USER_OCID="ocid1.user.oc1..xxxxx"
export OCI_FINGERPRINT="xx:xx:xx:xx:xx:xx"
export OCI_TENANCY_OCID="ocid1.tenancy.oc1..xxxxx"
export OCI_KEY_FILE="~/.oci/oci_api_key.pem"
export OCI_REGION="us-phoenix-1"
```

## Extending the Script

To add new features to `oci.py`:

1. **New Shapes**: Modify the `shape` parameter in `launch_ubuntu()`
2. **Different OS**: Change `operating_system` in image search
3. **Custom Networks**: Update VCN/subnet selection logic
4. **Block Storage**: Add `attach_volume()` function using `BlockstorageClient`

## Comparison with MCP Approach

**This vanilla approach**:
- ✅ Full compute instance control
- ✅ Direct, transparent operations
- ✅ No abstraction layers
- ❌ No MCP protocol benefits

**MCP servers**:
- ✅ Good for specific tools (database, pricing)
- ✅ Protocol standardization
- ❌ Can't create compute instances
- ❌ Limited to container instances

## Quick Wins

1. Launch instance: `make launch` (30 seconds)
2. Get all IPs: `make show-ips`
3. Quick SSH: `make ssh ID=xxx`
4. Clean slate: `make clean-all` (careful!)

## Next Steps

To enhance this tool:
1. Add support for block volume attachment
2. Implement load balancer creation
3. Add DNS record management
4. Create instance templates/profiles