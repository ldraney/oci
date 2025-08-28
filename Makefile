# OCI Python Vanilla - Makefile
# Direct Oracle Cloud control without frameworks

.PHONY: help launch launch-small launch-large list status terminate clean-all
.PHONY: show-network show-ips test ssh install dev

# Default target
help:
	@echo "OCI Python Vanilla - Cloud Control Commands"
	@echo ""
	@echo "Launch Operations:"
	@echo "  make launch        - Launch Ubuntu 22.04 with defaults"
	@echo "  make launch-small  - Launch minimal instance (1 OCPU, 6GB RAM)"
	@echo "  make launch-large  - Launch larger instance (2 OCPU, 16GB RAM)"
	@echo ""
	@echo "Instance Management:"
	@echo "  make list          - List all running instances"
	@echo "  make status ID=xxx - Get detailed instance status"
	@echo "  make terminate ID=xxx - Terminate specific instance"
	@echo "  make clean-all     - ⚠️  TERMINATE ALL INSTANCES"
	@echo ""
	@echo "Network Info:"
	@echo "  make show-network  - Display VCN and subnet information"
	@echo "  make show-ips      - List all public IPs"
	@echo ""
	@echo "Utilities:"
	@echo "  make ssh ID=xxx    - SSH into instance by ID"
	@echo "  make test          - Test OCI connectivity"
	@echo "  make install       - Install OCI Python SDK"
	@echo "  make dev           - Development mode (watch for changes)"

# Launch operations
launch:
	@echo "🚀 Launching Ubuntu 22.04 instance..."
	@python3 oci.py

launch-small:
	@echo "🚀 Launching small Ubuntu instance (1 OCPU, 6GB)..."
	@python3 oci.py --shape VM.Standard.A1.Flex --ocpus 1 --memory 6

launch-large:
	@echo "🚀 Launching large Ubuntu instance (2 OCPU, 16GB)..."
	@python3 oci.py --shape VM.Standard.A1.Flex --ocpus 2 --memory 16

# Instance management
list:
	@echo "📋 Listing all instances..."
	@python3 oci.py --list

status:
ifndef ID
	@echo "❌ Usage: make status ID=<instance-ocid>"
else
	@echo "🔍 Getting status for $(ID)..."
	@python3 oci.py --status $(ID)
endif

terminate:
ifndef ID
	@echo "❌ Usage: make terminate ID=<instance-ocid>"
else
	@echo "⚠️  Terminating instance $(ID)..."
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] && python3 oci.py --terminate $(ID)
endif

clean-all:
	@echo "⚠️  WARNING: This will terminate ALL instances!"
	@read -p "Type 'destroy all' to confirm: " confirm && \
	[ "$$confirm" = "destroy all" ] && python3 oci.py --terminate-all || echo "Cancelled"

# Network information
show-network:
	@echo "🌐 Network Configuration:"
	@python3 -c "exec(open('oci.py').read()); import asyncio; asyncio.run(show_network_info())"

show-ips:
	@echo "🌍 Public IPs:"
	@python3 oci.py --list | grep -E "(Public IP:|ubuntu@)" || echo "No instances with public IPs"

# SSH helper
ssh:
ifndef ID
	@echo "❌ Usage: make ssh ID=<instance-ocid>"
else
	@echo "🔐 Connecting to instance $(ID)..."
	@IP=$$(python3 oci.py --status $(ID) | grep "Public IP:" | cut -d: -f2 | xargs) && \
	[ -n "$$IP" ] && ssh ubuntu@$$IP || echo "Could not get IP for instance"
endif

# Testing and setup
test:
	@echo "🧪 Testing OCI connectivity..."
	@python3 -c "import oci; print('✅ OCI SDK installed')" || echo "❌ OCI SDK not found"
	@python3 -c "import os; assert os.getenv('OCI_USER_OCID'), 'OCI_USER_OCID not set'" && echo "✅ OCI_USER_OCID set" || echo "❌ OCI_USER_OCID not set"
	@python3 -c "import os; assert os.getenv('OCI_FINGERPRINT'), 'OCI_FINGERPRINT not set'" && echo "✅ OCI_FINGERPRINT set" || echo "❌ OCI_FINGERPRINT not set"
	@python3 -c "import os; assert os.getenv('OCI_TENANCY_OCID'), 'OCI_TENANCY_OCID not set'" && echo "✅ OCI_TENANCY_OCID set" || echo "❌ OCI_TENANCY_OCID not set"
	@python3 -c "import os; assert os.getenv('OCI_KEY_FILE'), 'OCI_KEY_FILE not set'" && echo "✅ OCI_KEY_FILE set" || echo "❌ OCI_KEY_FILE not set"
	@python3 -c "import os; assert os.path.exists(os.path.expanduser(os.getenv('OCI_KEY_FILE', ''))), 'Key file not found'" && echo "✅ Key file exists" || echo "❌ Key file not found"
	@echo ""
	@echo "🔌 Testing API connection..."
	@python3 oci.py --list > /dev/null 2>&1 && echo "✅ Successfully connected to OCI" || echo "❌ Failed to connect to OCI"

install:
	@echo "📦 Installing OCI Python SDK..."
	pip install oci

# Development
dev:
	@echo "👀 Watching for changes (Ctrl+C to stop)..."
	@while true; do \
		clear; \
		make test; \
		echo ""; \
		make list; \
		sleep 5; \
	done

# Git operations
commit:
	@git add -A && git commit -m "🚀 OCI Python Vanilla - Direct cloud control"

push:
	@git push origin main || echo "Run 'make setup-remote' first"

setup-remote:
	@echo "Setting up GitHub remote..."
	@git remote add origin https://github.com/ldraney/oci-python-vanilla.git 2>/dev/null || true
	@git push -u origin main

.DEFAULT_GOAL := help