#!/usr/bin/python3

import os
import sys
import ctypes
import ProjectedFS
from dataclasses import dataclass
from typing import Dict, List, Optional, Union
from pathlib import Path
import json
import base64
from datetime import datetime, timedelta

# HRESULT
S_OK                    = 0x00000000
E_OUTOFMEMORY           = 0x8007000E
E_INVALIDARG            = 0x80070057

# HRESULT_FROM_WIN32()
ERROR_FILE_NOT_FOUND    = 0x80070002
ERROR_INVALID_PARAMETER = 0x80070057

# Virtual file system root
virt_root = "C:\\vfs"

@dataclass
class VirtualFile:
    """Represents a virtual file"""
    name: str
    content: bytes
    size: int
    
    def __init__(self, name: str, content: Union[str, bytes]):
        self.name = name
        if isinstance(content, str):
            self.content = content.encode('utf-8')
        else:
            self.content = content
        self.size = len(self.content)

@dataclass
class VirtualDirectory:
    """Represents a virtual directory"""
    name: str
    files: Dict[str, VirtualFile]
    subdirs: Dict[str, 'VirtualDirectory']
    
    def __init__(self, name: str):
        self.name = name
        self.files = {}
        self.subdirs = {}
    
    def add_file(self, file: VirtualFile):
        self.files[file.name.lower()] = file
    
    def add_directory(self, subdir: 'VirtualDirectory'):
        self.subdirs[subdir.name.lower()] = subdir
    
    def get_item(self, path: str) -> Optional[Union[VirtualFile, 'VirtualDirectory']]:
        """Get an item by path relative to this directory"""
        if not path:
            return self
            
        # Normalize path
        path = path.replace('\\', '/')
        parts = [p for p in path.split('/') if p]  # Remove empty parts
        
        if not parts:
            return self
        
        first = parts[0].lower()
        
        if len(parts) == 1:
            # Looking for immediate child
            if first in self.files:
                return self.files[first]
            elif first in self.subdirs:
                return self.subdirs[first]
            return None
        else:
            # Looking deeper
            if first in self.subdirs:
                remaining_path = '/'.join(parts[1:])
                return self.subdirs[first].get_item(remaining_path)
            return None
    
    def enumerate_items(self) -> List[tuple]:
        """Enumerate all immediate children (files and directories)"""
        items = []
        
        # Add subdirectories first
        for name, subdir in self.subdirs.items():
            info = ProjectedFS.PRJ_FILE_BASIC_INFO()
            info.IsDirectory = True
            info.FileSize = 0
            items.append((subdir.name, info))
        
        # Add files
        for name, file in self.files.items():
            info = ProjectedFS.PRJ_FILE_BASIC_INFO()
            info.IsDirectory = False
            info.FileSize = file.size
            items.append((file.name, info))
        
        return items

def generate_fake_private_key():
    """Generate a fake SSH private key"""
    return """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA7VJejqHONZGnFLDfPOxW2ni6bvCJmK3gQ4L5hnXH/1FC6XQ7
HONEYPOT_PRIVATE_KEY_DO_NOT_USE_IN_PRODUCTION_SECURITY_MONITORING
8QZNnW8lxQL9qRnWDAJ5TqFRb5VmRfLbB5yQrPqaZPNPEckKZfQqB/DUYFmzzH5
bRvezWkDwBdGwqn1j5VmRqP6xqQYsq8K5rqaBn8fHz2wjZ5YhDH3j7qQ5VmRfLbB
INTRUDER_ALERT_SYSTEM_ACTIVATED_BY_ACCESSING_THIS_FILE_2024
vTK9WgCUzKLNvG5Y4QZKTwqY8V3nQKqF8QZNnW8lxQL9qRnWDAJ5TqFRb5VmRfL
-----END RSA PRIVATE KEY-----"""

def generate_fake_public_key():
    """Generate a fake SSH public key"""
    return "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQHONEYPOT_KEY_FOR_INTRUSION_DETECTION_DO_NOT_USE honeypot@security-monitoring-system"

