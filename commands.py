# commands.py

"""
This file contains all the read-only commands
that the application is allowed to execute.

The LLM will only select one of these command keys.
The actual Linux command is retrieved from this dictionary.
"""

COMMANDS = {
    # System Information
    "hostname": {
        "description": "Get the hostname of the server",
        "command": "hostname",
        "category": "System Information",
        "examples": [
            "What is the hostname?",
            "What is the server name?",
            "Show system host name"
        ]
    },

    "current_user": {
        "description": "Get the currently logged-in user",
        "command": "whoami",
        "category": "System Information",
        "examples": [
            "Which user is logged in?",
            "Who am I logged in as?",
            "Show current user"
        ]
    },

    "os_version": {
        "description": "Get the operating system version",
        "command": "cat /etc/os-release",
        "category": "System Information",
        "examples": [
            "What OS is this server running?",
            "Show OS release version",
            "What Linux distribution is this?"
        ]
    },

    "kernel_version": {
        "description": "Get Linux kernel version",
        "command": "uname -r",
        "category": "System Information",
        "examples": [
            "What Linux kernel version is installed?",
            "Show kernel release",
            "Get uname kernel version"
        ]
    },

    "system_architecture": {
        "description": "Get system architecture",
        "command": "uname -m",
        "category": "System Information",
        "examples": [
            "What is the system architecture?",
            "Is this server 64-bit or 32-bit?",
            "Show machine hardware name"
        ]
    },

    "system_information": {
        "description": "Get complete system information",
        "command": "uname -a",
        "category": "System Information",
        "examples": [
            "Show complete system info",
            "Display full uname information",
            "Show system build details"
        ]
    },

    "server_time": {
        "description": "Get current server date and time",
        "command": "date",
        "category": "System Information",
        "examples": [
            "What time is it on the server?",
            "Show current date and time",
            "What is the server system clock?"
        ]
    },

    "server_timezone": {
        "description": "Get configured timezone",
        "command": "timedatectl",
        "category": "System Information",
        "examples": [
            "What is the server timezone?",
            "Show timedatectl settings",
            "Check system clock synchronization"
        ]
    },

    "uptime": {
        "description": "Get system uptime and load averages",
        "command": "uptime",
        "category": "System Information",
        "examples": [
            "How long has the server been up?",
            "Show server uptime",
            "Check system load averages and uptime"
        ]
    },

    # CPU Information
    "cpu_information": {
        "description": "Get CPU information",
        "command": "lscpu",
        "category": "CPU",
        "examples": [
            "Show CPU information",
            "What CPU model is installed?",
            "How many CPU cores are available?"
        ]
    },

    "cpu_usage": {
        "description": "Display CPU usage",
        "command": "top -bn1",
        "category": "CPU",
        "examples": [
            "What is the CPU usage?",
            "Show current CPU utilization",
            "Is CPU usage high?"
        ]
    },

    "cpu_load": {
        "description": "Display system load averages",
        "command": "cat /proc/loadavg",
        "category": "CPU",
        "examples": [
            "Is the server under heavy load?",
            "Show system load averages",
            "Display loadavg statistics"
        ]
    },

    # Memory Information
    "memory_usage": {
        "description": "Display memory usage",
        "command": "free -m",
        "category": "Memory",
        "examples": [
            "How much RAM is available?",
            "Show memory usage",
            "Is swap being used?"
        ]
    },

    "memory_details": {
        "description": "Display detailed memory information",
        "command": "cat /proc/meminfo",
        "category": "Memory",
        "examples": [
            "Display detailed memory info",
            "Show proc meminfo",
            "Check memory buffer and cache"
        ]
    },

    # Disk Information
    "disk_usage": {
        "description": "Display disk usage",
        "command": "df -h",
        "category": "Disk",
        "examples": [
            "Show disk usage",
            "Which filesystem is almost full?",
            "How much disk space is free?"
        ]
    },

    "disk_inodes": {
        "description": "Display inode usage",
        "command": "df -i",
        "category": "Disk",
        "examples": [
            "Display inode usage",
            "Check for inode exhaustion",
            "Show filesystem inodes free"
        ]
    },

    "block_devices": {
        "description": "List block devices",
        "command": "lsblk",
        "category": "Disk",
        "examples": [
            "List block devices",
            "Show lsblk storage devices",
            "What hard drives are attached?"
        ]
    },

    "mounted_filesystems": {
        "description": "Show mounted filesystems",
        "command": "mount",
        "category": "Disk",
        "examples": [
            "Show mounted filesystems",
            "List active mounts",
            "What drives are mounted?"
        ]
    },

    # Network Information
    "ip_address": {
        "description": "Show IP addresses",
        "command": "ip addr",
        "category": "Network",
        "examples": [
            "What is the server IP?",
            "Show IP address",
            "List network interface IP addresses"
        ]
    },

    "routing_table": {
        "description": "Show routing table",
        "command": "ip route",
        "category": "Network",
        "examples": [
            "Show routing table",
            "Display default gateway and IP routes",
            "Show ip route"
        ]
    },

    "network_interfaces": {
        "description": "List network interfaces",
        "command": "ip link",
        "category": "Network",
        "examples": [
            "Show network interfaces",
            "List network interface link status",
            "Show network cards"
        ]
    },

    "dns_configuration": {
        "description": "Display DNS configuration",
        "command": "cat /etc/resolv.conf",
        "category": "Network",
        "examples": [
            "Display DNS configuration",
            "Show resolv.conf nameservers",
            "What DNS servers are used?"
        ]
    },

    "listening_ports": {
        "description": "Show listening TCP and UDP ports",
        "command": "ss -tuln",
        "category": "Network",
        "examples": [
            "Show listening ports",
            "Which TCP/UDP ports are open?",
            "Show active socket listeners"
        ]
    },

    "network_statistics": {
        "description": "Show network statistics",
        "command": "ss -s",
        "category": "Network",
        "examples": [
            "Show network statistics",
            "Display socket summary statistics",
            "Show active connection summary"
        ]
    },

    # Running Processes
    "running_processes": {
        "description": "List running processes",
        "command": "ps aux",
        "category": "Processes",
        "examples": [
            "Show running processes",
            "List all active processes",
            "Display ps aux"
        ]
    },

    "process_tree": {
        "description": "Display process hierarchy",
        "command": "pstree",
        "category": "Processes",
        "examples": [
            "Display process hierarchy",
            "Show process tree",
            "View parent-child process relationship"
        ]
    },

    "top_cpu_processes": {
        "description": "Show top CPU consuming processes",
        "command": "ps -eo pid,comm,%cpu --sort=-%cpu | head",
        "category": "Processes",
        "examples": [
            "Which processes use the most CPU?",
            "Show top CPU processes",
            "List heaviest CPU consumers"
        ]
    },

    "top_memory_processes": {
        "description": "Show top memory consuming processes",
        "command": "ps -eo pid,comm,%mem --sort=-%mem | head",
        "category": "Processes",
        "examples": [
            "Which processes use the most RAM?",
            "Show top memory processes",
            "List highest memory using processes"
        ]
    },

    # Services
    "running_services": {
        "description": "List running services",
        "command": "systemctl list-units --type=service --state=running",
        "category": "Services",
        "examples": [
            "Show running services",
            "List active systemd services",
            "What services are running?"
        ]
    },

    "failed_services": {
        "description": "List failed services",
        "command": "systemctl --failed",
        "category": "Services",
        "examples": [
            "Are any services failing?",
            "Show failed services",
            "List systemd units in failed state"
        ]
    },

    # Logged-in Users
    "logged_in_users": {
        "description": "Display logged-in users",
        "command": "who",
        "category": "Logged-in Users",
        "examples": [
            "Display logged-in users",
            "Who is currently connected?",
            "Show logged in user sessions"
        ]
    },

    "user_login_history": {
        "description": "Display login history",
        "command": "last",
        "category": "Logged-in Users",
        "examples": [
            "Display login history",
            "Show recent user logins",
            "Who logged in recently?"
        ]
    },

    # Filesystem
    "current_directory": {
        "description": "Display current working directory",
        "command": "pwd",
        "category": "Filesystem",
        "examples": [
            "Display current working directory",
            "Where am I on the filesystem?",
            "Show present working directory"
        ]
    },

    "disk_partitions": {
        "description": "List partitions",
        "command": "lsblk -f",
        "category": "Filesystem",
        "examples": [
            "List partitions and filesystems",
            "Show disk partition table with UUIDs",
            "List lsblk filesystem types"
        ]
    },

    # Environment
    "environment_variables": {
        "description": "Display environment variables",
        "command": "printenv",
        "category": "Environment",
        "examples": [
            "Display environment variables",
            "Show printenv output",
            "List system environment vars"
        ]
    },

    "path_variable": {
        "description": "Display PATH variable",
        "command": "echo $PATH",
        "category": "Environment",
        "examples": [
            "Display PATH variable",
            "What is the system executable PATH?",
            "Show echo $PATH"
        ]
    },

    # Docker (Read-only)
    "docker_containers": {
        "description": "List Docker containers",
        "command": "docker ps -a",
        "category": "Docker",
        "examples": [
            "List Docker containers",
            "Are any docker containers running?",
            "Show all container statuses"
        ]
    },

    "docker_images": {
        "description": "List Docker images",
        "command": "docker images",
        "category": "Docker",
        "examples": [
            "List Docker images",
            "Show local docker images",
            "What docker images are stored?"
        ]
    },

    "docker_system_info": {
        "description": "Display Docker information",
        "command": "docker info",
        "category": "Docker",
        "examples": [
            "Display Docker information",
            "Check docker engine status",
            "Show docker daemon overview"
        ]
    },

    # Last Command Run
    "last_command": {
        "description": "Get last command executed",
        "command": "history 1",
        "category": "History & Jobs",
        "examples": [
            "Get last command executed",
            "Show recent command history",
            "What was the last command?"
        ]
    },

    # Background Jobs
    "background_jobs": {
        "description": "List background jobs",
        "command": "jobs",
        "category": "History & Jobs",
        "examples": [
            "List background jobs",
            "Show running shell jobs",
            "Are there active background jobs?"
        ]
    },

    # Last Login Info
    "last_login": {
        "description": "Display last login information",
        "command": "lastlog -u $(whoami)",
        "category": "Logged-in Users",
        "examples": [
            "Display last login information",
            "When did the current user last log in?",
            "Show lastlog for current user"
        ]
    },

    # Kubernetes (Read-only)
    "kubectl_nodes": {
        "description": "List Kubernetes nodes",
        "command": "kubectl get nodes",
        "category": "Kubernetes",
        "examples": [
            "List Kubernetes nodes",
            "Check K8s node status",
            "Show kubectl nodes"
        ]
    },

    "kubectl_pods": {
        "description": "List Kubernetes pods",
        "command": "kubectl get pods -A",
        "category": "Kubernetes",
        "examples": [
            "List Kubernetes pods",
            "Show all running pods across namespaces",
            "Check kubectl get pods"
        ]
    },

    "kubectl_services": {
        "description": "List Kubernetes services",
        "command": "kubectl get svc -A",
        "category": "Kubernetes",
        "examples": [
            "List Kubernetes services",
            "Show K8s services across namespaces",
            "Check kubectl services"
        ]
    },

    # Security
    "logged_in_sessions": {
        "description": "Display login sessions",
        "command": "w",
        "category": "Security",
        "examples": [
            "Display login sessions and activity",
            "Show w command output",
            "What are active users doing?"
        ]
    },

    "sudo_version": {
        "description": "Display sudo version",
        "command": "sudo -V",
        "category": "Security",
        "examples": [
            "Display sudo version",
            "Check sudo binary version",
            "What version of sudo is installed?"
        ]
    }
}


def get_command(command_key: str):
    """
    Returns the command information for the given key.

    Example:
        get_command("memory_usage")

    Returns:
        {
            "description": "...",
            "command": "free -m",
            "category": "Memory",
            "examples": [...]
        }

    Returns None if the key does not exist.
    """
    return COMMANDS.get(command_key)