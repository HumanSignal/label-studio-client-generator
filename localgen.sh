#!/bin/bash

# Label Studio SDK Client Generator Script
# Generates Python SDK from OpenAPI spec and copies extension files

set -euo pipefail

# Color codes for console output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if docker container is running
check_container() {
    log_info "Checking if label-studio-enterprise-app-1 container is running..."
    if ! docker ps --format "table {{.Names}}" | grep -q "label-studio-enterprise-app-1"; then
        log_error "Container label-studio-enterprise-app-1 is not running"
        log_info "Please start the container with: docker-compose up -d"
        exit 1
    fi
    log_success "Container is running"
}

# Function to generate OpenAPI spec
generate_openapi() {
    log_info "Generating OpenAPI specification..."
    if ! docker exec label-studio-enterprise-app-1 bash -c "cd label_studio_enterprise && python manage.py spectacular" > fern/openapi/openapi.yaml; then
        log_error "Failed to generate OpenAPI spec"
        exit 1
    fi
    log_success "OpenAPI spec generated successfully"
}

# Function to display git diff for OpenAPI spec
show_openapi_diff() {
    log_info "Showing changes to OpenAPI specification..."
    if git diff --name-only | grep -q "fern/openapi/openapi.yaml"; then
        log_info "Changes detected in openapi.yaml:"
        git --no-pager diff fern/openapi/openapi.yaml
    else
        log_info "No changes detected in openapi.yaml"
    fi
}

# Function to validate OpenAPI spec
validate_spec() {
    log_info "Validating OpenAPI specification with fern check..."
    if ! fern check; then
        log_error "OpenAPI spec validation failed"
        exit 1
    fi
    log_success "OpenAPI spec validation passed"
}
# Function to cleanup local directory
cleanup_local_dir() {
    log_info "Checking for existing label_studio_sdk directory..."
    
    if [[ -d "label_studio_sdk" ]]; then
        log_warning "Found existing label_studio_sdk directory that may conflict with generation"
        
        echo
        read -p "Do you want to remove the existing label_studio_sdk directory before proceeding? (y/N): " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "Cleaning up existing label_studio_sdk directory..."
            if rm -rf "label_studio_sdk"; then
                log_success "Removed: label_studio_sdk/"
            else
                log_error "Failed to remove label_studio_sdk directory"
                exit 1
            fi
            log_success "Cleanup completed"
        else
            log_warning "Skipping cleanup - existing directory may cause conflicts"
        fi
    else
        log_info "No cleanup needed - label_studio_sdk directory does not exist"
    fi
}


# Function to generate SDK
generate_sdk() {
    cleanup_local_dir
    log_info "Generating Python SDK with fern..."
    if ! fern generate --group python-sdk-local; then
        log_error "SDK generation failed"
        exit 1
    fi
    log_success "SDK generated successfully"
}

# Function to copy extension files
copy_extensions() {
    log_info "Copying extension files from label-studio-sdk..."
    
    local sdk_src="../label-studio-sdk/src/label_studio_sdk"
    local sdk_dest="./label_studio_sdk"
    
    # Check if source directory exists
    if [[ ! -d "$sdk_src" ]]; then
        log_error "Source SDK directory not found: $sdk_src"
        log_info "Please ensure label-studio-sdk is at the same level as this generator directory:"
        log_info "Expected directory structure:"
        log_info "  parent/"
        log_info "  ├── label-studio-client-generator/  (this script location)"
        log_info "  │   └── localgen.sh"
        log_info "  └── label-studio-sdk/               (source for extension files)"
        log_info "      └── src/label_studio_sdk/"
        log_info ""
        log_info "The label-studio-sdk directory contains extension files needed for the complete SDK"
        exit 1
    fi
    
    # Array of files/directories to copy with their destination paths
    local files_to_copy=(
        "_extensions/:_extensions/"
        "_legacy/:_legacy/"
        "client.py:client.py"
        "tasks/client_ext.py:tasks/client_ext.py"
        "projects/client_ext.py:projects/client_ext.py"
        "label_interface/:label_interface/"
        "projects/exports/client_ext.py:projects/exports/client_ext.py"
        "tokens/client_ext.py:tokens/client_ext.py"
        "core/client_wrapper.py:core/client_wrapper.py"
        "data_manager.py:data_manager.py"
    )
    
    for file_mapping in "${files_to_copy[@]}"; do
        local src_file="${file_mapping%%:*}"
        local dest_file="${file_mapping##*:}"
        local full_src="$sdk_src/$src_file"
        local full_dest="$sdk_dest/$dest_file"
        
        if [[ -e "$full_src" ]]; then
            # Create destination directory if it doesn't exist
            mkdir -p "$(dirname "$full_dest")"
            
            if cp -r "$full_src" "$full_dest"; then
                log_success "Copied: $src_file"
            else
                log_error "Failed to copy: $src_file"
                exit 1
            fi
        else
            log_warning "Source file not found: $full_src"
        fi
    done
    
    log_success "All extension files copied successfully"
}

# Main execution
main() {
    log_info "Starting Label Studio SDK generation process..."
    
    check_container
    generate_openapi
    validate_spec
    show_openapi_diff
    generate_sdk
    copy_extensions
    
    log_success "SDK generation completed successfully!"
    log_info "Generated SDK is available in: ./label_studio_sdk/"
    
    log_info "Testing generated SDK..."
    
    # Test import
    if python -c "from label_studio_sdk import LabelStudio" 2>/dev/null; then
        log_success "SDK import test passed"
    else
        log_error "SDK import test failed"
        exit 1
    fi
    
    log_info "SDK is ready to use!"
    log_info "To use the generated SDK:"
    log_info "  1. Create a Python script from the current directory"
    log_info "  2. Import with: from label_studio_sdk import LabelStudio"
    echo ""
    echo "┌─────────────────────────────────────────────────────────────┐"
    echo "│  Try it now:                                                │"
    echo "│  python -c \"from label_studio_sdk import LabelStudio\"     │"
    echo "└─────────────────────────────────────────────────────────────┘"
    echo ""
}

# Error handler
error_handler() {
    log_error "Script failed on line $1"
    exit 1
}

# Set error trap
trap 'error_handler $LINENO' ERR

# Run main function
main "$@"