def create_virtual_filesystem():
    """Create a honeypot file system structure mimicking cloud configurations"""
    root = VirtualDirectory("")
    
    # Create timestamp for realistic looking dates
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    last_week = now - timedelta(days=7)
    
    # Root level sensitive files (bait)
    root.add_file(VirtualFile("database_backup.sql", 
        "-- HONEYPOT DATABASE DUMP - SECURITY MONITORING ACTIVE\n"
        "-- Unauthorized access detected and logged\n"
        "-- IP and credentials have been recorded\n"
        "CREATE DATABASE honeypot_prod;\n"
        "USE honeypot_prod;\n"
        "CREATE TABLE users (id INT, username VARCHAR(50), password VARCHAR(100));\n"
        "INSERT INTO users VALUES (1, 'admin', 'HONEYPOT_HASH_$2y$10$fake_bcrypt_hash');\n"
        "INSERT INTO users VALUES (2, 'root', 'HONEYPOT_HASH_$2y$10$security_monitoring');\n"
        "-- Alert: Intrusion Detection System Active\n"))
    
    root.add_file(VirtualFile("passwords.txt",
        "# HONEYPOT CREDENTIALS - SECURITY MONITORING ACTIVE\n"
        "# All access attempts are logged and reported\n"
        "admin:HoneyPot2024!Monitor\n"
        "root:SecurityAlert#Active\n"
        "deploy:IntrusionDetected123\n"
        "service:LoggingEnabled@2024\n"))
    
    root.add_file(VirtualFile("wallet.dat",
        b'\x00\x01\x02HONEYPOT_BITCOIN_WALLET_INTRUSION_DETECTION\x00' * 100))
    
    # .aws folder - AWS credentials honeypot
    aws_dir = VirtualDirectory(".aws")
    
    aws_dir.add_file(VirtualFile("credentials",
        "[default]\n"
        "# HONEYPOT AWS CREDENTIALS - INTRUSION DETECTION SYSTEM\n"
        "# Unauthorized access will be prosecuted\n"
        "aws_access_key_id = AKIAHONEYPOTDETECTION01\n"
        "aws_secret_access_key = wJalrXUtnHONEYPOT/K7MDENG/bPxRfiCYSECURITY\n"
        "region = us-east-1\n"
        "\n"
        "[production]\n"
        "aws_access_key_id = AKIAPRODINTRUSIONALERT02\n"
        "aws_secret_access_key = 5bXgRtHONEYPOT+SECURITY+MONITORING+ACTIVE+24/7\n"
        "region = us-west-2\n"
        "\n"
        "[staging]\n"
        "aws_access_key_id = AKIASTAGINGDETECTION03\n"
        "aws_secret_access_key = 7dYtPqHONEYPOT/LOGGED/REPORTED/AUTHORITIES\n"
        "region = eu-west-1\n"))
    
    aws_dir.add_file(VirtualFile("config",
        "[default]\n"
        "region = us-east-1\n"
        "output = json\n"
        "\n"
        "[profile production]\n"
        "region = us-west-2\n"
        "output = json\n"
        "role_arn = arn:aws:iam::123456789012:role/HoneypotProductionRole\n"
        "source_profile = default\n"
        "\n"
        "[profile staging]\n"
        "region = eu-west-1\n"
        "output = table\n"))
    
    aws_dir.add_file(VirtualFile("cli_history",
        f"# AWS CLI Command History - HONEYPOT MONITORING\n"
        f"# {yesterday.isoformat()}\n"
        "aws s3 ls s3://prod-secrets-bucket/\n"
        "aws iam list-users\n"
        "aws ec2 describe-instances --region us-east-1\n"
        "aws rds describe-db-instances\n"
        "aws lambda list-functions\n"
        "aws secretsmanager get-secret-value --secret-id prod/database/password\n"))
    
    # .azure folder - Azure credentials honeypot
    azure_dir = VirtualDirectory(".azure")
    
    azure_dir.add_file(VirtualFile("azureProfile.json", json.dumps({
        "subscriptions": [
            {
                "id": "honeypot-0000-0000-0000-detectintrusion",
                "name": "Production-Honeypot-Monitor",
                "state": "Enabled",
                "user": {
                    "name": "admin@honeypotcorp.onmicrosoft.com",
                    "type": "user"
                },
                "isDefault": True,
                "tenantId": "security-0000-0000-0000-monitoring"
            }
        ],
        "installationId": "honeypot-detection-system-2024",
        "_warning": "HONEYPOT - INTRUSION DETECTION ACTIVE"
    }, indent=2)))
    
    azure_dir.add_file(VirtualFile("accessTokens.json", json.dumps({
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.HONEYPOT_TOKEN_INTRUSION_DETECTED",
        "refresh_token": "0.ARoAv4jHONEYPOTSECURITYMONITORINGACTIVE2024DETECTION",
        "expires_on": "2024-12-31 23:59:59",
        "subscription": "honeypot-0000-0000-0000-detectintrusion",
        "_alert": "SECURITY MONITORING - ALL ACCESS LOGGED"
    }, indent=2)))
    
    azure_dir.add_file(VirtualFile("clouds.config",
        "[AzureCloud]\n"
        "endpoint=https://management.azure.com/\n"
        "api_key=HONEYPOT_AZURE_API_KEY_MONITORING_ACTIVE\n"
        "tenant=honeypotcorp.onmicrosoft.com\n"))
    
    # .ssh folder - SSH keys honeypot
    ssh_dir = VirtualDirectory(".ssh")
    
    ssh_dir.add_file(VirtualFile("id_rsa", generate_fake_private_key()))
    ssh_dir.add_file(VirtualFile("id_rsa.pub", generate_fake_public_key()))
    
    ssh_dir.add_file(VirtualFile("id_ed25519",
        "-----BEGIN OPENSSH PRIVATE KEY-----\n"
        "b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtz\n"
        "HONEYPOT_ED25519_KEY_INTRUSION_DETECTION_SYSTEM_ACTIVE_2024\n"
        "-----END OPENSSH PRIVATE KEY-----"))
    
    ssh_dir.add_file(VirtualFile("authorized_keys",
        "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAHONEYPOT production-key\n"
        "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHONEYPOTDETECTION deployment-key\n"
        "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAMONITORING backup-access\n"))
    
    ssh_dir.add_file(VirtualFile("known_hosts",
        "github.com ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQHONEYPOT\n"
        "gitlab.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMONITORING\n"
        "bitbucket.org ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAADETECTION\n"
        "prod-server.internal ssh-rsa AAAAB3NzaC1yc2ELOGGING\n"))
    
    ssh_dir.add_file(VirtualFile("config",
        "# SSH Config - HONEYPOT MONITORING\n"
        "Host prod-server\n"
        "    HostName 10.0.1.100\n"
        "    User admin\n"
        "    IdentityFile ~/.ssh/id_rsa\n"
        "    Port 22\n"
        "\n"
        "Host database-server\n"
        "    HostName 10.0.2.50\n"
        "    User dbadmin\n"
        "    IdentityFile ~/.ssh/id_ed25519\n"
        "    Port 2222\n"))
    
    # .docker folder
    docker_dir = VirtualDirectory(".docker")
    
    docker_dir.add_file(VirtualFile("config.json", json.dumps({
        "auths": {
            "https://index.docker.io/v1/": {
                "auth": base64.b64encode(b"honeypot:SecurityMonitoring2024").decode(),
                "_warning": "HONEYPOT CREDENTIALS - INTRUSION DETECTED"
            },
            "private-registry.company.com": {
                "auth": base64.b64encode(b"admin:HoneypotAlert123").decode(),
                "email": "security@honeypot-monitoring.com"
            }
        },
        "HttpHeaders": {
            "User-Agent": "Docker-Client-Honeypot/19.03.12"
        }
    }, indent=2)))
    
    # .kube folder - Kubernetes honeypot
    kube_dir = VirtualDirectory(".kube")
    
    kube_dir.add_file(VirtualFile("config",
        "apiVersion: v1\n"
        "kind: Config\n"
        "clusters:\n"
        "- cluster:\n"
        "    certificate-authority-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCkhPTkVZUE9UX0NFUlRJRklDQVRFX0lOVFJVU0lPTl9ERVRFQ1RJT04KLS0tLS1FTkQgQ0VSVElGSUNBVEUtLS0tLQ==\n"
        "    server: https://k8s-prod.honeypot.local:6443\n"
        "  name: production-cluster\n"
        "contexts:\n"
        "- context:\n"
        "    cluster: production-cluster\n"
        "    user: admin\n"
        "  name: production\n"
        "current-context: production\n"
        "users:\n"
        "- name: admin\n"
        "  user:\n"
        "    client-certificate-data: LS0tLS1IT05FWVBPVCBDTElFTlQgQ0VSVElGSUNBVEUtLS0tLQ==\n"
        "    client-key-data: LS0tLS1IT05FWVBPVCBQUklWQVRFIEtFWS0tLS0t\n"))
    
    # .gcloud folder - Google Cloud honeypot
    gcloud_dir = VirtualDirectory(".gcloud")
    
    gcloud_dir.add_file(VirtualFile("application_default_credentials.json", json.dumps({
        "type": "service_account",
        "project_id": "honeypot-project-2024",
        "private_key_id": "honeypot00000000000000000000000000000000",
        "private_key": "-----BEGIN RSA PRIVATE KEY-----\nHONEYPOT_GCP_KEY_INTRUSION_DETECTION\n-----END RSA PRIVATE KEY-----",
        "client_email": "honeypot@honeypot-project-2024.iam.gserviceaccount.com",
        "client_id": "000000000000000000000",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "_alert": "HONEYPOT - SECURITY MONITORING ACTIVE"
    }, indent=2)))
    
    gcloud_dir.add_file(VirtualFile("credentials.db",
        b'SQLite format 3\x00HONEYPOT_DATABASE_INTRUSION_ALERT'))
    
    # .git-credentials file
    root.add_file(VirtualFile(".git-credentials",
        "https://honeypot-user:ghp_HONEYPOTTOKEN0000000000000000000000@github.com\n"
        "https://admin:glpat-HONEYPOT_GITLAB_TOKEN_DETECTED_2024@gitlab.com\n"
        "https://deploy:BBHONEYPOTBITBUCKETTOKEN@bitbucket.org\n"))
    
    # .env files - Environment variables honeypot
    root.add_file(VirtualFile(".env",
        "# HONEYPOT ENVIRONMENT VARIABLES - INTRUSION DETECTION SYSTEM\n"
        "DATABASE_URL=postgresql://admin:HoneypotDB2024!@db.internal:5432/production\n"
        "REDIS_URL=redis://:HoneypotRedis123@cache.internal:6379/0\n"
        "SECRET_KEY=HONEYPOT_SECRET_KEY_SECURITY_MONITORING_ACTIVE_2024\n"
        "API_KEY=sk-HONEYPOT0000000000000000000000000000000000000\n"
        "STRIPE_SECRET_KEY=sk_live_HONEYPOT_STRIPE_KEY_INTRUSION_DETECTED\n"
        "SENDGRID_API_KEY=SG.HONEYPOT_SENDGRID_MONITORING_ACTIVE_2024\n"
        "JWT_SECRET=HONEYPOT_JWT_SECRET_ALL_ACCESS_LOGGED\n"
        "ENCRYPTION_KEY=HONEYPOT_AES256_KEY_SECURITY_ALERT\n"
        "SLACK_WEBHOOK=https://hooks.slack.com/services/HONEYPOT/DETECTION/ACTIVE\n"
        "TWILIO_AUTH_TOKEN=HONEYPOT_TWILIO_TOKEN_MONITORING_2024\n"))
    
    root.add_file(VirtualFile(".env.production",
        "# Production Environment - HONEYPOT MONITORING\n"
        "NODE_ENV=production\n"
        "API_ENDPOINT=https://api.honeypot-prod.com\n"
        "ADMIN_PASSWORD=Pr0duct10n#H0neyp0t!2024\n"))
    
    # Database config folder
    db_configs = VirtualDirectory("database_configs")
    
    db_configs.add_file(VirtualFile("mongodb.conf",
        "# MongoDB Configuration - HONEYPOT\n"
        "storage:\n"
        "  dbPath: /var/lib/mongodb\n"
        "security:\n"
        "  authorization: enabled\n"
        "net:\n"
        "  bindIp: 0.0.0.0\n"
        "# Admin credentials\n"
        "# username: admin\n"
        "# password: MongoHoneypot2024!\n"))
    
    db_configs.add_file(VirtualFile("redis.conf",
        "# Redis Configuration - HONEYPOT MONITORING\n"
        "bind 0.0.0.0\n"
        "protected-mode no\n"
        "requirepass HoneypotRedis2024!Security\n"
        "# Master password for replication\n"
        "masterauth HoneypotMaster2024!Alert\n"))
    
    db_configs.add_file(VirtualFile("mysql.cnf",
        "[client]\n"
        "host = db.internal.honeypot.com\n"
        "user = root\n"
        "password = MySQLHoneypot2024!Detect\n"
        "\n"
        "[mysql]\n"
        "database = production_honeypot\n"))
    
    # Backup folder with fake backups
    backups = VirtualDirectory("backups")
    
    backups.add_file(VirtualFile("backup_2024_full.tar.gz",
        b'\x1f\x8b\x08\x00HONEYPOT_BACKUP_FILE_INTRUSION_DETECTION' + b'\x00' * 1024))
    
    backups.add_file(VirtualFile("private_keys_backup.zip",
        b'PK\x03\x04HONEYPOT_ZIP_ARCHIVE_SECURITY_MONITORING' + b'\x00' * 512))
    
    backups.add_file(VirtualFile("customer_data_export.csv",
        "id,email,password_hash,credit_card_last4,ssn_last4\n"
        "1,admin@honeypot.com,HONEYPOT_HASH_DETECTED,1234,5678\n"
        "2,user@security.com,INTRUSION_ALERT_HASH,4321,8765\n"
        "# HONEYPOT DATA - ALL ACCESS IS MONITORED AND LOGGED\n"))
    
    # Terraform folder
    terraform = VirtualDirectory("terraform")
    
    terraform.add_file(VirtualFile("terraform.tfvars",
        "# Terraform Variables - HONEYPOT INFRASTRUCTURE\n"
        'aws_access_key = "AKIAHONEYPOTTERRAFORM"\n'
        'aws_secret_key = "wJalrXUtnHONEYPOT/TERRAFORM/INTRUSION/DETECTED"\n'
        'db_master_password = "TerraformDB2024!Honeypot"\n'
        'api_keys = {\n'
        '  stripe = "sk_live_HONEYPOT_STRIPE_TERRAFORM"\n'
        '  sendgrid = "SG.HONEYPOT_SENDGRID_TERRAFORM"\n'
        '  datadog = "HONEYPOT_DATADOG_API_KEY_2024"\n'
        '}\n'))
    
    terraform.add_file(VirtualFile("backend.tf",
        'terraform {\n'
        '  backend "s3" {\n'
        '    bucket = "honeypot-terraform-state"\n'
        '    key    = "prod/terraform.tfstate"\n'
        '    region = "us-east-1"\n'
        '    # HONEYPOT - SECURITY MONITORING ACTIVE\n'
        '  }\n'
        '}\n'))
    
    # VPN configs
    vpn_dir = VirtualDirectory("vpn_configs")
    
    vpn_dir.add_file(VirtualFile("client.ovpn",
        "client\n"
        "dev tun\n"
        "proto udp\n"
        "remote vpn.honeypot-corp.com 1194\n"
        "# HONEYPOT VPN CONFIGURATION\n"
        "<ca>\n"
        "-----BEGIN CERTIFICATE-----\n"
        "HONEYPOT_CA_CERTIFICATE_INTRUSION_DETECTION\n"
        "-----END CERTIFICATE-----\n"
        "</ca>\n"
        "<cert>\n"
        "-----BEGIN CERTIFICATE-----\n"
        "HONEYPOT_CLIENT_CERT_MONITORING_ACTIVE\n"
        "-----END CERTIFICATE-----\n"
        "</cert>\n"
        "<key>\n"
        "-----BEGIN PRIVATE KEY-----\n"
        "HONEYPOT_VPN_PRIVATE_KEY_SECURITY_ALERT\n"
        "-----END PRIVATE KEY-----\n"
        "</key>\n"))
    
    # Cryptocurrency wallets
    crypto = VirtualDirectory("crypto_wallets")
    
    crypto.add_file(VirtualFile("bitcoin_seed.txt",
        "# HONEYPOT BITCOIN WALLET SEED - INTRUSION DETECTED\n"
        "witness honeypot security monitor detect intrusion alert system active log report authority notify\n"
        "# Wallet Address: 1HoneyPotBTCAddressSecurityMonitor2024\n"
        "# Private Key: L5HoneypotPrivateKeyIntrusionDetectionSystemActive2024\n"))
    
    crypto.add_file(VirtualFile("ethereum_keystore.json", json.dumps({
        "address": "0xhoneypot0000000000000000000000000000000",
        "crypto": {
            "cipher": "aes-128-ctr",
            "ciphertext": "HONEYPOT_ENCRYPTED_KEY_INTRUSION_ALERT",
            "kdf": "scrypt",
            "_warning": "HONEYPOT WALLET - SECURITY MONITORING ACTIVE"
        },
        "version": 3
    }, indent=2)))
    
    # API Keys file
    root.add_file(VirtualFile("api_keys.yml",
        "# API Keys Configuration - HONEYPOT MONITORING\n"
        "production:\n"
        "  openai:\n"
        "    key: sk-HONEYPOT0000000000000000OpenAI00000000000000000\n"
        "    org: org-HoneypotSecurityMonitoring2024\n"
        "  google_maps:\n"
        "    key: AIzaHONEYPOT_GOOGLE_MAPS_INTRUSION_DETECTED\n"
        "  twitter:\n"
        "    consumer_key: HONEYPOT_TWITTER_CONSUMER_KEY_2024\n"
        "    consumer_secret: HONEYPOT_TWITTER_SECRET_MONITORING\n"
        "    access_token: HONEYPOT_TWITTER_ACCESS_TOKEN_ALERT\n"
        "  facebook:\n"
        "    app_id: honeypot_facebook_app_2024\n"
        "    app_secret: HONEYPOT_FB_SECRET_INTRUSION_LOGGED\n"
        "  paypal:\n"
        "    client_id: HONEYPOT_PAYPAL_CLIENT_DETECTION\n"
        "    secret: HONEYPOT_PAYPAL_SECRET_MONITORING_2024\n"))
    
    # Add all directories to root
    root.add_directory(aws_dir)
    root.add_directory(azure_dir)
    root.add_directory(ssh_dir)
    root.add_directory(docker_dir)
    root.add_directory(kube_dir)
    root.add_directory(gcloud_dir)
    root.add_directory(db_configs)
    root.add_directory(backups)
    root.add_directory(terraform)
    root.add_directory(vpn_dir)
    root.add_directory(crypto)
    
    # Add a README to explain (in case someone legitimate finds this)
    root.add_file(VirtualFile("README_HONEYPOT.txt",
        "=" * 70 + "\n"
        "                    SECURITY HONEYPOT SYSTEM\n"
        "=" * 70 + "\n\n"
        "This is a honeypot file system designed for intrusion detection.\n"
        "All files and credentials in this directory are fake and monitored.\n\n"
        "ANY UNAUTHORIZED ACCESS ATTEMPTS ARE:\n"
        "- Automatically logged with full details\n"
        "- Reported to security teams\n"
        "- Subject to legal action\n\n"
        "IP Address, access time, and all actions are being recorded.\n\n"
        "If you've accessed this system by mistake, please contact:\n"
        "security@honeypot-monitoring.local immediately.\n\n"
        "=" * 70 + "\n"))
    
    return root

