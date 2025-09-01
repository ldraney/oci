#!/usr/bin/env python3
"""
Vanilla Oracle MCP Server
Simple, direct OCI control via MCP
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

# MCP imports
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from pydantic import AnyUrl

# OCI imports
try:
    import oci
    HAS_OCI = True
except ImportError:
    HAS_OCI = False
    print("Warning: OCI SDK not installed. Install with: pip install oci")


class VanillaOracleMCP:
    """MCP server for Oracle Cloud Infrastructure operations"""
    
    def __init__(self):
        self.server = Server("vanilla-oracle")
        self.config = None
        self.compute_client = None
        self.network_client = None
        self.setup_handlers()
    
    def setup_handlers(self):
        """Set up MCP handlers"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available OCI tools"""
            return [
                Tool(
                    name="oci_instance_launch",
                    description="Launch a new OCI compute instance",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Instance name"},
                            "shape": {"type": "string", "description": "Instance shape (e.g., VM.Standard.A1.Flex)"},
                            "ocpus": {"type": "number", "description": "Number of OCPUs", "default": 1},
                            "memory_gb": {"type": "number", "description": "Memory in GB", "default": 6},
                            "image_os": {"type": "string", "description": "OS type", "default": "Canonical Ubuntu"},
                            "image_version": {"type": "string", "description": "OS version", "default": "22.04"},
                            "ssh_key_path": {"type": "string", "description": "Path to SSH public key", "default": "~/.ssh/id_rsa.pub"}
                        },
                        "required": ["name"]
                    }
                ),
                Tool(
                    name="oci_instance_list",
                    description="List all OCI compute instances",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "state": {"type": "string", "description": "Filter by state (RUNNING, STOPPED, etc.)"}
                        }
                    }
                ),
                Tool(
                    name="oci_instance_terminate",
                    description="Terminate an OCI compute instance",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "instance_id": {"type": "string", "description": "Instance OCID to terminate"}
                        },
                        "required": ["instance_id"]
                    }
                ),
                Tool(
                    name="oci_instance_get",
                    description="Get details of a specific OCI instance",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "instance_id": {"type": "string", "description": "Instance OCID"}
                        },
                        "required": ["instance_id"]
                    }
                ),
                Tool(
                    name="oci_network_list",
                    description="List VCNs and subnets",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="oci_config_check",
                    description="Check OCI configuration and credentials",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            
            if not HAS_OCI:
                return [TextContent(
                    type="text",
                    text="Error: OCI SDK not installed. Run: pip install oci"
                )]
            
            # Initialize OCI clients if needed
            if not self.compute_client:
                try:
                    self.initialize_oci()
                except Exception as e:
                    return [TextContent(
                        type="text",
                        text=f"Error initializing OCI: {str(e)}"
                    )]
            
            # Route to appropriate handler
            handlers = {
                "oci_instance_launch": self.launch_instance,
                "oci_instance_list": self.list_instances,
                "oci_instance_terminate": self.terminate_instance,
                "oci_instance_get": self.get_instance,
                "oci_network_list": self.list_networks,
                "oci_config_check": self.check_config
            }
            
            handler = handlers.get(name)
            if not handler:
                return [TextContent(
                    type="text",
                    text=f"Unknown tool: {name}"
                )]
            
            try:
                result = await handler(arguments)
                return [TextContent(type="text", text=result)]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error executing {name}: {str(e)}"
                )]
    
    def initialize_oci(self):
        """Initialize OCI configuration and clients"""
        # Try environment variables first
        self.config = {
            "user": os.getenv("OCI_USER_OCID"),
            "key_file": os.getenv("OCI_KEY_FILE"),
            "fingerprint": os.getenv("OCI_FINGERPRINT"),
            "tenancy": os.getenv("OCI_TENANCY_OCID"),
            "region": os.getenv("OCI_REGION", "us-phoenix-1")
        }
        
        # Check for missing config
        missing = [k for k, v in self.config.items() if not v]
        if missing:
            # Try to load from ~/.oci/config
            try:
                self.config = oci.config.from_file()
            except:
                raise ValueError(f"Missing OCI configuration: {', '.join(missing)}")
        
        # Initialize clients
        self.compute_client = oci.core.ComputeClient(self.config)
        self.network_client = oci.core.VirtualNetworkClient(self.config)
    
    async def launch_instance(self, args: Dict[str, Any]) -> str:
        """Launch a new compute instance"""
        name = args["name"]
        shape = args.get("shape", "VM.Standard.A1.Flex")
        ocpus = args.get("ocpus", 1)
        memory_gb = args.get("memory_gb", 6)
        
        compartment_id = self.config["tenancy"]
        
        # Find Ubuntu image
        images = self.compute_client.list_images(
            compartment_id=compartment_id,
            operating_system=args.get("image_os", "Canonical Ubuntu"),
            operating_system_version=args.get("image_version", "22.04"),
            shape=shape,
            sort_by="TIMECREATED",
            sort_order="DESC"
        ).data
        
        if not images:
            return "Error: No suitable image found"
        
        image_id = images[0].id
        
        # Get first AD
        ads = oci.identity.IdentityClient(self.config).list_availability_domains(
            compartment_id=compartment_id
        ).data
        ad = ads[0].name
        
        # Get subnet
        vcns = self.network_client.list_vcns(compartment_id=compartment_id).data
        if not vcns:
            return "Error: No VCN found"
        
        subnets = self.network_client.list_subnets(
            compartment_id=compartment_id,
            vcn_id=vcns[0].id
        ).data
        
        if not subnets:
            return "Error: No subnet found"
        
        # Read SSH key
        ssh_key_path = os.path.expanduser(args.get("ssh_key_path", "~/.ssh/id_rsa.pub"))
        try:
            with open(ssh_key_path, 'r') as f:
                ssh_key = f.read().strip()
        except:
            return f"Error: Cannot read SSH key from {ssh_key_path}"
        
        # Launch instance
        launch_details = oci.core.models.LaunchInstanceDetails(
            availability_domain=ad,
            compartment_id=compartment_id,
            display_name=name,
            image_id=image_id,
            shape=shape,
            shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(
                ocpus=float(ocpus),
                memory_in_gbs=float(memory_gb)
            ) if shape.endswith(".Flex") else None,
            create_vnic_details=oci.core.models.CreateVnicDetails(
                subnet_id=subnets[0].id,
                assign_public_ip=True
            ),
            metadata={
                "ssh_authorized_keys": ssh_key
            }
        )
        
        response = self.compute_client.launch_instance(launch_details)
        instance = response.data
        
        # Wait for running state
        instance = oci.wait_until(
            self.compute_client,
            self.compute_client.get_instance(instance.id),
            'lifecycle_state',
            'RUNNING',
            max_wait_seconds=300
        ).data
        
        # Get public IP
        vnic_attachments = self.compute_client.list_vnic_attachments(
            compartment_id=compartment_id,
            instance_id=instance.id
        ).data
        
        vnic = self.network_client.get_vnic(vnic_attachments[0].vnic_id).data
        
        return json.dumps({
            "status": "success",
            "instance_id": instance.id,
            "name": name,
            "public_ip": vnic.public_ip,
            "private_ip": vnic.private_ip,
            "shape": shape,
            "state": instance.lifecycle_state,
            "ssh_command": f"ssh ubuntu@{vnic.public_ip}"
        }, indent=2)
    
    async def list_instances(self, args: Dict[str, Any]) -> str:
        """List all compute instances"""
        compartment_id = self.config["tenancy"]
        state_filter = args.get("state")
        
        instances = self.compute_client.list_instances(
            compartment_id=compartment_id
        ).data
        
        if state_filter:
            instances = [i for i in instances if i.lifecycle_state == state_filter]
        
        result = []
        for instance in instances:
            # Try to get public IP
            public_ip = "N/A"
            try:
                vnic_attachments = self.compute_client.list_vnic_attachments(
                    compartment_id=compartment_id,
                    instance_id=instance.id
                ).data
                if vnic_attachments:
                    vnic = self.network_client.get_vnic(vnic_attachments[0].vnic_id).data
                    public_ip = vnic.public_ip or "N/A"
            except:
                pass
            
            result.append({
                "id": instance.id,
                "name": instance.display_name,
                "state": instance.lifecycle_state,
                "shape": instance.shape,
                "public_ip": public_ip,
                "created": instance.time_created.isoformat() if instance.time_created else "N/A"
            })
        
        return json.dumps({
            "total": len(result),
            "instances": result
        }, indent=2)
    
    async def terminate_instance(self, args: Dict[str, Any]) -> str:
        """Terminate a compute instance"""
        instance_id = args["instance_id"]
        
        # Get instance details first
        try:
            instance = self.compute_client.get_instance(instance_id).data
            name = instance.display_name
        except:
            return f"Error: Instance {instance_id} not found"
        
        # Terminate
        self.compute_client.terminate_instance(instance_id)
        
        return json.dumps({
            "status": "success",
            "message": f"Instance {name} ({instance_id}) is being terminated",
            "instance_id": instance_id,
            "previous_state": instance.lifecycle_state
        }, indent=2)
    
    async def get_instance(self, args: Dict[str, Any]) -> str:
        """Get details of a specific instance"""
        instance_id = args["instance_id"]
        
        try:
            instance = self.compute_client.get_instance(instance_id).data
        except:
            return f"Error: Instance {instance_id} not found"
        
        compartment_id = self.config["tenancy"]
        
        # Get public IP
        public_ip = "N/A"
        private_ip = "N/A"
        try:
            vnic_attachments = self.compute_client.list_vnic_attachments(
                compartment_id=compartment_id,
                instance_id=instance_id
            ).data
            if vnic_attachments:
                vnic = self.network_client.get_vnic(vnic_attachments[0].vnic_id).data
                public_ip = vnic.public_ip or "N/A"
                private_ip = vnic.private_ip or "N/A"
        except:
            pass
        
        return json.dumps({
            "id": instance.id,
            "name": instance.display_name,
            "state": instance.lifecycle_state,
            "shape": instance.shape,
            "public_ip": public_ip,
            "private_ip": private_ip,
            "availability_domain": instance.availability_domain,
            "created": instance.time_created.isoformat() if instance.time_created else "N/A",
            "region": instance.region,
            "ssh_command": f"ssh ubuntu@{public_ip}" if public_ip != "N/A" else "N/A"
        }, indent=2)
    
    async def list_networks(self, args: Dict[str, Any]) -> str:
        """List VCNs and subnets"""
        compartment_id = self.config["tenancy"]
        
        vcns = self.network_client.list_vcns(compartment_id=compartment_id).data
        
        result = []
        for vcn in vcns:
            subnets = self.network_client.list_subnets(
                compartment_id=compartment_id,
                vcn_id=vcn.id
            ).data
            
            result.append({
                "vcn_id": vcn.id,
                "vcn_name": vcn.display_name,
                "cidr_block": vcn.cidr_block,
                "state": vcn.lifecycle_state,
                "subnets": [
                    {
                        "id": subnet.id,
                        "name": subnet.display_name,
                        "cidr_block": subnet.cidr_block,
                        "availability_domain": subnet.availability_domain
                    }
                    for subnet in subnets
                ]
            })
        
        return json.dumps({
            "total_vcns": len(result),
            "networks": result
        }, indent=2)
    
    async def check_config(self, args: Dict[str, Any]) -> str:
        """Check OCI configuration"""
        result = {
            "config_source": "environment" if os.getenv("OCI_USER_OCID") else "file",
            "region": self.config.get("region", "not set"),
            "tenancy_id": self.config.get("tenancy", "not set")[:50] + "...",
            "user_id": self.config.get("user", "not set")[:50] + "...",
            "key_file": self.config.get("key_file", "not set"),
            "fingerprint": self.config.get("fingerprint", "not set")[:20] + "..." if self.config.get("fingerprint") else "not set"
        }
        
        # Test API access
        try:
            compartment_id = self.config["tenancy"]
            self.compute_client.list_instances(compartment_id=compartment_id, limit=1)
            result["api_access"] = "✅ Working"
        except Exception as e:
            result["api_access"] = f"❌ Error: {str(e)[:100]}"
        
        return json.dumps(result, indent=2)
    
    async def run(self):
        """Run the MCP server"""
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="vanilla-oracle",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )


async def main():
    """Main entry point"""
    server = VanillaOracleMCP()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())