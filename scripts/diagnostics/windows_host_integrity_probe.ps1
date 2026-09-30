#Requires -Version 5.1
$ErrorActionPreference = "Continue"

# Read-only host diagnostic for Runner MCP issue #194.
# No BIOS/settings/service/storage changes are made.

function Section([string]$Name) {
    Write-Host ""
    Write-Host "=== $Name ==="
}

Section "TIMESTAMP"
Get-Date -Format o

Section "CPU"
Get-CimInstance Win32_Processor |
    Select-Object Name, Manufacturer, ProcessorId, NumberOfCores, NumberOfLogicalProcessors,
                  MaxClockSpeed, CurrentClockSpeed |
    Format-List

Section "MOTHERBOARD / BIOS"
Get-CimInstance Win32_BaseBoard |
    Select-Object Manufacturer, Product, Version |
    Format-List
Get-CimInstance Win32_BIOS |
    Select-Object Manufacturer, SMBIOSBIOSVersion,
        @{Name="ReleaseDate";Expression={$_.ReleaseDate.ToString("o")}} |
    Format-List

Section "INTEL MICROCODE REGISTRY"
$cpuKey = "HKLM\HARDWARE\DESCRIPTION\System\CentralProcessor\0"
foreach ($value in @(
    "Identifier",
    "ProcessorNameString",
    "Update Revision",
    "Previous Update Revision",
    "Firmware Record Version",
    "Previous Record Version",
    "Current Record Version",
    "Preferred Record Version",
    "Patch Configuration Used",
    "Update Status",
    "Update Environment"
)) {
    Write-Host "--- $value ---"
    & reg.exe query $cpuKey /v $value 2>&1
}

Section "PHYSICAL MEMORY"
Get-CimInstance Win32_PhysicalMemory |
    Select-Object BankLabel, Manufacturer, PartNumber,
        @{Name="CapacityGiB";Expression={[math]::Round($_.Capacity / 1GB, 2)}},
        Speed, ConfiguredClockSpeed |
    Format-Table -AutoSize

Section "WHEA HARDWARE ERRORS - LAST 90 DAYS"
$whea = Get-WinEvent -FilterHashtable @{
    LogName = "System"
    ProviderName = "Microsoft-Windows-WHEA-Logger"
    StartTime = (Get-Date).AddDays(-90)
} -ErrorAction SilentlyContinue

if ($whea) {
    $whea |
        Select-Object TimeCreated, Id, LevelDisplayName, Message |
        Format-List
} else {
    Write-Host "No WHEA-Logger events found in the last 90 days."
}

Section "SYSTEM CRITICAL / HARDWARE-RELATED EVENTS - LAST 30 DAYS"
Get-WinEvent -FilterHashtable @{
    LogName = "System"
    Level = 1,2
    StartTime = (Get-Date).AddDays(-30)
} -ErrorAction SilentlyContinue |
    Where-Object {
        $_.ProviderName -match "WHEA|Kernel-Power|Hyper-V|Disk|stornvme|storahci|Ntfs|volmgr"
    } |
    Select-Object -First 200 TimeCreated, ProviderName, Id, LevelDisplayName, Message |
    Format-List

Section "PHYSICAL DISK HEALTH"
Get-PhysicalDisk -ErrorAction SilentlyContinue |
    Select-Object FriendlyName, MediaType, BusType, HealthStatus, OperationalStatus,
                  @{Name="SizeGiB";Expression={[math]::Round($_.Size / 1GB, 1)}} |
    Format-Table -AutoSize

Section "STORAGE RELIABILITY COUNTERS"
Get-PhysicalDisk -ErrorAction SilentlyContinue | ForEach-Object {
    $disk = $_
    try {
        $counter = $disk | Get-StorageReliabilityCounter -ErrorAction Stop
        [pscustomobject]@{
            FriendlyName = $disk.FriendlyName
            Temperature = $counter.Temperature
            ReadErrorsTotal = $counter.ReadErrorsTotal
            ReadErrorsUncorrected = $counter.ReadErrorsUncorrected
            WriteErrorsTotal = $counter.WriteErrorsTotal
            WriteErrorsUncorrected = $counter.WriteErrorsUncorrected
            Wear = $counter.Wear
            PowerOnHours = $counter.PowerOnHours
        }
    }
    catch {
        [pscustomobject]@{
            FriendlyName = $disk.FriendlyName
            Temperature = "<unavailable>"
            ReadErrorsTotal = "<unavailable>"
            ReadErrorsUncorrected = "<unavailable>"
            WriteErrorsTotal = "<unavailable>"
            WriteErrorsUncorrected = "<unavailable>"
            Wear = "<unavailable>"
            PowerOnHours = "<unavailable>"
        }
    }
} | Format-Table -AutoSize

Section "HYPER-V AIFORDABLE-LAB"
if (Get-Command Get-VM -ErrorAction SilentlyContinue) {
    $vm = Get-VM -Name "aifordable-lab" -ErrorAction SilentlyContinue
    if ($vm) {
        $vm | Select-Object Name, State, Generation, ProcessorCount,
            @{Name="MemoryAssignedGiB";Expression={[math]::Round($_.MemoryAssigned / 1GB, 2)}},
            DynamicMemoryEnabled, AutomaticCheckpointsEnabled, Version |
            Format-List

        Get-VMProcessor -VMName "aifordable-lab" |
            Select-Object Count, CompatibilityForMigrationEnabled,
                CompatibilityForOlderOperatingSystemsEnabled,
                ExposeVirtualizationExtensions, Maximum, Reserve, RelativeWeight |
            Format-List

        Get-VMMemory -VMName "aifordable-lab" |
            Select-Object DynamicMemoryEnabled,
                @{Name="StartupGiB";Expression={[math]::Round($_.Startup / 1GB, 2)}},
                @{Name="MinimumGiB";Expression={[math]::Round($_.Minimum / 1GB, 2)}},
                @{Name="MaximumGiB";Expression={[math]::Round($_.Maximum / 1GB, 2)}},
                Buffer, Priority |
            Format-List

        Get-VMHardDiskDrive -VMName "aifordable-lab" |
            Select-Object ControllerType, ControllerNumber, ControllerLocation, Path |
            Format-List

        Get-VMSnapshot -VMName "aifordable-lab" -ErrorAction SilentlyContinue |
            Select-Object Name, SnapshotType, CreationTime |
            Format-Table -AutoSize
    }
    else {
        Write-Host "VM aifordable-lab not found."
    }
}
else {
    Write-Host "Hyper-V PowerShell module is unavailable."
}

Section "END"
Write-Host "Read-only host probe complete."