# Global virtual file system
virtual_fs = create_virtual_filesystem()
sessions = {}

@ProjectedFS.PRJ_START_DIRECTORY_ENUMERATION_CB
def startdir_enum_cb(callbackData, enumerationId):
    """Start directory enumeration"""
    try:
        # Get the directory path being enumerated
        path = ""
        if hasattr(callbackData, 'contents'):
            if hasattr(callbackData.contents, 'FilePathName'):
                path = callbackData.contents.FilePathName
        
        # Initialize session for this enumeration
        sessions[enumerationId.contents] = {
            'path': path,
            'completed': False,
            'items_sent': set()
        }
        
        # Log potential intrusion attempt
        print(f"[HONEYPOT] Directory enumeration started for: '{path}'")
        return S_OK
    except Exception as e:
        print(f"Error in startdir_enum_cb: {e}")
        return S_OK

@ProjectedFS.PRJ_END_DIRECTORY_ENUMERATION_CB
def enddir_enum_cb(callbackData, enumerationId):
    """End directory enumeration"""
    try:
        enum_id = enumerationId.contents
        if enum_id in sessions:
            del sessions[enum_id]
        return S_OK
    except Exception as e:
        print(f"Error in enddir_enum_cb: {e}")
        return S_OK

@ProjectedFS.PRJ_GET_DIRECTORY_ENUMERATION_CB
def getdir_enum_cb(callbackData, enumerationId, searchExpression, dirEntryBufferHandle):
    """Get directory enumeration entries"""
    try:
        enum_id = enumerationId.contents
        
        # Get or create session
        if enum_id not in sessions:
            sessions[enum_id] = {
                'path': "",
                'completed': False,
                'items_sent': set()
            }
        
        session = sessions[enum_id]
        
        # Check for restart scan flag
        restart_scan = False
        if hasattr(callbackData, 'contents'):
            if hasattr(callbackData.contents, 'Flags'):
                restart_scan = bool(callbackData.contents.Flags & ProjectedFS.PRJ_CB_DATA_FLAG_ENUM_RESTART_SCAN)
        
        # Reset if restart is requested
        if restart_scan or not session['items_sent']:
            session['completed'] = False
            session['items_sent'] = set()
            
            # Update path if available
            if hasattr(callbackData, 'contents'):
                if hasattr(callbackData.contents, 'FilePathName'):
                    session['path'] = callbackData.contents.FilePathName or ""
        
        # If already completed, return
        if session['completed']:
            return S_OK
        
        # Get the directory being enumerated
        path = session['path']
        
        # Get the directory item
        if path:
            item = virtual_fs.get_item(path)
        else:
            item = virtual_fs
        
        if not item or not isinstance(item, VirtualDirectory):
            return ERROR_FILE_NOT_FOUND
        
        # Get all items in this directory
        items = item.enumerate_items()
        
        # Send items that match the search expression
        for name, info in items:
            # Skip if already sent
            if name.lower() in session['items_sent']:
                continue
            
            # Check if matches search expression
            if searchExpression is None or ProjectedFS.PrjFileNameMatch(name, searchExpression):
                result = ProjectedFS.PrjFillDirEntryBuffer(name, info, dirEntryBufferHandle)
                
                if result == S_OK:
                    session['items_sent'].add(name.lower())
                elif result == 0x8007007A:  # ERROR_INSUFFICIENT_BUFFER
                    return S_OK
        
        # Mark as completed
        session['completed'] = True
        return S_OK
        
    except Exception as e:
        print(f"Error in getdir_enum_cb: {e}")
        return ERROR_INVALID_PARAMETER

