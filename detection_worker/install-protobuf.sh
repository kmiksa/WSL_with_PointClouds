#!/bin/bash

cd /tmp

# Make sure you grab the latest version
curl -OL https://github.com/google/protobuf/releases/download/v3.7.0/protoc-3.7.0-linux-x86_64.zip

# Unzip
unzip protoc-3.7.0-linux-x86_64.zip -d protoc3

# Move protoc to /usr/local/bin/
mv protoc3/bin/* /usr/local/bin/

# Move protoc3/include to /usr/local/include/
mv protoc3/include/* /usr/local/include/


cd -
