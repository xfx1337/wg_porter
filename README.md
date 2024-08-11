# wg_porter
wg_porter allows you to easily forward ports from Wireguard VPN network to WAN

# Practical usage
If you have a PC that doesn't have an ability to forward it's port to WAN, you can use this method: connect it to VPN network hosted on a server that has this ability and forward port from there.

# Idea
wg_porter is an utility that just configures your wg interface. No need to run wg_porter all time. wg_porter configures iptables commands to forward port from VPN network to WAN.

# Usage
1. Host WireGuard VPN Network on a server that can forward it's port to WAN
2. Connect your target PC to this VPN network.
3. Run wg_porter and setup a port forwarding

# Dependencies
1. WireGuard server with wg-quick installed
2. python package: wgconfig https://pypi.org/project/wgconfig/

#Tips
You wireguard_install.sh to simplify wireguard installation and peer(user/client) setup. https://github.com/angristan/wireguard-install
