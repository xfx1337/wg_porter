import os, sys
import subprocess
import logging
from collections import deque
import csv

if os.geteuid() != 0:
    exit("you need to have root privileges to run this script.\nplease try again, this time using 'sudo'. exiting.")

HELP = """
wg_porter - utility that allows you to forward a port from your Wireguard VPN network's peer to WAN.

commands:
clients - list clients
forward - forward prompt
unforward - unforward prompt
ports - see opened ports
"""


def split_quote(string,quotechar='"'):
    s = csv.StringIO(string)
    C = csv.reader(s, delimiter=" ",quotechar=quotechar)
    return list(C)[0]

try:
    import wgconfig
except:
    ans = input("could not load wgconfig library. can we try to install manually? (Y/n):").lower()
    if ans == "y":
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "wgconfig"])
        except:
            logging.critical("could not install wgconfig library. install it manually please. https://pypi.org/project/wgconfig/")
            sys.exit()
    else:
        print("so install it manually please. https://pypi.org/project/wgconfig/")
        sys.exit(0)

class Wireguard:
    def __init__(self, wg_conf):
        self.conf_path = wg_conf

    def get_clients(self):
        cfg = wgconfig.WGConfig(self.conf_path)
        cfg.read_file()
        clients = cfg.get_peers(keys_only=False)
        for i in range(len(clients.keys())):
            client = list(clients.keys())[i]
            clients[client]["name"] = self.get_client_name(clients[client]["PublicKey"]).replace("\n", "")
        
        return clients

    def get_client_name(self, pub_key):
        #some shit
        last_lines = deque(maxlen=2)
        name = "N/A"
        with open(self.conf_path, "r") as f:
            for line in f:
                if line.endswith(f'{pub_key}\n'): # Your real condition here
                    name = last_lines[0]
                last_lines.append(line)
        return name

    def unforward_port(self, port):
        str1 = f"PreUp = iptables -t nat -A PREROUTING -p tcp --dport {port} --jump DNAT --to-destination"
        str2 = f"PreUp = iptables -t nat -A PREROUTING -p udp --dport {port} --jump DNAT --to-destination"

        lines = []
        with open(self.conf_path, "r") as f:
            for line in f:
                if str1 not in line and str2 not in line:
                    lines.append(line)
        with open(self.conf_path, "w") as f:
            for line in lines:
                f.write(line)
                       
    def forward(self, ip, lan_port, wan_port, protocol):
        str1 = f"PreUp = iptables -t nat -A PREROUTING -p {protocol} --dport {wan_port} --jump DNAT --to-destination {ip}:{lan_port}\n"
        lines = []
        st = False
        with open(self.conf_path, "r") as f:
            for line in f:
                lines.append(line)
                if "PreUp = iptables -t nat -A PREROUTING" in line and not st:
                    lines.append(str1)
                    st = True
        if not st:
            lines.append(str1)
        with open(self.conf_path, "w") as f:
            for line in lines:
                f.write(line)

    def get_ports(self):
        search = "PreUp = iptables -t nat -A PREROUTING"
        ports = []
        with open(self.conf_path, "r") as f:
            for line in f:
                if line.startswith(search):
                    ports.append(line.replace("\n", ""))
        ports_real = []
        for p in ports:
            port = {"protocol": "N/A", "wan_port": "N/A", "ip": "N/A", "lan_port": "N/A"}
            args = split_quote(p)
            if "-p" in args:
                port["protocol"] = args[args.index("-p")+1]
            if "--dport" in args:
                port["wan_port"] = args[args.index("--dport")+1]
            if "--to-destination" in args:
                ip_full = args[args.index("--to-destination")+1]
                ip = ip_full.split(":")[0]
                port_ = ip_full.split(":")[1]
                port["ip"] = ip
                port["lan_port"] = port_
            ports_real.append(port)
        
        return ports_real


def get_confs():
    files = [f for f in os.listdir("/etc/wireguard/")]
    return files

def get_config():
    logging.info("searching for wg conf")
    try:
        wg_confs = get_confs()
    except:
        wg_confs = []
        logging.error("could not get confs. enter it manually")

    print("available configs:")
    for i in range(len(wg_confs)):
        file = wg_confs[i]
        wg_confs[i] = os.path.join("/etc/wireguard/", wg_confs[i])
        print(f"[{i}] {file}")
    idx = input("enter id or full path to your wg configuration file: ")
    try: 
        idx = int(idx)
        wg_conf = wg_confs[idx]
    except:
        wg_conf = idx
    
    return wg_conf

def print_clients():
    clients = wg.get_clients()
    print("all peers(clients):")
    for i in range(len(clients.keys())):
        client = clients[list(clients.keys())[i]]
        client_name = client["name"]
        ipv4 = "N/A"
        ipv6 = "N/A"
        try:
            ipv4 = client["AllowedIPs"][0]
            ipv6 = client["AllowedIPs"][1]
        except:
            pass
        print(f"[{i}] {client_name} - {ipv4} - {ipv6}")

def print_ports():
    ports = wg.get_ports()
    print("opened ports:")
    for p in ports:
        ip = p["ip"]
        lan_port = p["lan_port"]
        wan_port = p["wan_port"]
        protocol = p["protocol"]
        print(f"{ip} {lan_port} --> {wan_port} {protocol}")

def unforward_port_seq():
    port = input("enter wan port that you wont to unforward: ")
    wg.unforward_port(port)
    print("configuration changed. please reload wg-server")

def forward_port_seq():
    ip = input("enter in-vpn ip address of the peer whose port you want to forward: ")
    lan_port = input("enter it's port: ")
    wan_port = input("enter wan port: ")
    protocol = input("enter protocol(tcp/udp): ")
    wg.forward(ip, lan_port, wan_port, protocol)
    print("configuration changed. please reload wg-server")

print("wg_porter")
wg_conf = get_config()
try:
    with open(wg_conf, "r") as f:
        f.readlines()
except:
    logging.critical("wg_conf is not readable! exiting")
    sys.exit(-1)


wg = Wireguard(wg_conf)
print("\n")
print_clients()

print(HELP)

while True:
    try:
        cmd = input(">>> ")
    except KeyboardInterrupt:
        print("exiting")
        sys.exit()
    
    if cmd == "clients":
        print_clients()
    elif cmd == "ports":
        print_ports()
    elif cmd == "help":
        print(HELP)
    elif cmd == "unforward":
        unforward_port_seq()
    elif cmd == "forward":
        forward_port_seq()
    elif cmd == "exit":
        sys.exit()
    else:
        print("invalid syntax. help - check manual")
