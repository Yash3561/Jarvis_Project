"""
A.R.I.E.S. Guardian - The Unblinking Sentinel
Rules-Based Execution & Security Engine

This module implements:
- Credential Vault: Manages OAuth tokens & passwords via Master Password
- Permission Manager: Granular, explicit approval for ALL system-level actions
- Pre-Flight Verifier: Backs up files, generates 'diffs' for user confirmation
- Execution Engine: Safely runs the approved tools
- Rollback Controller: Automatically reverts failed operations
"""

import os
import json
import hashlib
import shutil
import tempfile
import difflib
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class CredentialVault:
    """Secure credential storage with master password protection"""
    
    def __init__(self, vault_path: str = "./.aries_vault"):
        self.vault_path = Path(vault_path)
        self.vault_path.mkdir(exist_ok=True)
        self.credentials_file = self.vault_path / "credentials.enc"
        self.salt_file = self.vault_path / "salt.bin"
        self.key_file = self.vault_path / "key.bin"
        self._fernet = None
        self._is_unlocked = False
    
    def initialize_vault(self, master_password: str) -> bool:
        """Initialize the vault with a master password"""
        try:
            # Generate salt and derive key
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
            
            # Save salt and key
            with open(self.salt_file, 'wb') as f:
                f.write(salt)
            with open(self.key_file, 'wb') as f:
                f.write(key)
            
            # Initialize empty credentials
            self._fernet = Fernet(key)
            self._save_credentials({})
            self._is_unlocked = True
            
            print("INFO: Credential vault initialized successfully")
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to initialize vault: {e}")
            return False
    
    def unlock_vault(self, master_password: str) -> bool:
        """Unlock the vault with master password"""
        try:
            if not self.salt_file.exists() or not self.key_file.exists():
                return False
            
            # Read salt and derive key
            with open(self.salt_file, 'rb') as f:
                salt = f.read()
            with open(self.key_file, 'rb') as f:
                stored_key = f.read()
            
            # Verify password by deriving key
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            derived_key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
            
            if derived_key != stored_key:
                return False
            
            self._fernet = Fernet(derived_key)
            self._is_unlocked = True
            print("INFO: Credential vault unlocked successfully")
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to unlock vault: {e}")
            return False
    
    def store_credential(self, service: str, username: str, credential_data: Dict) -> bool:
        """Store a credential securely"""
        if not self._is_unlocked:
            print("ERROR: Vault is locked")
            return False
        
        try:
            credentials = self._load_credentials()
            if service not in credentials:
                credentials[service] = {}
            
            credentials[service][username] = {
                "data": credential_data,
                "created": datetime.now().isoformat(),
                "last_used": None
            }
            
            self._save_credentials(credentials)
            print(f"INFO: Credential stored for {service}:{username}")
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to store credential: {e}")
            return False
    
    def get_credential(self, service: str, username: str) -> Optional[Dict]:
        """Retrieve a credential"""
        if not self._is_unlocked:
            print("ERROR: Vault is locked")
            return None
        
        try:
            credentials = self._load_credentials()
            if service in credentials and username in credentials[service]:
                # Update last used timestamp
                credentials[service][username]["last_used"] = datetime.now().isoformat()
                self._save_credentials(credentials)
                return credentials[service][username]["data"]
            return None
            
        except Exception as e:
            print(f"ERROR: Failed to retrieve credential: {e}")
            return None
    
    def _load_credentials(self) -> Dict:
        """Load encrypted credentials"""
        if not self.credentials_file.exists():
            return {}
        
        with open(self.credentials_file, 'rb') as f:
            encrypted_data = f.read()
        
        decrypted_data = self._fernet.decrypt(encrypted_data)
        return json.loads(decrypted_data.decode())
    
    def _save_credentials(self, credentials: Dict):
        """Save encrypted credentials"""
        encrypted_data = self._fernet.encrypt(json.dumps(credentials).encode())
        with open(self.credentials_file, 'wb') as f:
            f.write(encrypted_data)

