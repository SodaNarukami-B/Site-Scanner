from urllib.parse import urlparse
from ping3 import ping
import httpx
import socket
import configparser
import os
import sys
import logging



import colorama
colorama.init()
from colorama import Fore, Style
from datetime import datetime

logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    format='%(asctime)s - %(levelname)s - %(message)s'
)

### Load configs
def load_config():
    config = configparser.ConfigParser()
    logging.info('Getting configs')
    config.read('config.cfg')
    
    defaults = {
        'Settings' : {
            'ping_timeout' : '5',
            'ports_to_scan' : '80,443,8080,8443,3000,5000,22,25,587,993,995,21,53,110,143,1433,3306,5432,27017',
            'one_port_timeout' : '2',    # If 0 then ports just will be skiped
            'save_ping_directory' : './saves/ping/',
            'save_ports_directory' : './saves/ports/',
            'save_headers_directory' : './saves/headers',
            'wordlist_directory' : './wordlist.txt',
            'dirs_directory' : './saves/directories'
        }
    }
    
    if not config.sections():
        logging.debug('Config file not found. Creating default...')
        config.read_dict(defaults)
        with open('config.cfg', 'w', encoding='utf-8') as f:
            config.write(f)
    
    return config

config = load_config()

### Loggingф



### Support functions:

# Check one port
def check_port(target, port, timeout):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        result = sock.connect_ex((target, port))
        sock.close()

        if result == 0:
            logging.info(f'Port {port} is open on {target}')
        else:
            logging.info(f'Port {port} is close on {target}')
        
        return result == 0
    except socket.error:
        logging.error(f'Failed to check {port} on {target}')
        return False

# Create directory
def create_directory(dir_path):
    try:
        os.makedirs(dir_path, exist_ok=True) 
        logging.info(f'Directory created/verified: [{dir_path}]')
        return True  
    except OSError as e:
        logging.error(f'Failed to create directory {dir_path}: {e}')
        return False 
    
    
### Main functions:

# Ping target host, returns ping
def ping_target(target, timeout):
    time = round(ping(target, timeout) * 1000, 2)
    if time:
        logging.info(f'Ping from {target}: {time}')
    else:
        logging.info(f'Ping from {target}: Host down')
    return time

# Scan ports
def scan_ports(url, ports, timeout):
    try:
        open_ports = []
        
        for port in ports:
            if check_port(url, port, timeout):
                open_ports.append(port)
        
        logging.info(f'{url} was scanned succsessfuly. Open ports: {' '.join(map(str,open_ports))}')
        return True, open_ports
    
    except socket.error as e:
        logging.error(f'Failed to scan ports:\n{open_ports}')
        return False, f'{e}'
    
# Get headers
def get_headers(target):
    try:
        
        response = httpx.get(target, timeout=10, follow_redirects=True)
        headers = response.headers
        logging.info(f'Headers from {target} colected')
        return True, headers.items()
    except httpx.RequestError as e:
        logging.error(f'Failed to collect headers from {target} - {e}')
        return False, e
    
# Scan directories
def scan_directories(target, wordlist):
    try:
        found_dirs = []
        if target[-1] == '/':
            target = target[:-1]
        for dir in wordlist:
            url = f'{target}/{dir}'
            logging.info(f'Searching {dir} on {target}')
            response = httpx.get(url, follow_redirects=False, timeout=5)
            if response.status_code == 200:
                found_dirs.append(dir)
                logging.info(f'Directory {dir} was founded on {target}')
        logging.info(f'Founded directories on {target} : ' + ', '.join(found_dirs))
        return True, found_dirs
    except httpx.RequestError as e:
        logging.error(f'{e}')
        return False, e
    
# Save data
def save_data(content, prefix, path):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f'{timestamp}_{prefix}'
        with open(f'{path}/{file_name}', 'w', encoding='utf-8') as f:
            f.write(content)
        logging.info(f'{prefix} saved to {path}/{file_name}')
        return True
    except Exception:
        logging.error(f'Filed save {prefix} to {path}/{file_name}')
        return False
    
