#!/bin/bash

# Update package repositories
sudo apt-get update

# Install dependencies for Pantheon
sudo apt-get install -y git python3-pip python3-dev \
  build-essential autoconf libtool pkg-config \
  libssl-dev libncurses5-dev libncursesw5-dev \
  tcpdump iperf3 nload netperf \
  python3-numpy python3-matplotlib

# Install additional Python dependencies
pip3 install pandas scipy matplotlib jupyter

# Clone Pantheon repository
cd ~/networks_assignment
git clone https://github.com/StanfordSNR/pantheon.git
cd pantheon

# Setup Pantheon dependencies
./tools/install_deps.sh

# Build Pantheon
./tools/build_third_party.sh

# Install MahiMahi
sudo apt-get install -y debhelper autotools-dev dh-autoreconf iptables \
  protobuf-compiler libprotobuf-dev pkg-config \
  libssl-dev libxcb-present-dev libcairo2-dev \
  libpango1.0-dev iproute2 apache2-dev \
  apache2-bin libapache2-mod-fastcgi apache2

cd ~/networks_assignment
git clone https://github.com/ravinet/mahimahi.git
cd mahimahi
./autogen.sh
./configure
make
sudo make install

# Add mahimahi shared libraries to path
sudo sh -c "echo '/usr/local/lib' > /etc/ld.so.conf.d/mahimahi.conf"
sudo ldconfig

# Create trace files
cd ~/networks_assignment/traces

# Create 50mbps trace
python3 -c "
import sys
for _ in range(60000):  # 60 seconds at millisecond granularity
    sys.stdout.write(str(int(50 * 1000 * 1000 / 8 / 1000)) + '\n')
" > 50mbps.trace

# Create 1mbps trace
python3 -c "
import sys
for _ in range(60000):  # 60 seconds at millisecond granularity
    sys.stdout.write(str(int(1 * 1000 * 1000 / 8 / 1000)) + '\n')
" > 1mbps.trace

echo "Environment setup complete!"
