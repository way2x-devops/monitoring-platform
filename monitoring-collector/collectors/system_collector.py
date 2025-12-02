#!/usr/bin/env python3
import os
import time
import subprocess
import socket
from datetime import datetime
import psycopg2
from psycopg2 import sql

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'postgres_db',
    'user': 'app_user',
    'password': 'app_pass',
    'port': 5432
}

# Пути к хостовым файлам
HOST_PREFIX = "/host"

def get_db_connection():
    """Create and return database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def create_tables():
    """Create necessary tables if they don't exist"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            # Memory info table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS memory_info (
                    id SERIAL PRIMARY KEY,
                    hostname VARCHAR(100),
                    timestamp TIMESTAMP,
                    total_memory VARCHAR(50),
                    used_memory VARCHAR(50),
                    free_memory VARCHAR(50),
                    shared_memory VARCHAR(50),
                    buffer_cache VARCHAR(50),
                    available_memory VARCHAR(50),
                    swap_total VARCHAR(50),
                    swap_used VARCHAR(50),
                    swap_free VARCHAR(50)
                )
            """)
            
            # CPU info table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS cpu_info (
                    id SERIAL PRIMARY KEY,
                    hostname VARCHAR(100),
                    timestamp TIMESTAMP,
                    load_average VARCHAR(100),
                    tasks_total INTEGER,
                    tasks_running INTEGER,
                    tasks_sleeping INTEGER,
                    tasks_stopped INTEGER,
                    tasks_zombie INTEGER,
                    cpu_us VARCHAR(10),
                    cpu_sy VARCHAR(10),
                    cpu_ni VARCHAR(10),
                    cpu_id VARCHAR(10),
                    cpu_wa VARCHAR(10),
                    cpu_hi VARCHAR(10),
                    cpu_si VARCHAR(10),
                    cpu_st VARCHAR(10)
                )
            """)
            
            # Disk info table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS disk_info (
                    id SERIAL PRIMARY KEY,
                    hostname VARCHAR(100),
                    timestamp TIMESTAMP,
                    filesystem VARCHAR(100),
                    size VARCHAR(20),
                    used VARCHAR(20),
                    available VARCHAR(20),
                    use_percent VARCHAR(10),
                    mounted_on VARCHAR(100)
                )
            """)
            
            # Process info table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS process_info (
                    id SERIAL PRIMARY KEY,
                    hostname VARCHAR(100),
                    timestamp TIMESTAMP,
                    user VARCHAR(50),
                    pid INTEGER,
                    cpu_percent FLOAT,
                    mem_percent FLOAT,
                    vsz VARCHAR(20),
                    rss VARCHAR(20),
                    tty VARCHAR(20),
                    stat VARCHAR(10),
                    start_time VARCHAR(20),
                    cpu_time VARCHAR(20),
                    command TEXT
                )
            """)
            
            # Network info table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS network_info (
                    id SERIAL PRIMARY KEY,
                    hostname VARCHAR(100),
                    timestamp TIMESTAMP,
                    interface VARCHAR(50),
                    state VARCHAR(20),
                    local_address VARCHAR(50),
                    foreign_address VARCHAR(50),
                    pid INTEGER,
                    program_name VARCHAR(100)
                )
            """)
            
            conn.commit()
            return True
    except Exception as e:
        print(f"Error creating tables: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def read_host_file(filepath):
    """Чтение файла с хоста"""
    try:
        with open(f"{HOST_PREFIX}{filepath}", 'r') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return ""

def parse_memory_info_from_host(hostname, timestamp):
    """Parse memory info from host's /proc/meminfo"""
    try:
        meminfo = read_host_file("/proc/meminfo")
        lines = meminfo.strip().split('\n')
        
        mem_data = {}
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                mem_data[key.strip()] = value.strip().split()[0]
        
        # Convert kB to MB/GB for consistency with free command
        def convert_kb(value_kb):
            kb = int(value_kb)
            if kb >= 1024*1024:
                return f"{kb/(1024*1024):.1f}G"
            elif kb >= 1024:
                return f"{kb/1024:.1f}M"
            return f"{kb}K"
        
        return {
            'hostname': hostname,
            'timestamp': timestamp,
            'total_memory': convert_kb(mem_data.get('MemTotal', '0')),
            'used_memory': convert_kb(str(int(mem_data.get('MemTotal', '0')) - int(mem_data.get('MemFree', '0')))),
            'free_memory': convert_kb(mem_data.get('MemFree', '0')),
            'shared_memory': convert_kb(mem_data.get('Shmem', '0')),
            'buffer_cache': convert_kb(mem_data.get('Buffers', '0')),
            'available_memory': convert_kb(mem_data.get('MemAvailable', '0')),
            'swap_total': convert_kb(mem_data.get('SwapTotal', '0')),
            'swap_used': convert_kb(str(int(mem_data.get('SwapTotal', '0')) - int(mem_data.get('SwapFree', '0')))),
            'swap_free': convert_kb(mem_data.get('SwapFree', '0'))
        }
    except Exception as e:
        print(f"Error parsing memory info: {e}")
        return None

