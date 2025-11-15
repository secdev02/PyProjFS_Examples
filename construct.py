#!/usr/bin/python3

import os
import sys
import ctypes
import ProjectedFS
from dataclasses import dataclass
from typing import Dict, List, Optional, Union
from pathlib import Path

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

# Create the virtual file system structure
def create_virtual_filesystem():
    """Create a sample nested file system structure"""
    root = VirtualDirectory("")
    
    # Add some files to root
    root.add_file(VirtualFile("readme.txt", "This is a virtual file system"))
    root.add_file(VirtualFile("test.py", "print('Hello from virtual FS!')"))
    
    # Create documents folder
    docs = VirtualDirectory("Documents")
    docs.add_file(VirtualFile("report.txt", "Annual Report 2024\n" + "="*50 + "\nSales data..."))
    docs.add_file(VirtualFile("notes.md", "# Meeting Notes\n\n- Item 1\n- Item 2\n- Item 3"))
    
    # Create a subfolder in documents
    projects = VirtualDirectory("Projects")
    projects.add_file(VirtualFile("project1.txt", "Project Alpha Details"))
    projects.add_file(VirtualFile("project2.txt", "Project Beta Details"))
    docs.add_directory(projects)
    
    # Create source folder
    src = VirtualDirectory("Source")
    src.add_file(VirtualFile("main.cpp", "#include <iostream>\n\nint main() {\n    std::cout << \"Hello!\" << std::endl;\n    return 0;\n}"))
    src.add_file(VirtualFile("utils.cpp", "// Utility functions"))
    
    # Create headers subfolder
    headers = VirtualDirectory("Headers")
    headers.add_file(VirtualFile("common.h", "#pragma once\n\n#define VERSION \"1.0.0\""))
    headers.add_file(VirtualFile("utils.h", "#pragma once\n\nvoid util_function();"))
    src.add_directory(headers)
    
    # Create data folder
    data = VirtualDirectory("Data")
    data.add_file(VirtualFile("config.json", '{\n    "setting1": true,\n    "setting2": 42\n}'))
    data.add_file(VirtualFile("data.csv", "Name,Age,City\nAlice,30,New York\nBob,25,Los Angeles"))
    
    # Create nested folder in data
    cache = VirtualDirectory("Cache")
    cache.add_file(VirtualFile("temp.dat", b'\x00\x01\x02\x03\x04\x05'))
    
    logs = VirtualDirectory("Logs")
    logs.add_file(VirtualFile("app.log", "[2024-01-01] Application started\n[2024-01-01] Processing data..."))
    cache.add_directory(logs)
    data.add_directory(cache)
    
    # Add all top-level directories to root
    root.add_directory(docs)
    root.add_directory(src)
    root.add_directory(data)
    
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
        print(f"Starting enumeration for path: '{path}'")
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
            print(f"Ending enumeration for path: '{sessions[enum_id].get('path', '')}'")
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
        
        # Check for restart scan flag - need to access it correctly
        restart_scan = False
        if hasattr(callbackData, 'contents'):
            if hasattr(callbackData.contents, 'Flags'):
                restart_scan = bool(callbackData.contents.Flags & ProjectedFS.PRJ_CB_DATA_FLAG_ENUM_RESTART_SCAN)
        
        # Reset if restart is requested or this is first call
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
        print(f"Enumerating path: '{path}'")
        
        # Get the directory item
        if path:
            item = virtual_fs.get_item(path)
        else:
            item = virtual_fs
        
        if not item or not isinstance(item, VirtualDirectory):
            print(f"Path not found or not a directory: '{path}'")
            return ERROR_FILE_NOT_FOUND
        
        # Get all items in this directory
        items = item.enumerate_items()
        
        # Send items that match the search expression and haven't been sent yet
        for name, info in items:
            # Skip if already sent
            if name.lower() in session['items_sent']:
                continue
            
            # Check if matches search expression (None means match all)
            if searchExpression is None or ProjectedFS.PrjFileNameMatch(name, searchExpression):
                print(f"  Adding item: {name} (dir={info.IsDirectory})")
                result = ProjectedFS.PrjFillDirEntryBuffer(name, info, dirEntryBufferHandle)
                
                if result == S_OK:
                    session['items_sent'].add(name.lower())
                elif result == 0x8007007A:  # ERROR_INSUFFICIENT_BUFFER
                    # Buffer full, will continue in next call
                    print("Buffer full, will continue later")
                    return S_OK
                else:
                    print(f"Failed to add item {name}: {hex(result)}")
        
        # Mark as completed
        session['completed'] = True
        return S_OK
        
    except Exception as e:
        print(f"Error in getdir_enum_cb: {e}")
        import traceback
        traceback.print_exc()
        return ERROR_INVALID_PARAMETER

