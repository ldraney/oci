#!/usr/bin/env python3
"""
Launch OCI staging server using your existing config
"""

import oci
import time
import json
import base64
from pathlib import Path

# Load config from ~/.oci/config
config = oci.config.from_file()

# Initialize clients
compute = oci.core.ComputeClient(config)
network = oci.core.VirtualNetworkClient(config)

# Use your tenancy as compartment (root compartment)
compartment_id = config["tenancy"]

def launch_staging_server():
    """Launch staging server on OCI"""
    
    print("🚀 Launching Staging Server on OCI\n")
    
    # 1. Get Ubuntu image for ARM (like production)
    print("1️⃣  Finding Ubuntu 22.04 image for ARM...")
    images = compute.list_images(
        compartment_id=compartment_id,
        operating_system="Canonical Ubuntu",
        operating_system_version="22.04",
        shape="VM.Standard.A1.Flex",  # ARM shape like production
        sort_by="TIMECREATED",
        sort_order="DESC"
    ).data
    
    if not images:
        print("❌ No Ubuntu 22.04 images found for E2.1.Micro")
        return None
    
    image_id = images[0].id
    print(f"   ✅ Found: {images[0].display_name}")
    
    # 2. Get existing subnet (use the one from your deployments)
    print("\n2️⃣  Finding subnet...")
    subnets = network.list_subnets(
        compartment_id=compartment_id
    ).data
    
    # Find public subnet
    public_subnet = None
    for subnet in subnets:
        if "public" in subnet.display_name.lower():
            public_subnet = subnet
            break
    
    if not public_subnet:
        public_subnet = subnets[0] if subnets else None
    
    if not public_subnet:
        print("❌ No subnet found")
        return None
    
    print(f"   ✅ Using subnet: {public_subnet.display_name}")
    
    # 3. Get SSH key - use staging_deploy key
    ssh_key_path = Path.home() / ".ssh" / "staging_deploy.pub"
    if not ssh_key_path.exists():
        print("❌ SSH key not found at ~/.ssh/staging_deploy.pub")
        print("   Key should have been created by secret-vault")
        return None
    
    ssh_key = ssh_key_path.read_text().strip()
    print("   ✅ SSH key loaded")
    
    # 4. Create cloud-init script
    cloud_init = """#!/bin/bash
# Staging Server Setup

apt-get update
apt-get install -y python3-pip git tmux supervisor curl

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install Cloudflared
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
dpkg -i cloudflared-linux-amd64.deb

# Create namespaces directory
mkdir -p /home/ubuntu/namespaces
chown ubuntu:ubuntu /home/ubuntu/namespaces

# Clone tamara and mariana
su - ubuntu -c "cd ~/namespaces && git clone https://github.com/ldraney/tamara.git"
su - ubuntu -c "cd ~/namespaces && git clone https://github.com/ldraney/mariana.git"

# Checkout staging branches
su - ubuntu -c "cd ~/namespaces/tamara && git checkout staging || git checkout -b staging origin/staging || git checkout -b staging"
su - ubuntu -c "cd ~/namespaces/mariana && git checkout staging || git checkout -b staging origin/staging || git checkout -b staging"

echo "✅ Staging setup complete!"
"""
    
    # 5. Launch instance
    print("\n3️⃣  Launching instance...")
    
    instance_details = oci.core.models.LaunchInstanceDetails(
        availability_domain=public_subnet.availability_domain,
        compartment_id=compartment_id,
        shape="VM.Standard.A1.Flex",
        display_name="staging-server",
        shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(
            ocpus=2.0,
            memory_in_gbs=12.0
        ),
        source_details=oci.core.models.InstanceSourceViaImageDetails(
            source_type="image",
            image_id=image_id
        ),
        create_vnic_details=oci.core.models.CreateVnicDetails(
            subnet_id=public_subnet.id,
            assign_public_ip=True
        ),
        metadata={
            "ssh_authorized_keys": ssh_key,
            "user_data": base64.b64encode(cloud_init.encode()).decode()
        }
    )
    
    try:
        response = compute.launch_instance(instance_details)
        instance = response.data
        print(f"   ✅ Instance launching: {instance.id}")
        
        # Wait for running state
        print("\n4️⃣  Waiting for instance to start...")
        instance = compute.get_instance(instance.id).data
        
        while instance.lifecycle_state != "RUNNING":
            time.sleep(5)
            instance = compute.get_instance(instance.id).data
            print(f"   Status: {instance.lifecycle_state}...")
        
        print("   ✅ Instance is running!")
        
        # Get public IP
        print("\n5️⃣  Getting public IP...")
        vnic_attachments = compute.list_vnic_attachments(
            compartment_id=compartment_id,
            instance_id=instance.id
        ).data
        
        if vnic_attachments:
            vnic = network.get_vnic(vnic_attachments[0].vnic_id).data
            public_ip = vnic.public_ip
            print(f"   ✅ Public IP: {public_ip}")
            
            # Save deployment info
            deployment_info = {
                "type": "staging",
                "instance_id": instance.id,
                "public_ip": public_ip,
                "shape": "VM.Standard.E2.1.Micro",
                "status": "running",
                "created_at": str(instance.time_created)
            }
            
            deployment_file = Path.home() / "namespaces" / "oci" / "staging_deployment.json"
            with open(deployment_file, "w") as f:
                json.dump(deployment_info, f, indent=2)
            
            print(f"\n✅ STAGING SERVER READY!")
            print(f"\n📋 Details:")
            print(f"   Instance ID: {instance.id}")
            print(f"   Public IP: {public_ip}")
            print(f"   SSH: ssh ubuntu@{public_ip}")
            print(f"\n📝 Next Steps:")
            print(f"1. Wait 2-3 minutes for setup to complete")
            print(f"2. SSH in: ssh ubuntu@{public_ip}")
            print(f"3. Setup staging tunnels:")
            print(f"   cd ~/namespaces/devy")
            print(f"   ./setup_staging_tunnels.sh")
            print(f"4. Update devy/deployment_config.py with IP: {public_ip}")
            
            return public_ip
        else:
            print("❌ Could not get public IP")
            return None
            
    except oci.exceptions.ServiceError as e:
        print(f"❌ Error launching instance: {e.message}")
        if "QuotaExceeded" in str(e):
            print("   You may have reached your free tier limit")
            print("   Try terminating unused instances first")
        return None

if __name__ == "__main__":
    public_ip = launch_staging_server()
    if public_ip:
        print(f"\n🎉 Success! Your staging server is at: {public_ip}")
    else:
        print("\n❌ Failed to launch staging server")