def parse_cpu_info_from_host(hostname, timestamp):
    """Parse CPU info from host's /proc files"""
    try:
        # Read load average
        loadavg = read_host_file("/proc/loadavg")
        load_parts = loadavg.strip().split()
        
        # Read CPU stats
        stat = read_host_file("/proc/stat")
        lines = stat.strip().split('\n')
        
        cpu_data = {
            'hostname': hostname,
            'timestamp': timestamp,
            'load_average': f"{load_parts[0]}, {load_parts[1]}, {load_parts[2]}" if len(load_parts) >= 3 else '',
            'tasks_total': 0,
            'tasks_running': 0,
            'tasks_sleeping': 0,
            'tasks_stopped': 0,
            'tasks_zombie': 0,
            'cpu_us': '', 'cpu_sy': '', 'cpu_ni': '', 'cpu_id': '',
            'cpu_wa': '', 'cpu_hi': '', 'cpu_si': '', 'cpu_st': ''
        }
        
        # Parse process stats from /proc/stat
        for line in lines:
            if line.startswith('procs_running'):
                cpu_data['tasks_running'] = int(line.split()[1])
            elif line.startswith('procs_blocked'):
                cpu_data['tasks_sleeping'] = int(line.split()[1])
            elif line.startswith('cpu '):
                parts = line.split()
                # Calculate CPU percentages (simplified)
                total = sum(int(x) for x in parts[1:])
                if total > 0:
                    cpu_data['cpu_us'] = f"{(int(parts[1]) + int(parts[2])) * 100 / total:.1f}"
                    cpu_data['cpu_sy'] = f"{int(parts[3]) * 100 / total:.1f}"
                    cpu_data['cpu_id'] = f"{int(parts[4]) * 100 / total:.1f}"
        
        return cpu_data
    except Exception as e:
        print(f"Error parsing CPU info: {e}")
        return None

def parse_disk_info_from_host(hostname, timestamp):
    """Parse disk info using host's df command"""
    try:
        # Run df on host by using chroot
        result = subprocess.run(
            ["chroot", HOST_PREFIX, "df", "-h"],
            capture_output=True,
            text=True,
            check=True
        )
        
        lines = result.stdout.strip().split('\n')[1:]
        disks = []
        
        for line in lines:
            parts = line.split()
            if len(parts) >= 6:
                disk_data = {
                    'hostname': hostname,
                    'timestamp': timestamp,
                    'filesystem': parts[0],
                    'size': parts[1],
                    'used': parts[2],
                    'available': parts[3],
                    'use_percent': parts[4],
                    'mounted_on': parts[5]
                }
                disks.append(disk_data)
        
        return disks
    except Exception as e:
        print(f"Error parsing disk info: {e}")
        return []

def parse_process_info_from_host(hostname, timestamp):
    """Parse process info from host's /proc"""
    try:
        # Use ps через chroot
        result = subprocess.run(
            ["chroot", HOST_PREFIX, "ps", "aux", "--sort=-%cpu"],
            capture_output=True,
            text=True,
            check=True
        )
        
        lines = result.stdout.strip().split('\n')[1:6]  # Только топ-5 процессов
        processes = []
        
        for line in lines:
            parts = line.split(maxsplit=10)
            if len(parts) >= 11:
                process_data = {
                    'hostname': hostname,
                    'timestamp': timestamp,
                    'user': parts[0],
                    'pid': int(parts[1]),
                    'cpu_percent': float(parts[2]),
                    'mem_percent': float(parts[3]),
                    'vsz': parts[4],
                    'rss': parts[5],
                    'tty': parts[6],
                    'stat': parts[7],
                    'start_time': parts[8],
                    'cpu_time': parts[9],
                    'command': parts[10] if len(parts) > 10 else ''
                }
                processes.append(process_data)
        
        return processes
    except Exception as e:
        print(f"Error parsing process info: {e}")
        return []

