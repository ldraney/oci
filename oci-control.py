#!/usr/bin/env python3
"""
Simple OCI instance launcher - using YOUR existing infrastructure
"""

import os
import oci
import time

# Your config from environment
config = {
    "user": os.getenv("OCI_USER_OCID"),
    "key_file": os.getenv("OCI_KEY_FILE"),
    "fingerprint": os.getenv("OCI_FINGERPRINT"),
    "tenancy": os.getenv("OCI_TENANCY_OCID"),
    "region": os.getenv("OCI_REGION", "us-phoenix-1")
}

# Use root compartment (your tenancy) since that's what worked
compartment_id = config["tenancy"]  # Using tenancy as compartment

compute = oci.core.ComputeClient(config)
network = oci.core.VirtualNetworkClient(config)

def launch_ubuntu():
    """Launch Ubuntu using your existing infrastructure"""
    
    print("🚀 Launching Ubuntu 22.04 on OCI\n")
    
    # 1. Get the Ubuntu image
    print("1️⃣  Finding Ubuntu 22.04 image...")
    images = compute.list_images(
        compartment_id=compartment_id,
        operating_system="Canonical Ubuntu",
        operating_system_version="22.04",
        shape="VM.Standard.A1.Flex",  # Using ARM like your existing instances
        sort_by="TIMECREATED",
        sort_order="DESC"
    ).data
    
    if not images:
        print("   Trying x86 images...")
        images = compute.list_images(
            compartment_id=compartment_id,
            operating_system="Canonical Ubuntu", 
            operating_system_version="22.04",
            sort_by="TIMECREATED",
            sort_order="DESC"
        ).data
    
    if not images:
        print("❌ No Ubuntu images found")
        return
        
    image = images[0]
    print(f"   ✓ Found: {image.display_name}")
    
    # 2. Get existing VCN and subnet (use the first one)
    print("\n2️⃣  Using existing network...")
    vcns = network.list_vcns(compartment_id=compartment_id).data
    if not vcns:
        print("❌ No VCN found")
        return
    vcn = vcns[0]
    print(f"   ✓ VCN: {vcn.display_name}")
    
    subnets = network.list_subnets(
        compartment_id=compartment_id,
        vcn_id=vcn.id
    ).data
    if not subnets:
        print("❌ No subnet found")
        return
    subnet = subnets[0]
    print(f"   ✓ Subnet: {subnet.display_name}")
    
    # 3. Get availability domain
    identity = oci.identity.IdentityClient(config)
    ads = identity.list_availability_domains(compartment_id).data
    ad = ads[0].name
    print(f"   ✓ AD: {ad}")
    
    # 4. Read SSH key
    print("\n3️⃣  Setting up SSH...")
    ssh_key_path = os.path.expanduser("~/.ssh/id_rsa.pub")
    with open(ssh_key_path, 'r') as f:
        ssh_key = f.read().strip()
    print(f"   ✓ Using key from {ssh_key_path}")
    
    # 5. Launch the instance
    print("\n4️⃣  Launching instance...")
    
    launch_details = oci.core.models.LaunchInstanceDetails(
        availability_domain=ad,
        compartment_id=compartment_id,
        display_name="ubuntu-vanilla-test",
        image_id=image.id,
        subnet_id=subnet.id,
        shape="VM.Standard.A1.Flex",  # ARM shape like your others
        shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(
            ocpus=1.0,
            memory_in_gbs=6.0
        ),
        metadata={
            "ssh_authorized_keys": ssh_key
        },
        create_vnic_details=oci.core.models.CreateVnicDetails(
            assign_public_ip=True,
            subnet_id=subnet.id
        )
    )
    
    try:
        response = compute.launch_instance(launch_details)
        instance = response.data
        print(f"   ✓ Instance created: {instance.id}")
        
        # 6. Wait for it to run
        print("\n5️⃣  Waiting for instance to start...")
        while instance.lifecycle_state != "RUNNING":
            time.sleep(5)
            instance = compute.get_instance(instance.id).data
            print(f"   State: {instance.lifecycle_state}")
        
        # 7. Get the public IP
        print("\n6️⃣  Getting public IP...")
        vnics = compute.list_vnic_attachments(
            compartment_id=compartment_id,
            instance_id=instance.id
        ).data
        
        if vnics:
            vnic = network.get_vnic(vnics[0].vnic_id).data
            print(f"   ✓ Public IP: {vnic.public_ip}")
            
            print("\n" + "="*50)
            print("✅ SUCCESS! Ubuntu 22.04 is running!")
            print("="*50)
            print(f"\nSSH into it with:")
            print(f"  ssh ubuntu@{vnic.public_ip}")
            print(f"\nInstance ID: {instance.id}")
            print(f"\nTo terminate later:")
            print(f"  python3 oci-simple.py --terminate {instance.id}")
            
    except oci.exceptions.ServiceError as e:
        print(f"\n❌ Failed to launch: {e.message}")
        print(f"   Status: {e.status}")
        print(f"   Code: {e.code}")
        
        if e.status == 404:
            print("\n💡 Try using the root compartment (tenancy OCID)")
        elif "quota" in e.message.lower():
            print("\n💡 You may have hit quota limits for this shape")
        elif "shape" in e.message.lower():
            print("\n💡 This shape might not be available in this AD")

def terminate(instance_id):
    """Terminate an instance"""
    print(f"🗑️  Terminating {instance_id}...")
    try:
        compute.terminate_instance(instance_id)
        print("✓ Termination started")
    except Exception as e:
        print(f"❌ Failed: {e}")

def list_all():
    """List all instances"""
    print("📋 Your instances:\n")
    instances = compute.list_instances(compartment_id=compartment_id).data
    for i in instances:
        print(f"• {i.display_name}")
        print(f"  ID: {i.id}")
        print(f"  State: {i.lifecycle_state}")
        print(f"  Shape: {i.shape}")
        print()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--list":
            list_all()
        elif sys.argv[1] == "--terminate" and len(sys.argv) > 2:
            terminate(sys.argv[2])
        else:
            print("Usage: python3 oci-simple.py [--list | --terminate <id>]")
    else:
        launch_ubuntu()