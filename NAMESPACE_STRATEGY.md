# OCI Instance Strategy for Namespaces

## My Recommendation: **Selective Deployment** 🎯

### Why NOT give everyone their own server:

1. **Cost**: Even with free tier, you'll hit limits (2 VMs max for ARM free tier)
2. **Management overhead**: More instances = more to maintain, patch, monitor
3. **Waste**: Most namespaces probably don't need 24/7 compute
4. **Complexity**: Network segmentation, security groups, SSH key management multiplies

### Smart Approach: **Hub and Spoke Model**

```
┌─────────────────────────────────────────┐
│        OCI Infrastructure Hub           │
│         (oci-python-vanilla)            │
└────────────┬────────────────────────────┘
             │
    ┌────────┴────────┬─────────┬────────┐
    │                 │         │        │
┌───▼───┐      ┌─────▼────┐  ┌─▼──┐  ┌──▼──┐
│ PROD  │      │   DEV    │  │TEST│  │TEMP │
│Servers│      │  Shared  │  │ VM │  │ VMs │
└───┬───┘      └────┬─────┘  └────┘  └─────┘
    │               │
┌───▼───────┐  ┌────▼──────────────────────┐
│  tamara   │  │ mariana, annabelle, karri │
│lab-manager│  │    (shared dev box)       │
└───────────┘  └───────────────────────────┘
```

## Instance Allocation Plan

### ✅ **NEEDS Dedicated Instance:**

#### 1. **tamara** (ALREADY HAS ONE)
- Has `tamara-deployment-server` running
- Production AI manufacturing app
- Customer-facing, needs isolation
- **Action**: Keep existing

#### 2. **lab-manager** 
- Central lab operations system
- Critical business function
- Needs reliability and isolation
- **Action**: Launch dedicated instance when ready

### ❌ **DOESN'T Need Dedicated Instance:**

#### 3. **mariana**
- No clear production workload yet
- Can deploy to shared dev instance
- **Action**: Use shared development server

#### 4. **annabelle**
- No README, unclear purpose
- Start with shared resources
- **Action**: Evaluate after requirements clear

#### 5. **karri**
- No README, unclear purpose
- Start with shared resources
- **Action**: Evaluate after requirements clear

## Recommended Architecture

```bash
# Production Instances (Always On)
tamara-deployment-server     # Existing - AI manufacturing
lab-manager-server           # New - Lab operations

# Development Instance (Shared)
dev-shared-server           # New - For mariana, annabelle, karri

# Utility/Temp Instances (On-Demand)
ubuntu-vanilla-test         # Existing - Can terminate when not testing
```

## Implementation Commands

```bash
# Launch dedicated lab-manager instance
make launch NAME=lab-manager SHAPE=VM.Standard.A1.Flex MEMORY=8 OCPUS=2

# Launch shared dev instance  
make launch NAME=dev-shared SHAPE=VM.Standard.A1.Flex MEMORY=6 OCPUS=1

# Tag instances for namespace ownership
# (Would need to extend the script to support tags)
```

## Cost Analysis

Current free tier limits (OCI):
- 2 AMD VMs or 4 ARM Ampere A1 cores with 24 GB RAM total
- Split across all instances

Current usage:
- 4 ARM instances × 1 OCPU × 6GB = Already at/over free tier

**Recommendation**: 
- Terminate `ubuntu-vanilla-test` to free resources
- Consolidate the 2 `purelabsourcing-ubuntu-arm64` instances
- This frees up resources for `lab-manager` when needed

## Decision: **It's Overkill** ❌

**Why**: 
- You're already at free tier limits
- Most namespaces don't have clear compute needs
- Shared development server covers 80% of use cases
- Can always spin up on-demand with your vanilla tool

**Better approach**:
1. Keep tamara's dedicated server (production)
2. Create ONE shared dev server for experiments
3. Use your `oci-python-vanilla` tool to spin up temporary instances as needed
4. Only create dedicated instances when namespace has production workload

Want me to help consolidate your current instances to free up resources?