# Read-only Windows host evidence collector for Runner MCP issue #195.
# Does not change BIOS, Hyper-V, storage, services, or Runner MCP state.

$ErrorActionPreference = "Continue"

function Section([string]$Name) {
    Write-Host ""
    Write-Host "=== $Name ==="
}

Section "SYSTEM"
Get-Date -Format o
Get-CimInstance Win32_OperatingSystem |
    Select-Object Caption, Version, BuildNumber, LastBootUpTime
Get-CimInstance Win32_ComputerSystem |
    Select-Object Manufacturer, Model, TotalPhysicalMemory, HypervisorPresent

Section "CPU / BIOS / BOARD"
Get-CimInstance Win32_Processor |
    Select-Object Name, Manufacturer, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed
Get-CimInstance Win32_BIOS |
    Select-Object Manufacturer, SMBIOSBIOSVersion, ReleaseDate
Get-CimInstance Win32_BaseBoard |
    Select-Object Manufacturer, Product, Version

Section "CPU MICROCODE REGISTRY EVIDENCE"
try {
    $rev = (Get-ItemProperty 'HKLM:\HARDWARE\DESCRIPTION\System\CentralProcessor\0' -Name 'Update Revision').'Update Revision'
    if ($rev -is [byte[]]) {
        "Update Revision raw hex: " + (($rev | ForEach-Object { $_.ToString('X2') }) -join '')
    } else {
        "Update Revision: $rev"
    }
} catch {
    "Microcode registry value unavailable: $($_.Exception.GetType().Name)"
}

Section "PHYSICAL MEMORY"
Get-CimInstance Win32_PhysicalMemory |
    Select-Object DeviceLocator, BankLabel, Manufacturer, PartNumber, Capacity, Speed, ConfiguredClockSpeed, ConfiguredVoltage

Section "WINDOWS MEMORY DIAGNOSTIC RESULTS"
try {
    Get-WinEvent -FilterHashtable @{
        LogName='System'
        ProviderName='Microsoft-Windows-MemoryDiagnostics-Results'
    } -MaxEvents 20 |
        Select-Object TimeCreated, Id, LevelDisplayName, Message
} catch {
    "No MemoryDiagnostics-Results events available."
}

Section "WHEA HARDWARE ERRORS - LAST 30 DAYS"
try {
    Get-WinEvent -FilterHashtable @{
        LogName='System'
        ProviderName='Microsoft-Windows-WHEA-Logger'
        StartTime=(Get-Date).AddDays(-30)
    } -MaxEvents 200 |
        Select-Object TimeCreated, Id, LevelDisplayName, Message
} catch {
    "No WHEA events returned."
}

Section "STORAGE / FILESYSTEM ERRORS - LAST 30 DAYS"
$providers = @(
    'disk',
    'Ntfs',
    'stornvme',
    'storahci',
    'volmgr',
    'Microsoft-Windows-StorPort'
)
foreach ($provider in $providers) {
    try {
        Get-WinEvent -FilterHashtable @{
            LogName='System'
            ProviderName=$provider
            StartTime=(Get-Date).AddDays(-30)
        } -MaxEvents 100 |
            Where-Object { $_.Level -le 3 } |
            Select-Object TimeCreated, ProviderName, Id, LevelDisplayName, Message
    } catch {
        # Some providers may not exist on every system.
    }
}

Section "PHYSICAL DISKS"
try {
    Get-PhysicalDisk |
        Select-Object FriendlyName, MediaType, BusType, HealthStatus, OperationalStatus, Size
} catch {
    "Get-PhysicalDisk unavailable."
}

Section "STORAGE RELIABILITY COUNTERS"
try {
    Get-PhysicalDisk | ForEach-Object {
        $disk = $_
        try {
            $r = $disk | Get-StorageReliabilityCounter
            [pscustomobject]@{
                FriendlyName = $disk.FriendlyName
                Temperature = $r.Temperature
                ReadErrorsTotal = $r.ReadErrorsTotal
                ReadErrorsUncorrected = $r.ReadErrorsUncorrected
                WriteErrorsTotal = $r.WriteErrorsTotal
                WriteErrorsUncorrected = $r.WriteErrorsUncorrected
                Wear = $r.Wear
                PowerOnHours = $r.PowerOnHours
            }
        } catch {
            [pscustomobject]@{
                FriendlyName = $disk.FriendlyName
                Note = 'Reliability counters unavailable'
            }
        }
    } | Format-Table -AutoSize
} catch {
    "Storage reliability counters unavailable."
}

Section "F: VOLUME"
try {
    Get-Volume -DriveLetter F |
        Select-Object DriveLetter, FileSystem, FileSystemLabel, HealthStatus, OperationalStatus, Size, SizeRemaining
    Get-Partition -DriveLetter F |
        Select-Object DiskNumber, PartitionNumber, DriveLetter, Size
} catch {
    "F: volume/partition details unavailable."
}

Section "AIFORDABLE-LAB HYPER-V"
try {
    Get-VM -Name 'aifordable-lab' |
        Select-Object Name, State, ProcessorCount, MemoryAssigned, MemoryDemand, DynamicMemoryEnabled
    Get-VMHardDiskDrive -VMName 'aifordable-lab' |
        Select-Object VMName, ControllerType, ControllerNumber, ControllerLocation, Path
    Get-VMHardDiskDrive -VMName 'aifordable-lab' | ForEach-Object {
        if ($_.Path) {
            Get-VHD -Path $_.Path |
                Select-Object Path, VhdType, VhdFormat, FileSize, Size, MinimumSize, FragmentationPercentage
        }
    }
} catch {
    "Hyper-V VM details unavailable: $($_.Exception.GetType().Name)"
}

Section "RECENT HYPER-V ERRORS - LAST 7 DAYS"
$hvLogs = @(
    'Microsoft-Windows-Hyper-V-VMMS-Admin',
    'Microsoft-Windows-Hyper-V-Worker-Admin'
)
foreach ($log in $hvLogs) {
    try {
        Get-WinEvent -FilterHashtable @{
            LogName=$log
            StartTime=(Get-Date).AddDays(-7)
        } -MaxEvents 100 |
            Where-Object { $_.Level -le 3 } |
            Select-Object TimeCreated, LogName, Id, LevelDisplayName, Message
    } catch {
    }
}

Section "IMPORTANT"
"Read-only evidence collection complete."
"A clean Windows event log does NOT prove RAM or CPU health."
"Before Runner MCP activation: verify latest motherboard BIOS with Intel microcode 0x12F+ and Intel Default Settings, then perform an offline physical RAM test."