@ProjectedFS.PRJ_GET_PLACEHOLDER_INFO_CB
def getplaceholder_info_cb(callbackData):
    """Get placeholder information for a file or directory"""
    try:
        if not hasattr(callbackData, 'contents'):
            return ERROR_INVALID_PARAMETER
            
        path = callbackData.contents.FilePathName
        
        # Log file access for honeypot monitoring
        if path and any(sensitive in path.lower() for sensitive in 
                       ['.aws', '.azure', 'credential', 'password', 'key', 'wallet', 'backup']):
            print(f"[HONEYPOT ALERT] Sensitive file accessed: '{path}'")
        
        # Get the item
        if path:
            item = virtual_fs.get_item(path)
        else:
            item = virtual_fs
        
        if not item:
            return ERROR_FILE_NOT_FOUND
        
        # Create placeholder info
        PlaceholderInfo = ProjectedFS.PRJ_PLACEHOLDER_INFO()
        PlaceholderInfo.FileBasicInfo = ProjectedFS.PRJ_FILE_BASIC_INFO()
        
        if isinstance(item, VirtualDirectory):
            PlaceholderInfo.FileBasicInfo.IsDirectory = True
            PlaceholderInfo.FileBasicInfo.FileSize = 0
        else:
            PlaceholderInfo.FileBasicInfo.IsDirectory = False
            PlaceholderInfo.FileBasicInfo.FileSize = item.size
        
        # Write placeholder info
        result = ProjectedFS.PrjWritePlaceholderInfo(
            callbackData.contents.NamespaceVirtualizationContext,
            path,
            PlaceholderInfo,
            ctypes.sizeof(PlaceholderInfo)
        )
        
        return result
        
    except Exception as e:
        print(f"Error in getplaceholder_info_cb: {e}")
        return ERROR_FILE_NOT_FOUND

