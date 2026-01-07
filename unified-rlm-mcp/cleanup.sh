#!/bin/bash
# Cleanup script - Remove all node_modules and build artifacts

echo "🧹 Cleaning up..."

# Remove node_modules
echo "Removing node_modules..."
find . -name "node_modules" -type d -exec rm -rf {} + 2>/dev/null || true

# Remove build outputs
echo "Removing build outputs..."
rm -rf dist/ build/ *.tsbuildinfo

# Remove lock files (optional - comment out if you want to keep them)
# echo "Removing lock files..."
# rm -f pnpm-lock.yaml package-lock.json yarn.lock

# Remove runtime state
echo "Removing runtime state..."
rm -rf .rlm-unified/

# Remove logs
echo "Removing logs..."
rm -f *.log

echo "✅ Cleanup complete!"
echo ""
echo "To reinstall:"
echo "  pnpm install"
echo "  pnpm build"

