# utils/mac_address.py
import uuid
import subprocess
import platform
import re

def get_mac_address():
    try:
        mac_int = uuid.getnode()
        mac_hex = format(mac_int, '012x')
        mac_address = ':'.join(mac_hex[i:i+2] for i in range(0, 12, 2)).upper()
        
        if mac_address != '00:00:00:00:00:00' and mac_address != 'FF:FF:FF:FF:FF:FF':
            return mac_address
        
        system = platform.system().lower()
        
        if system == 'windows':
            result = subprocess.run(['getmac', '/format', 'table'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'Physical Address' in line or len(line.strip()) == 17:
                        mac_match = re.search(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', line)
                        if mac_match:
                            return mac_match.group(0).upper().replace('-', ':')
        
        elif system == 'linux':
            result = subprocess.run(['cat', '/sys/class/net/*/address'], 
                                  capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if re.match(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$', line.strip()):
                        return line.strip().upper()
        
        elif system == 'darwin':  # macOS
            result = subprocess.run(['ifconfig'], capture_output=True, text=True)
            if result.returncode == 0:
                mac_match = re.search(r'ether ([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}', result.stdout)
                if mac_match:
                    return mac_match.group(0).split()[1].upper()
        
        return "Unknown-Device"
        
    except Exception as e:
        print(f"Error getting MAC address: {e}")
        return "Unknown-Device"

def format_mac_address(mac):
    """
    Ensure MAC address is in standard format XX:XX:XX:XX:XX:XX
    """
    if not mac:
        return "Unknown-Device"
    
    clean_mac = re.sub(r'[:-]', '', mac.upper())
    
    if len(clean_mac) == 12:
        return ':'.join(clean_mac[i:i+2] for i in range(0, 12, 2))
    
    return mac