@ProjectedFS.PRJ_GET_FILE_DATA_CB
def getfiledata_cb(callbackData, byteOffset, length):
    """Get file data for a virtual file"""
    try:
        if not hasattr(callbackData, 'contents'):
            return ERROR_INVALID_PARAMETER
            
        path = callbackData.contents.FilePathName
        
        # Critical honeypot alert for accessing file contents
        if path:
            print(f"[HONEYPOT CRITICAL] File contents read: '{path}' (offset={byteOffset}, len={length})")
        
        # Get the file
        item = virtual_fs.get_item(path)
        
        if not item or isinstance(item, VirtualDirectory):
            return ERROR_FILE_NOT_FOUND
        
        # Check bounds
        if byteOffset >= item.size:
            return S_OK
        
        # Calculate how much to write
        bytes_to_write = min(length, item.size - byteOffset)
        
        # Allocate buffer
        writeBuffer = ProjectedFS.PrjAllocateAlignedBuffer(
            callbackData.contents.NamespaceVirtualizationContext,
            bytes_to_write
        )
        
        if not writeBuffer:
            return E_OUTOFMEMORY
        
        # Copy the data
        data_slice = item.content[byteOffset:byteOffset + bytes_to_write]
        ctypes.memmove(ctypes.c_void_p(writeBuffer), data_slice, bytes_to_write)
        
        # Write the data
        result = ProjectedFS.PrjWriteFileData(
            callbackData.contents.NamespaceVirtualizationContext,
            callbackData.contents.DataStreamId,
            writeBuffer,
            byteOffset,
            bytes_to_write
        )
        
        # Free the buffer
        ProjectedFS.PrjFreeAlignedBuffer(writeBuffer)
        
        return result
        
    except Exception as e:
        print(f"Error in getfiledata_cb: {e}")
        return E_INVALIDARG

