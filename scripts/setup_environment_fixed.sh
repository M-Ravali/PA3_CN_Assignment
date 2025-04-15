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

# Clone Pantheon repository if not already done
if [ ! -d "$HOME/networks_assignment/pantheon" ]; then
  cd ~/networks_assignment
  git clone https://github.com/StanfordSNR/pantheon.git
fi

# Install MahiMahi from source
sudo apt-get install -y build-essential git debhelper autotools-dev dh-autoreconf iptables \
  protobuf-compiler libprotobuf-dev pkg-config \
  libssl-dev libxcb-present-dev libcairo2-dev \
  libpango1.0-dev iproute2 apache2-dev

# Only clone if directory doesn't exist
if [ ! -d "$HOME/networks_assignment/mahimahi" ]; then
  cd ~/networks_assignment
  git clone https://github.com/ravinet/mahimahi.git
fi

cd ~/networks_assignment/mahimahi
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

# Try to setup Pantheon dependencies
cd ~/networks_assignment/pantheon
echo "Setting up Pantheon dependencies..."
if [ -f "./tools/install_deps.sh" ]; then
  ./tools/install_deps.sh || echo "Warning: install_deps.sh failed, but continuing..."
fi

# Try to build Pantheon third-party dependencies
if [ -f "./tools/build_third_party.sh" ]; then
  ./tools/build_third_party.sh || echo "Warning: build_third_party.sh failed, but continuing..."
fi

echo "Environment setup complete! (Some errors may have occurred but the main components should be installed)"