def parse_network_info_from_host(hostname, timestamp):
    """Parse network info from host"""
    try:
        # Используем ss через chroot
        result = subprocess.run(
            ["chroot", HOST_PREFIX, "ss", "-tulpn"],
            capture_output=True,
            text=True,
            check=True
        )
        
        lines = result.stdout.strip().split('\n')[1:]
        connections = []
        
        for line in lines:
            parts = line.split()
            if len(parts) >= 5:
                network_data = {
                    'hostname': hostname,
                    'timestamp': timestamp,
                    'interface': parts[4] if len(parts) > 4 else '',
                    'state': parts[0],
                    'local_address': parts[4] if len(parts) > 4 else '',
                    'foreign_address': parts[5] if len(parts) > 5 else '',
                    'pid': 0,
                    'program_name': parts[-1] if 'users:' in line else ''
                }
                connections.append(network_data)
        
        return connections
    except Exception as e:
        print(f"Error parsing network info: {e}")
        return []

def save_to_database(data, table_name):
    """Save parsed data to database"""
    conn = get_db_connection()
    if not conn or not data:
        return False
    
    try:
        with conn.cursor() as cur:
            if isinstance(data, list):
                for item in data:
                    columns = item.keys()
                    values = [item[column] for column in columns]
                    insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                        sql.Identifier(table_name),
                        sql.SQL(', ').join(map(sql.Identifier, columns)),
                        sql.SQL(', ').join(sql.Placeholder() * len(columns))
                    )
                    cur.execute(insert_query, values)
            else:
                columns = data.keys()
                values = [data[column] for column in columns]
                insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                    sql.Identifier(table_name),
                    sql.SQL(', ').join(map(sql.Identifier, columns)),
                    sql.SQL(', ').join(sql.Placeholder() * len(columns))
                )
                cur.execute(insert_query, values)
            
            conn.commit()
            return True
    except Exception as e:
        print(f"Error saving to {table_name}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def animated_loading(text, dots=3, delay=0.5):
    """Display animated loading dots"""
    print(text, end="", flush=True)
    for _ in range(dots):
        print(".", end="", flush=True)
        time.sleep(delay)
    print(" готово")

def main():
    print("Запускаю скрипт сбора телеметрии с ХОСТА")
    time.sleep(1)
    
    # Получаем хостовое имя
    try:
        hostname_content = read_host_file("/etc/hostname")
        hostname = hostname_content.strip()
    except:
        hostname = "unknown-host"
    
    # Initialize database
    print("Инициализирую базу данных...")
    if not create_tables():
        print("Ошибка при инициализации базы данных!")
        return
    
    timestamp = datetime.now()
    
    # Collect data from HOST with loading animations
    animated_loading("Собираю данные о памяти с хоста")
    mem_data = parse_memory_info_from_host(hostname, timestamp)
    if mem_data:
        save_to_database(mem_data, "memory_info")
    
    animated_loading("Собираю данные о CPU с хоста")
    cpu_data = parse_cpu_info_from_host(hostname, timestamp)
    if cpu_data:
        save_to_database(cpu_data, "cpu_info")
    
    animated_loading("Собираю данные о дисках хоста")
    disks_data = parse_disk_info_from_host(hostname, timestamp)
    if disks_data:
        save_to_database(disks_data, "disk_info")
    
    animated_loading("Собираю данные о процессах хоста")
    proc_data = parse_process_info_from_host(hostname, timestamp)
    if proc_data:
        save_to_database(proc_data, "process_info")
    
    animated_loading("Собираю данные о сети хоста")
    net_data = parse_network_info_from_host(hostname, timestamp)
    if net_data:
        save_to_database(net_data, "network_info")
    
    print(f"Готово! Данные с хоста '{hostname}' сохранены в базу данных PostgreSQL")

if __name__ == "__main__":
    main()