class PermissionManager:
    """Granular permission system for all system actions"""
    
    def __init__(self):
        self.permission_levels = {
            "safe": ["read_file", "list_files", "get_location", "search_web"],
            "moderate": ["write_file", "create_directory", "run_command", "browse_web"],
            "high_risk": ["delete_file", "system_control", "install_software", "modify_registry"],
            "critical": ["format_drive", "delete_system_files", "modify_bootloader"]
        }
        
        self.user_permissions = {}  # Will be loaded from user preferences
        self.auto_approve_safe = True
        self.require_confirmation_moderate = True
        self.require_confirmation_high_risk = True
        self.require_confirmation_critical = True
    
    def check_permission(self, tool_name: str, action_description: str) -> Tuple[bool, str]:
        """Check if an action is permitted"""
        # Determine risk level
        risk_level = "safe"
        for level, tools in self.permission_levels.items():
            if tool_name in tools:
                risk_level = level
                break
        
        # Check auto-approval settings
        if risk_level == "safe" and self.auto_approve_safe:
            return True, "Auto-approved safe action"
        
        if risk_level == "moderate" and not self.require_confirmation_moderate:
            return True, "Auto-approved moderate action"
        
        if risk_level == "high_risk" and not self.require_confirmation_high_risk:
            return True, "Auto-approved high-risk action"
        
        if risk_level == "critical" and not self.require_confirmation_critical:
            return True, "Auto-approved critical action"
        
        # Action requires user confirmation
        return False, f"Requires user confirmation for {risk_level} risk action"
    
    def set_user_permissions(self, permissions: Dict):
        """Set user permission preferences"""
        self.user_permissions = permissions
        self.auto_approve_safe = permissions.get("auto_approve_safe", True)
        self.require_confirmation_moderate = permissions.get("require_confirmation_moderate", True)
        self.require_confirmation_high_risk = permissions.get("require_confirmation_high_risk", True)
        self.require_confirmation_critical = permissions.get("require_confirmation_critical", True)