### Interface
if __name__ == '__main__':
    try:
        # Get config settings
        
        PING_TIMEOUT = config.getint('Settings', 'ping_timeout')
        PORTS_TIMEOUT = config.getint('Settings', 'one_port_timeout')
        PORTS_TO_SCAN = [int(port) for port in config.get('Settings', 'ports_to_scan').split(',')]
        PING_DIRECTORY = config.get('Settings', 'save_ping_directory')
        PORTS_DIRECTORY = config.get('Settings', 'save_ports_directory')
        HEADERS_DIRECTORY = config.get('Settings', 'save_headers_directory')
        try:
            with open(config.get('Settings', 'wordlist_directory'), 'r') as f:
                words = [line.strip() for line in f if line.strip()]
            WORDLIST = words
        except FileNotFoundError:
            logging.warning("Wordlist file not found, using empty list")
            WORDLIST = []
        WORDLIST = words
        DIRS_DIRECTORY = config.get('Settings', 'dirs_directory')
        
        while True:
            url = input(f'{Style.BRIGHT}Url > ')
            parsed_url = urlparse(url)
            
            # Gives result:
            if parsed_url.scheme and parsed_url.netloc:
                
                # DNS check
                try:
                    socket.gethostbyname(parsed_url.netloc)
                except socket.gaierror:
                    print(f'{Style.BRIGHT}{Fore.RED}Host not found!{Style.RESET_ALL}') 
                    continue
                print(f'\n{Style.BRIGHT}{Fore.CYAN}======[ {Fore.RESET}{url}{Fore.CYAN} ]======                 {Style.RESET_ALL}{Fore.GREEN}Site-scanner v0.1 preBeta{Fore.RESET}')
                
                # Ping
                
                ping_result = ping_target(parsed_url.netloc, PING_TIMEOUT)
                
                if ping_result:
                    clean_ping = f'Ping: {ping_result}'
                    print(f'\n{Style.BRIGHT}Ping: {Style.RESET_ALL}{Fore.GREEN}{ping_result}{Fore.RESET}')
                else:
                    clean_ping = 'Ping: Host down'
                    print(f'\n{Style.BRIGHT}Ping: {Style.RESET_ALL}{Fore.YELLOW}Host down{Fore.RESET}')
                    
                # Ports

                result, open_ports = scan_ports(parsed_url.netloc, PORTS_TO_SCAN, PORTS_TIMEOUT)
                
                if result:
                    if open_ports:
                        clean_ports = 'Open ports: ' + ' '.join(map(str, open_ports))
                        print(f'\n{Style.BRIGHT}Open ports: {Style.RESET_ALL}{Fore.GREEN}' + ' '.join(map(str, open_ports)) + Fore.RESET)
                    else:
                        clean_ports = 'Open ports: No open ports'
                        print(f'\n{Style.BRIGHT}Open ports: {Style.RESET_ALL}{Fore.YELLOW}No open ports{Fore.RESET}')
                else:
                    print(f'\n{Style.BRIGHT}Open ports: {Style.RESET_ALL}{Fore.RED}Error! See main.log for more information{Fore.RESET}')
                
                # Headers
                
                result, headers = get_headers(url)
                if result:
                    print(f'{Style.BRIGHT}\nHeaders:{Style.RESET_ALL}')
                    clean_headers = 'Headers:\n'
                    for key, value in headers:
                        clean_headers += f'- {key}: {value}\n'
                        print(f'{Fore.MAGENTA}- {key}: {Fore.BLUE}{value}{Fore.RESET}')
                else:
                    clean_headers = f'Headers: {headers}'  # <- создаем переменную
                    print(f'{Fore.RED}Failed to collect headers from {url}, See main.log for more information{Fore.RESET}')
                
                # Directories
                result, directoies = scan_directories(url, WORDLIST)
                if result:
                    if directoies:
                        # Добавляем - к каждому элементу
                        dirs_formatted = '\n- '.join([''] + directoies)  # Добавляем пустой элемент для первого -
                        clean_directories = f'Founded directories: {dirs_formatted}'
                        print(f'{Style.BRIGHT}\nFounded directories: {Style.RESET_ALL}{Fore.GREEN}{dirs_formatted}{Fore.RESET}')
                    else:
                        clean_directories = 'Founded directories: not found'
                        print(f'{Style.BRIGHT}\nFounded directories: {Style.RESET_ALL}{Fore.YELLOW}not found{Fore.RESET}')
                else:
                    clean_directories = '\nFounded directories: Failed to scan directories, see main.log for more information'
                    print(f'{Style.BRIGHT}\nFounded directories: {Style.RESET_ALL}{Fore.RED}Failed to scan directories, see main.log for more information')
                        
                 
                # Saving results
                save_choise = input(f'{Style.BRIGHT}{Fore.CYAN}Save results? [Y/n] {Style.RESET_ALL}')
                if save_choise.lower() in ['y', '']:
                    create_directory(PING_DIRECTORY)
                    create_directory(PORTS_DIRECTORY)
                    create_directory(HEADERS_DIRECTORY)
                    create_directory(DIRS_DIRECTORY)
                    if save_data(clean_ping, 'Ping', PING_DIRECTORY):
                        print(f'{Fore.GREEN}Ping saved to {PING_DIRECTORY}{Fore.RESET}')
                    else:
                        print(f'{Fore.RED}Filed to save ping{Fore.RESET}')
                    
                    if save_data(clean_ports, 'Ports', PORTS_DIRECTORY):
                        print(f'{Fore.GREEN}Ports saved to {PORTS_DIRECTORY}{Fore.RESET}')
                    else:
                        print(f'{Fore.RED}Failed to save ports{Fore.RESET}')
                    
                    if save_data(clean_headers, 'Headers', HEADERS_DIRECTORY):
                        print(f'{Fore.GREEN}Headers saved to {HEADERS_DIRECTORY}{Fore.RESET}')
                    else:
                        print(f'{Fore.RED}Failed to save headers{Fore.RESET}')
                    
                    if save_data(clean_directories, 'Directories', DIRS_DIRECTORY):
                        print(f'{Fore.GREEN}Directories saved to {DIRS_DIRECTORY}{Fore.RESET}')
                    else:
                        print(f'{Fore.RED}Failed to save directories{Fore.RESET}')
                
            else:
                print(f'{Fore.RED}{Style.BRIGHT}Invalid url! Example: https://www.example.com/  or https://0.0.0.0/{Fore.RESET}{Style.RESET_ALL}')
                continue
    except KeyboardInterrupt:
        sys.exit(0)
    