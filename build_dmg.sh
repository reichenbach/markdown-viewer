#!/bin/bash
#
# build_dmg.sh — Build a distributable .dmg for Markdown Viewer
# Run from the project root: bash build_dmg.sh
#
# Produces: "Markdown Viewer 1.0.dmg" in the current directory
#

APP_NAME="Markdown Viewer"
DMG_NAME="Markdown Viewer 1.0"
VOL_NAME="Markdown Viewer"
APP_BUNDLE="Markdown Viewer.app"
STAGING_DIR=".dmg_staging"
DMG_TEMP="${DMG_NAME}_temp.dmg"
DMG_FINAL="${DMG_NAME}.dmg"

# Cleanup function for error handling
cleanup() {
    echo "Cleaning up..."
    # Unmount if still mounted
    if [ -d "/Volumes/${VOL_NAME}" ]; then
        hdiutil detach "/Volumes/${VOL_NAME}" -force 2>/dev/null || true
    fi
    rm -f "${DMG_TEMP}"
    rm -rf "${STAGING_DIR}"
}

echo "=== Building ${DMG_FINAL} ==="

# -------------------------------------------------------
# Step 0: Ensure no previous volume is mounted
# -------------------------------------------------------
if [ -d "/Volumes/${VOL_NAME}" ]; then
    echo "Ejecting previously mounted volume..."
    hdiutil detach "/Volumes/${VOL_NAME}" -force 2>/dev/null || true
    sleep 1
fi

# -------------------------------------------------------
# Step 1: Make sure the .app bundle is up to date
# -------------------------------------------------------
echo "[1/7] Syncing latest source into app bundle..."
cp -f viewer.py "${APP_BUNDLE}/Contents/Resources/viewer.py"
cp -f markdown_parser.py "${APP_BUNDLE}/Contents/Resources/markdown_parser.py"

# Make sure the launcher is executable
chmod +x "${APP_BUNDLE}/Contents/MacOS/MarkdownViewer"

# Ensure bundle bit is set
SetFile -a B "${APP_BUNDLE}"

# -------------------------------------------------------
# Step 2: Clean up any previous build artifacts
# -------------------------------------------------------
echo "[2/7] Cleaning previous build artifacts..."
rm -rf "${STAGING_DIR}"
rm -f "${DMG_TEMP}"
rm -f "${DMG_FINAL}"

# -------------------------------------------------------
# Step 3: Create staging directory with app + Applications link
# -------------------------------------------------------
echo "[3/7] Creating staging directory..."
mkdir -p "${STAGING_DIR}"

# Copy the .app bundle (preserving resource forks and metadata)
cp -pR "${APP_BUNDLE}" "${STAGING_DIR}/"

# Ensure the bundle bit is set on the copy
SetFile -a B "${STAGING_DIR}/${APP_BUNDLE}"

# Create symlink to /Applications for drag-install
ln -s /Applications "${STAGING_DIR}/Applications"

# -------------------------------------------------------
# Step 4: Create a read/write DMG from the staging dir
# -------------------------------------------------------
echo "[4/7] Creating temporary read/write DMG..."

# Calculate size needed (app size + 5MB padding)
APP_SIZE_KB=$(du -sk "${STAGING_DIR}" | awk '{print $1}')
DMG_SIZE_KB=$((APP_SIZE_KB + 5120))

hdiutil create \
    -srcfolder "${STAGING_DIR}" \
    -volname "${VOL_NAME}" \
    -fs HFS+ \
    -fsargs "-c c=64,a=16,e=16" \
    -format UDRW \
    -size ${DMG_SIZE_KB}k \
    "${DMG_TEMP}"

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create DMG"
    cleanup
    exit 1
fi

# -------------------------------------------------------
# Step 5: Mount the DMG and customize Finder appearance
# -------------------------------------------------------
echo "[5/7] Mounting DMG and setting Finder view options..."

# Mount the writable DMG
MOUNT_OUTPUT=$(hdiutil attach -readwrite -noverify -noautoopen "${DMG_TEMP}" 2>&1)
MOUNT_POINT="/Volumes/${VOL_NAME}"

if [ ! -d "${MOUNT_POINT}" ]; then
    echo "ERROR: Failed to mount DMG"
    echo "${MOUNT_OUTPUT}"
    cleanup
    exit 1
fi

echo "    Mounted at: ${MOUNT_POINT}"

# Give Finder a moment to index
sleep 2

# Use AppleScript to set the Finder window appearance
osascript <<APPLESCRIPT
tell application "Finder"
    tell disk "${VOL_NAME}"
        open
        set current view of container window to icon view
        set toolbar visible of container window to false
        set statusbar visible of container window to false
        set bounds of container window to {200, 200, 680, 460}
        set theViewOptions to the icon view options of container window
        set arrangement of theViewOptions to not arranged
        set icon size of theViewOptions to 80
        set position of item "${APP_BUNDLE}" of container window to {120, 130}
        set position of item "Applications" of container window to {360, 130}
        close
        open
        update without registering applications
        delay 2
        close
    end tell
end tell
APPLESCRIPT

# Make sure .DS_Store is flushed
sync

# -------------------------------------------------------
# Step 5b: Set custom volume icon (optional)
# -------------------------------------------------------
if [ -f "${APP_BUNDLE}/Contents/Resources/appicon.icns" ]; then
    echo "[5b/7] Setting volume icon..."
    cp "${APP_BUNDLE}/Contents/Resources/appicon.icns" "${MOUNT_POINT}/.VolumeIcon.icns" 2>/dev/null && {
        SetFile -c icnC "${MOUNT_POINT}/.VolumeIcon.icns" 2>/dev/null || true
        SetFile -a C "${MOUNT_POINT}" 2>/dev/null || true
    } || echo "    (skipped - could not write to volume)"
fi

# -------------------------------------------------------
# Step 6: Unmount
# -------------------------------------------------------
echo "[6/7] Unmounting..."
hdiutil detach "/Volumes/${VOL_NAME}" -force 2>/dev/null || true
sleep 1

# Make sure it's really gone
if [ -d "/Volumes/${VOL_NAME}" ]; then
    echo "    Retrying unmount..."
    sleep 3
    hdiutil detach "/Volumes/${VOL_NAME}" -force 2>/dev/null || true
fi

# -------------------------------------------------------
# Step 7: Convert to compressed read-only DMG
# -------------------------------------------------------
echo "[7/7] Converting to compressed read-only DMG..."
hdiutil convert \
    "${DMG_TEMP}" \
    -format UDZO \
    -imagekey zlib-level=9 \
    -o "${DMG_FINAL}"

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to convert DMG"
    cleanup
    exit 1
fi

# Clean up
rm -f "${DMG_TEMP}"
rm -rf "${STAGING_DIR}"

echo ""
echo "=== Done! ==="
FINAL_SIZE=$(du -sh "${DMG_FINAL}" | awk '{print $1}')
echo "Created: ${DMG_FINAL} (${FINAL_SIZE})"
echo ""
echo "To test: open \"${DMG_FINAL}\""