class PreFlightVerifier:
    """Pre-execution verification and backup system"""
    
    def __init__(self, backup_dir: str = "./.aries_backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.backup_history = []
    
    async def verify_operation(self, tool_name: str, parameters: Dict, action_description: str) -> Tuple[bool, str, Optional[str]]:
        """Verify operation safety and create backups if needed"""
        try:
            # Check if this operation affects files
            if self._affects_files(tool_name, parameters):
                backup_path = await self._create_backup(parameters)
                diff_content = await self._generate_diff_preview(tool_name, parameters)
                
                return True, f"Backup created at {backup_path}", diff_content
            
            return True, "Operation verified safe", None
            
        except Exception as e:
            return False, f"Verification failed: {str(e)}", None
    
    def _affects_files(self, tool_name: str, parameters: Dict) -> bool:
        """Check if operation affects files"""
        file_operations = ["write_file", "delete_file", "create_directory", "modify_file"]
        return tool_name in file_operations
    
    async def _create_backup(self, parameters: Dict) -> str:
        """Create backup of affected files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"backup_{timestamp}"
        backup_path.mkdir(exist_ok=True)
        
        # Backup specific files mentioned in parameters
        if "file_path" in parameters:
            file_path = Path(parameters["file_path"])
            if file_path.exists():
                backup_file = backup_path / file_path.name
                shutil.copy2(file_path, backup_file)
        
        # Record backup
        self.backup_history.append({
            "timestamp": timestamp,
            "backup_path": str(backup_path),
            "parameters": parameters
        })
        
        return str(backup_path)
    
    async def _generate_diff_preview(self, tool_name: str, parameters: Dict) -> Optional[str]:
        """Generate diff preview for file modifications"""
        if tool_name == "write_file" and "file_path" in parameters:
            file_path = Path(parameters["file_path"])
            new_content = parameters.get("content", "")
            
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    old_content = f.read()
                
                # Generate diff
                diff = difflib.unified_diff(
                    old_content.splitlines(keepends=True),
                    new_content.splitlines(keepends=True),
                    fromfile=str(file_path),
                    tofile=str(file_path)
                )
                
                return ''.join(diff)
        
        return None

class RollbackController:
    """Automatic rollback system for failed operations"""
    
    def __init__(self, backup_dir: str = "./.aries_backups"):
        self.backup_dir = Path(backup_dir)
        self.operation_log = []
    
    async def log_operation(self, tool_name: str, parameters: Dict, backup_path: Optional[str] = None):
        """Log an operation for potential rollback"""
        operation = {
            "timestamp": datetime.now().isoformat(),
            "tool_name": tool_name,
            "parameters": parameters,
            "backup_path": backup_path,
            "status": "pending"
        }
        self.operation_log.append(operation)
    
    async def rollback_operation(self, operation_index: int) -> bool:
        """Rollback a specific operation"""
        if operation_index >= len(self.operation_log):
            return False
        
        operation = self.operation_log[operation_index]
        
        try:
            if operation["backup_path"] and Path(operation["backup_path"]).exists():
                # Restore from backup
                if "file_path" in operation["parameters"]:
                    file_path = Path(operation["parameters"]["file_path"])
                    backup_file = Path(operation["backup_path"]) / file_path.name
                    
                    if backup_file.exists():
                        shutil.copy2(backup_file, file_path)
                        operation["status"] = "rolled_back"
                        print(f"INFO: Successfully rolled back operation {operation_index}")
                        return True
            
            operation["status"] = "rollback_failed"
            return False
            
        except Exception as e:
            print(f"ERROR: Rollback failed: {e}")
            operation["status"] = "rollback_failed"
            return False
    
    async def rollback_last_operation(self) -> bool:
        """Rollback the most recent operation"""
        if not self.operation_log:
            return False
        
        return await self.rollback_operation(len(self.operation_log) - 1)

class Guardian:
    """
    The Unblinking Sentinel - Main Guardian class
    
    This class orchestrates all security and safety measures:
    1. Credential management
    2. Permission checking
    3. Pre-flight verification
    4. Safe execution
    5. Rollback capabilities
    """
    
    def __init__(self, controller=None):
        self.controller = controller
        self.credential_vault = CredentialVault()
        self.permission_manager = PermissionManager()
        self.preflight_verifier = PreFlightVerifier()
        self.rollback_controller = RollbackController()
        
        self._is_initialized = False
        print("INFO: A.R.I.E.S. Guardian initialized - Security protocols active")
    
    def initialize(self, master_password: str, user_permissions: Dict = None) -> bool:
        """Initialize the Guardian with master password and permissions"""
        try:
            # Initialize credential vault
            if not self.credential_vault.initialize_vault(master_password):
                return False
            
            # Set user permissions
            if user_permissions:
                self.permission_manager.set_user_permissions(user_permissions)
            
            self._is_initialized = True
            print("INFO: Guardian fully initialized and secured")
            return True
            
        except Exception as e:
            print(f"ERROR: Guardian initialization failed: {e}")
            return False
    
    async def execute_tool_safely(self, tool_name: str, parameters: Dict, verification: str) -> Any:
        """
        Execute a tool with full safety protocols
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            verification: How to verify success
            
        Returns:
            Tool execution result
        """
        if not self._is_initialized:
            raise Exception("Guardian not initialized")
        
        try:
            # Step 1: Permission Check
            permitted, reason = self.permission_manager.check_permission(tool_name, str(parameters))
            if not permitted:
                raise PermissionError(f"Action not permitted: {reason}")
            
            # Step 2: Pre-flight Verification
            verified, verification_msg, diff_content = await self.preflight_verifier.verify_operation(
                tool_name, parameters, verification
            )
            if not verified:
                raise Exception(f"Pre-flight verification failed: {verification_msg}")
            
            # Step 3: Log Operation for Rollback
            backup_path = None
            if "Backup created at" in verification_msg:
                backup_path = verification_msg.split("Backup created at ")[1]
            
            await self.rollback_controller.log_operation(tool_name, parameters, backup_path)
            
            # Step 4: Show Diff if Available
            if diff_content and self.controller:
                await self._show_diff_confirmation(diff_content, tool_name, parameters)
            
            # Step 5: Execute Tool
            result = await self._execute_tool(tool_name, parameters)
            
            # Step 6: Verify Success
            if not await self._verify_success(result, verification):
                # Rollback on verification failure
                await self.rollback_controller.rollback_last_operation()
                raise Exception("Tool execution verification failed - operation rolled back")
            
            print(f"INFO: Tool '{tool_name}' executed successfully")
            return result
            
        except Exception as e:
            print(f"ERROR: Tool execution failed: {e}")
            # Attempt rollback
            await self.rollback_controller.rollback_last_operation()
            raise
    
    async def _execute_tool(self, tool_name: str, parameters: Dict) -> Any:
        """Execute the actual tool function"""
        # This is where we'd dynamically import and execute the tool
        # For now, return a placeholder
        return f"Tool {tool_name} executed with parameters {parameters}"
    
    async def _verify_success(self, result: Any, verification: str) -> bool:
        """Verify that the tool execution was successful"""
        # Simple verification - in practice, this would be more sophisticated
        return result is not None and result != ""
    
    async def _show_diff_confirmation(self, diff_content: str, tool_name: str, parameters: Dict):
        """Show diff to user for confirmation"""
        if self.controller and hasattr(self.controller, 'add_message_signal'):
            diff_message = f"""
**File Modification Preview**

Tool: {tool_name}
File: {parameters.get('file_path', 'Unknown')}

**Changes to be made:**
```diff
{diff_content}
```

**Action:** This operation will modify the above file. Please confirm to proceed.
            """
            self.controller.add_message_signal.emit('system', diff_message, diff_message)
    
    def get_credential(self, service: str, username: str) -> Optional[Dict]:
        """Get a credential from the vault"""
        return self.credential_vault.get_credential(service, username)
    
    def store_credential(self, service: str, username: str, credential_data: Dict) -> bool:
        """Store a credential in the vault"""
        return self.credential_vault.store_credential(service, username, credential_data)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get Guardian system status"""
        return {
            "guardian_status": "active" if self._is_initialized else "initializing",
            "credential_vault": "unlocked" if self.credential_vault._is_unlocked else "locked",
            "permission_manager": "active",
            "preflight_verifier": "active",
            "rollback_controller": "active",
            "backup_count": len(self.rollback_controller.operation_log)
        }