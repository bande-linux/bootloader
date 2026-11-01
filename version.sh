#!/bin/sh
cd "$(dirname "$0")"

dirbase="$(basename "$(pwd)")"

if [ -n "$UNBOOT_VERSION_TAG" ]; then
    version="$UNBOOT_VERSION_TAG"
elif [ -e ".git" ]; then
    version="$(git describe --tags --always --dirty)"
elif [ "${dirbase#unboot-}" != "${dirbase}" ]; then
    version="${dirbase#unboot-}"
    version="v${version##v}"
else
    version="unknown"
fi

echo "#define BUILD_TAG \"$version\""