@ProjectedFS.PRJ_GET_PLACEHOLDER_INFO_CB
def getplaceholder_info_cb(callbackData):
    """Get placeholder information for a file or directory"""
    try:
        if not hasattr(callbackData, 'contents'):
            return ERROR_INVALID_PARAMETER
            
        path = callbackData.contents.FilePathName
        print(f"Getting placeholder info for: '{path}'")
        
        # Get the item
        if path:
            item = virtual_fs.get_item(path)
        else:
            item = virtual_fs
        
        if not item:
            print(f"Item not found: '{path}'")
            return ERROR_FILE_NOT_FOUND
        
        # Create placeholder info
        PlaceholderInfo = ProjectedFS.PRJ_PLACEHOLDER_INFO()
        PlaceholderInfo.FileBasicInfo = ProjectedFS.PRJ_FILE_BASIC_INFO()
        
        if isinstance(item, VirtualDirectory):
            PlaceholderInfo.FileBasicInfo.IsDirectory = True
            PlaceholderInfo.FileBasicInfo.FileSize = 0
            print(f"  -> Directory")
        else:  # VirtualFile
            PlaceholderInfo.FileBasicInfo.IsDirectory = False
            PlaceholderInfo.FileBasicInfo.FileSize = item.size
            print(f"  -> File, size={item.size}")
        
        # Write placeholder info
        result = ProjectedFS.PrjWritePlaceholderInfo(
            callbackData.contents.NamespaceVirtualizationContext,
            path,
            PlaceholderInfo,
            ctypes.sizeof(PlaceholderInfo)
        )
        
        if result != S_OK:
            print(f"Failed to write placeholder info: {hex(result)}")
        
        return result
        
    except Exception as e:
        print(f"Error in getplaceholder_info_cb: {e}")
        import traceback
        traceback.print_exc()
        return ERROR_FILE_NOT_FOUND

@ProjectedFS.PRJ_GET_FILE_DATA_CB
def getfiledata_cb(callbackData, byteOffset, length):
    """Get file data for a virtual file"""
    try:
        if not hasattr(callbackData, 'contents'):
            return ERROR_INVALID_PARAMETER
            
        path = callbackData.contents.FilePathName
        print(f"Getting file data for: '{path}' (offset={byteOffset}, length={length})")
        
        # Get the file
        item = virtual_fs.get_item(path)
        
        if not item or isinstance(item, VirtualDirectory):
            print(f"Not a file: '{path}'")
            return ERROR_FILE_NOT_FOUND
        
        # Check bounds
        if byteOffset >= item.size:
            print(f"Offset beyond file size")
            return S_OK  # Nothing to write
        
        # Calculate how much to write
        bytes_to_write = min(length, item.size - byteOffset)
        print(f"  Writing {bytes_to_write} bytes")
        
        # Allocate buffer
        writeBuffer = ProjectedFS.PrjAllocateAlignedBuffer(
            callbackData.contents.NamespaceVirtualizationContext,
            bytes_to_write
        )
        
        if not writeBuffer:
            print("Failed to allocate buffer")
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
        
        if result != S_OK:
            print(f"Failed to write file data: {hex(result)}")
        
        return result
        
    except Exception as e:
        print(f"Error in getfiledata_cb: {e}")
        import traceback
        traceback.print_exc()
        return E_INVALIDARG

def main():
    # Create instance GUID
    instanceId = ProjectedFS.GUID()
    instanceId.Data1 = 0xD137C01A
    instanceId.Data2 = 0xBAAD
    instanceId.Data3 = 0xCAA7
    
    # Create root directory if it doesn't exist
    if not os.path.exists(virt_root):
        print(f"{virt_root} does not exist yet, creating..")
        os.mkdir(virt_root)
    
    if not os.path.isdir(virt_root):
        print(f"{virt_root} is not a directory, exiting..")
        sys.exit(1)
    
    # Clear directory contents if not empty
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
        print("Make sure the directory is empty or was previously used as a ProjFS root.")
        sys.exit(1)
    
    # Set up callbacks
    callbackTable = ProjectedFS.PRJ_CALLBACKS()
    callbackTable.StartDirectoryEnumerationCallback = startdir_enum_cb
    callbackTable.EndDirectoryEnumerationCallback = enddir_enum_cb
    callbackTable.GetDirectoryEnumerationCallback = getdir_enum_cb
    callbackTable.GetPlaceholderInfoCallback = getplaceholder_info_cb
    callbackTable.GetFileDataCallback = getfiledata_cb
    
    print("Starting virtualization instance")
    print("\nVirtual file system structure:")
    print("  /readme.txt")
    print("  /test.py")
    print("  /Documents/")
    print("    ├── report.txt")
    print("    ├── notes.md")
    print("    └── Projects/")
    print("        ├── project1.txt")
    print("        └── project2.txt")
    print("  /Source/")
    print("    ├── main.cpp")
    print("    ├── utils.cpp")
    print("    └── Headers/")
    print("        ├── common.h")
    print("        └── utils.h")
    print("  /Data/")
    print("    ├── config.json")
    print("    ├── data.csv")
    print("    └── Cache/")
    print("        ├── temp.dat")
    print("        └── Logs/")
    print("            └── app.log")
    print(f"\nYou can now browse to {virt_root} to see the virtual files!")
    print("\n" + "="*50)
    print("Debug output will appear below:")
    print("="*50 + "\n")
    
    # Start virtualization
    instanceHandle = ProjectedFS.PRJ_NAMESPACE_VIRTUALIZATION_CONTEXT()
    result = ProjectedFS.PrjStartVirtualizing(virt_root, callbackTable, None, None, instanceHandle)
    if result != S_OK:
        print(f"Error starting virtualization. Error code: {hex(result)}")
        sys.exit(1)
    
    try:
        input("\nPress Enter to stop the virtual file system...")
    except KeyboardInterrupt:
        print("\nStopping...")
    
    # Stop virtualization
    ProjectedFS.PrjStopVirtualizing(instanceHandle)
    print("Stopped virtualization instance")

if __name__ == "__main__":
    main()
    