def main():
    # Create instance GUID
    instanceId = ProjectedFS.GUID()
    instanceId.Data1 = 0xDEADBEEF  # Honeypot identifier
    instanceId.Data2 = 0xCAFE
    instanceId.Data3 = 0xBABE
    
    # Create root directory if it doesn't exist
    if not os.path.exists(virt_root):
        print(f"Creating honeypot directory: {virt_root}")
        os.mkdir(virt_root)
    
    if not os.path.isdir(virt_root):
        print(f"{virt_root} is not a directory, exiting..")
        sys.exit(1)
    
    # Clear directory contents
    for item in os.listdir(virt_root):
        item_path = os.path.join(virt_root, item)
        try:
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                import shutil
                shutil.rmtree(item_path)
        except:
            pass
    
    # Mark directory as placeholder
    result = ProjectedFS.PrjMarkDirectoryAsPlaceholder(virt_root, None, None, instanceId)
    if result != S_OK:
        print(f"Error marking {virt_root} directory as placeholder. Error code: {hex(result)}")
        sys.exit(1)
    
    # Set up callbacks
    callbackTable = ProjectedFS.PRJ_CALLBACKS()
    callbackTable.StartDirectoryEnumerationCallback = startdir_enum_cb
    callbackTable.EndDirectoryEnumerationCallback = enddir_enum_cb
    callbackTable.GetDirectoryEnumerationCallback = getdir_enum_cb
    callbackTable.GetPlaceholderInfoCallback = getplaceholder_info_cb
    callbackTable.GetFileDataCallback = getfiledata_cb
    
    print("=" * 70)
    print("         HONEYPOT FILE SYSTEM - INTRUSION DETECTION ACTIVE")
    print("=" * 70)
    print("\nVirtual honeypot structure created with fake:")
    print("  • AWS credentials (.aws/)")
    print("  • Azure credentials (.azure/)")
    print("  • SSH keys (.ssh/)")
    print("  • Docker configs (.docker/)")
    print("  • Kubernetes configs (.kube/)")
    print("  • Google Cloud credentials (.gcloud/)")
    print("  • Database configs and backups")
    print("  • Terraform variables with 'secrets'")
    print("  • Cryptocurrency wallets")
    print("  • API keys and environment files")
    print("  • VPN configurations")
    print("\n[!] All access attempts will be logged")
    print(f"[!] Honeypot location: {virt_root}")
    print("\n" + "=" * 70)
    print("MONITORING LOG:")
    print("=" * 70 + "\n")
    
    # Start virtualization
    instanceHandle = ProjectedFS.PRJ_NAMESPACE_VIRTUALIZATION_CONTEXT()
    result = ProjectedFS.PrjStartVirtualizing(virt_root, callbackTable, None, None, instanceHandle)
    if result != S_OK:
        print(f"Error starting virtualization. Error code: {hex(result)}")
        sys.exit(1)
    
    try:
        input("\nPress Enter to stop the honeypot system...")
    except KeyboardInterrupt:
        print("\n[!] Shutting down honeypot monitoring...")
    
    # Stop virtualization
    ProjectedFS.PrjStopVirtualizing(instanceHandle)
    print("\n[!] Honeypot system stopped")
    print("[!] Remember to check logs for any intrusion attempts")

if __name__ == "__main__":
    main()
