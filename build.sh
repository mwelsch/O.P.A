#!/bin/bash
set -e

echo "=== Remote Debug Tool Build Script ==="
echo ""

CLIENT_VERSION=$(grep 'VERSION = ' client/version.py | sed "s/.*VERSION = \"\(.*\)\".*/\1/")
LINUX_VERSION=$(python3 -c "import json; print(json.load(open('server/version.json'))['linux'])")
WINDOWS_VERSION=$(python3 -c "import json; print(json.load(open('server/version.json'))['windows'])")

echo "Current versions:"
echo "  Client:   $CLIENT_VERSION"
echo "  Linux:    $LINUX_VERSION"
echo "  Windows:  $WINDOWS_VERSION"
echo ""

read -p "Update client version? (y/n): " REPLY
while [[ ! "$REPLY" =~ ^[YyNn]$ ]]; do
    read -p "Update client version? (y/n): " REPLY
done
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter new version (e.g., 1.1.0): " NEW_VERSION
    while [[ ! "$NEW_VERSION" =~ ^[vV]?[0-9]+(\.[0-9]+)*(-[a-zA-Z0-9]+)?$ ]]; do
        read -p "Enter new version (e.g., 1.1.0): " NEW_VERSION
    done

    sed -i "s/VERSION = \".*\"/VERSION = \"$NEW_VERSION\"/" client/version.py

    python3 -c "
import json
with open('server/version.json', 'r+') as f:
    data = json.load(f)
    data['linux'] = '$NEW_VERSION'
    data['windows'] = '$NEW_VERSION'
    f.seek(0)
    json.dump(data, f, indent=4)
    f.truncate()
"
    echo "Updated to version $NEW_VERSION"
else
    echo "Keeping version $CLIENT_VERSION"
fi

echo ""
echo "=== Building client ==="
docker build -t remote-debug-builder ./builder
docker run --rm -v $(pwd)/output:/output -v $(pwd)/client:/src remote-debug-builder

echo ""
echo "=== Copying binary to updates folder ==="
cp output/client-linux server/updates/

echo ""
echo "=== Done ==="
echo "Binary: output/client-linux"
echo "Also copied to: server/updates/client-linux"
