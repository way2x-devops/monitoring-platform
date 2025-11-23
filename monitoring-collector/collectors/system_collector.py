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

def parse_memory_info(output, hostname, timestamp):
    """Parse memory info from free command output"""
    lines = output.strip().split('\n')
    if len(lines) < 2:
        return None
    
    # Parse memory line
    mem_parts = lines[1].split()
    # Parse swap line
    swap_parts = lines[2].split()
    
    return {
        'hostname': hostname,
        'timestamp': timestamp,
        'total_memory': mem_parts[1] if len(mem_parts) > 1 else '',
        'used_memory': mem_parts[2] if len(mem_parts) > 2 else '',
        'free_memory': mem_parts[3] if len(mem_parts) > 3 else '',
        'shared_memory': mem_parts[4] if len(mem_parts) > 4 else '',
        'buffer_cache': mem_parts[5] if len(mem_parts) > 5 else '',
        'available_memory': mem_parts[6] if len(mem_parts) > 6 else '',
        'swap_total': swap_parts[1] if len(swap_parts) > 1 else '',
        'swap_used': swap_parts[2] if len(swap_parts) > 2 else '',
        'swap_free': swap_parts[3] if len(swap_parts) > 3 else ''
    }

def parse_cpu_info(output, hostname, timestamp):
    """Parse CPU info from top command output"""
    lines = output.strip().split('\n')
    if len(lines) < 4:
        return None
    
    cpu_data = {
        'hostname': hostname,
        'timestamp': timestamp,
        'load_average': '',
        'tasks_total': 0,
        'tasks_running': 0,
        'tasks_sleeping': 0,
        'tasks_stopped': 0,
        'tasks_zombie': 0,
        'cpu_us': '', 'cpu_sy': '', 'cpu_ni': '', 'cpu_id': '',
        'cpu_wa': '', 'cpu_hi': '', 'cpu_si': '', 'cpu_st': ''
    }
    
    # Parse load average (first line)
    if 'load average:' in lines[0]:
        load_part = lines[0].split('load average:')[1].strip()
        cpu_data['load_average'] = load_part
    
    # Parse tasks (second line)
    if 'tasks:' in lines[1]:
        tasks_part = lines[1].split('tasks:')[1].strip()
        tasks_parts = tasks_part.split(',')
        for part in tasks_parts:
            if 'total' in part:
                cpu_data['tasks_total'] = int(part.split()[0])
            elif 'running' in part:
                cpu_data['tasks_running'] = int(part.split()[0])
            elif 'sleeping' in part:
                cpu_data['tasks_sleeping'] = int(part.split()[0])
            elif 'stopped' in part:
                cpu_data['tasks_stopped'] = int(part.split()[0])
            elif 'zombie' in part:
                cpu_data['tasks_zombie'] = int(part.split()[0])
    
    # Parse CPU percentages (third line)
    if '%Cpu(s):' in lines[2]:
        cpu_part = lines[2].split('%Cpu(s):')[1].strip()
        cpu_parts = cpu_part.split(',')
        for part in cpu_parts:
            if 'us' in part:
                cpu_data['cpu_us'] = part.split()[0]
            elif 'sy' in part:
                cpu_data['cpu_sy'] = part.split()[0]
            elif 'ni' in part:
                cpu_data['cpu_ni'] = part.split()[0]
            elif 'id' in part:
                cpu_data['cpu_id'] = part.split()[0]
            elif 'wa' in part:
                cpu_data['cpu_wa'] = part.split()[0]
            elif 'hi' in part:
                cpu_data['cpu_hi'] = part.split()[0]
            elif 'si' in part:
                cpu_data['cpu_si'] = part.split()[0]
            elif 'st' in part:
                cpu_data['cpu_st'] = part.split()[0]
    
    return cpu_data

def parse_disk_info(output, hostname, timestamp):
    """Parse disk info from df command output"""
    lines = output.strip().split('\n')[1:]  # Skip header
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

def parse_process_info(output, hostname, timestamp):
    """Parse process info from ps command output"""
    lines = output.strip().split('\n')[1:]  # Skip header
    processes = []
    
    for line in lines:
        parts = line.split(maxsplit=10)  # Limit splits to preserve command
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

def parse_network_info(output, hostname, timestamp):
    """Parse network info from ss command output"""
    lines = output.strip().split('\n')[1:]  # Skip header
    connections = []
    
    for line in lines:
        parts = line.split()
        if len(parts) >= 6:
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

def run_command(command):
    """Execute shell command and return output"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error executing command: {e}"

def animated_loading(text, dots=3, delay=0.5):
    """Display animated loading dots"""
    print(text, end="", flush=True)
    for _ in range(dots):
        print(".", end="", flush=True)
        time.sleep(delay)
    print(" готово")

def main():
    print("Запускаю скрипт сбора телеметрии")
    time.sleep(1)
    
    # Initialize database
    print("Инициализирую базу данных...")
    if not create_tables():
        print("Ошибка при инициализации базы данных!")
        return
    
    hostname = socket.gethostname()
    timestamp = datetime.now()
    
    # Collect data with loading animations
    animated_loading("Собираю данные о памяти")
    mem_output = run_command("free -h")
    mem_data = parse_memory_info(mem_output, hostname, timestamp)
    if mem_data:
        save_to_database(mem_data, "memory_info")
    
    animated_loading("Собираю данные о CPU")
    cpu_output = run_command("top -bn1 | head -5")
    cpu_data = parse_cpu_info(cpu_output, hostname, timestamp)
    if cpu_data:
        save_to_database(cpu_data, "cpu_info")
    
    animated_loading("Собираю данные о дисках")
    disks_output = run_command("df -h")
    disks_data = parse_disk_info(disks_output, hostname, timestamp)
    if disks_data:
        save_to_database(disks_data, "disk_info")
    
    animated_loading("Собираю данные о процессах")
    proc_output = run_command("ps aux --sort=-%cpu | head -5")
    proc_data = parse_process_info(proc_output, hostname, timestamp)
    if proc_data:
        save_to_database(proc_data, "process_info")
    
    animated_loading("Собираю данные о сети")
    net_output = run_command("ss -tulpn")
    net_data = parse_network_info(net_output, hostname, timestamp)
    if net_data:
        save_to_database(net_data, "network_info")
    
    print(f"Готово братан! Данные сохранены в базу данных PostgreSQL")

if __name__ == "__main__":
    main()