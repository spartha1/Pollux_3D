# Script to check SWIG setup
$ErrorActionPreference = "Stop"

Write-Host "Checking SWIG installation..."

# Function to get version from swig executable
function Get-SwigVersion {
    param($Path)
    try {
        Write-Host "Attempting to run: $Path -version"

        # Use Start-Process to capture output reliably
        $pinfo = New-Object System.Diagnostics.ProcessStartInfo
        $pinfo.FileName = $Path
        $pinfo.Arguments = "-version"
        $pinfo.RedirectStandardOutput = $true
        $pinfo.RedirectStandardError = $true
        $pinfo.UseShellExecute = $false
        $pinfo.WorkingDirectory = Split-Path -Parent $Path

        $p = New-Object System.Diagnostics.Process
        $p.StartInfo = $pinfo

        Write-Host "Starting SWIG process..."
        $p.Start() | Out-Null

        $stdout = $p.StandardOutput.ReadToEnd()
        $stderr = $p.StandardError.ReadToEnd()
        $p.WaitForExit()

        Write-Host "SWIG process exit code: $($p.ExitCode)"
        Write-Host "Standard output:"
        if ($stdout) { Write-Host $stdout }
        Write-Host "Standard error:"
        if ($stderr) { Write-Host $stderr }

        # Search for version in both stdout and stderr
        $output = $stdout + $stderr
        if ($p.ExitCode -eq 0) {
            if ($output -match "SWIG Version (\d+\.\d+\.\d+)") {
                Write-Host "Successfully parsed version: $($matches[1])"
                return $matches[1]
            }
            Write-Host "Warning: Could not find version string in output"
            Write-Host "Raw output was:"
            Write-Host $output
        } else {
            Write-Host "SWIG process failed with exit code: $($p.ExitCode)"
        }
        return $null

    } catch {
        Write-Host "Error running SWIG:"
        Write-Host "Exception type: $($_.Exception.GetType().FullName)"
        Write-Host "Message: $($_.Exception.Message)"
        Write-Host "Stack trace:"
        Write-Host $_.Exception.StackTrace
        return $null
    }
}

# Function to copy SWIG interface files from conda
function Copy-SwigFiles {
    param($CondaPrefix, $SwigRoot)

    Write-Host "Looking for SWIG files..."

    # Define essential files to check
    $essentialFiles = @(
        "swig.swg",
        "python.swg",
        "typemaps.i",
        "std_string.i",
        "exception.i"
    )

    # First check if files already exist in swigwin-4.2.1\Lib
    $swigLib = Join-Path $SwigRoot "Lib"
    if (-not (Test-Path $swigLib)) {
        New-Item -Path $swigLib -ItemType Directory -Force | Out-Null
    }

    # Check original SWIG directory for files
    $originalSwigLib = Join-Path $SwigRoot "Lib"
    $allFilesExist = $true

    Write-Host "Checking for files in original SWIG directory: $originalSwigLib"
    foreach ($file in $essentialFiles) {
        $filePath = Join-Path $originalSwigLib $file
        if (-not (Test-Path $filePath)) {
            $allFilesExist = $false
            Write-Host "Missing: $file"
        }
    }

    # If all files exist in original location, just move them
    if ($allFilesExist) {
        Write-Host "Found all required files in original SWIG directory"
        return
    }

    # Look for files in conda environment
    Write-Host "Looking for SWIG files in conda environment..."
    $condaLibDir = Join-Path $CondaPrefix "Library"
    $condaSwigShare = Join-Path $condaLibDir "share\swig\4.2.1"

    if (Test-Path $condaSwigShare) {
        Write-Host "Found SWIG files in conda environment"

        # First copy everything from the root of swig share
        Get-ChildItem -Path $condaSwigShare -File | ForEach-Object {
            Write-Host "Copying file: $($_.Name)"
            Copy-Item -Path $_.FullName -Destination $swigLib -Force
        }

        # Then copy all subdirectories
        Get-ChildItem -Path $condaSwigShare -Directory | ForEach-Object {
            $destDir = Join-Path $swigLib $_.Name
            Write-Host "Copying directory: $($_.Name)"
            Copy-Item -Path $_.FullName -Destination $destDir -Recurse -Force
        }
    } else {
        # If files don't exist in conda, download them from the SWIG GitHub repository
        Write-Host "Downloading SWIG interface files from GitHub..."
        $tempFile = Join-Path $env:TEMP "swig-4.2.1.zip"
        $tempDir = Join-Path $env:TEMP "swig-4.2.1-extract"
        $webClient = New-Object System.Net.WebClient
        $url = "https://github.com/swig/swig/archive/refs/tags/v4.2.1.zip"

        try {
            if (Test-Path $tempDir) {
                Remove-Item $tempDir -Recurse -Force
            }
            New-Item -Path $tempDir -ItemType Directory -Force | Out-Null

            Write-Host "Downloading from $url..."
            $webClient.DownloadFile($url, $tempFile)
            Write-Host "Download complete. Extracting..."

            # Extract the zip file
            Add-Type -AssemblyName System.IO.Compression.FileSystem
            [System.IO.Compression.ZipFile]::ExtractToDirectory($tempFile, $tempDir)

            # Get the actual extracted directory
            $extractedDir = Get-ChildItem -Path $tempDir -Directory | Select-Object -First 1

            Write-Host "Extracted directory: $($extractedDir.FullName)"

            # Define source directories
            $libSourceDir = Join-Path $extractedDir.FullName "Lib"
            $srcDir = Join-Path $extractedDir.FullName "Source"

            # Create all required directories first
            $requiredDirs = @("python", "std", "typemaps")
            foreach ($dir in $requiredDirs) {
                $dirPath = Join-Path $swigLib $dir
                if (-not (Test-Path $dirPath)) {
                    New-Item -Path $dirPath -ItemType Directory -Force | Out-Null
                }
            }

            # Map of essential files to their possible locations
            $fileLocations = @{
                "swig.swg" = @(
                    (Join-Path $libSourceDir "swig.swg"),
                    (Join-Path $srcDir "Lib/swig.swg")
                )
                "python.swg" = @(
                    (Join-Path $libSourceDir "python/python.swg"),
                    (Join-Path $srcDir "Lib/python/python.swg")
                )
                "typemaps.i" = @(
                    (Join-Path $libSourceDir "typemaps/typemaps.i"),
                    (Join-Path $srcDir "Lib/typemaps/typemaps.i")
                )
                "std_string.i" = @(
                    (Join-Path $libSourceDir "std/std_string.i"),
                    (Join-Path $srcDir "Lib/std/std_string.i")
                )
                "exception.i" = @(
                    (Join-Path $libSourceDir "exception.i"),
                    (Join-Path $srcDir "Lib/exception.i")
                )
            }

            # Directories already created above

            # Copy files from their locations
            foreach ($file in $fileLocations.Keys) {
                $found = $false
                foreach ($location in $fileLocations[$file]) {
                    if (Test-Path $location) {
                        Write-Host "Found $file at: $location"

                        # Determine destination path based on file type
                        $destPath = switch -Wildcard ($file) {
                            "python.swg" { Join-Path $swigLib "python/$file" }
                            "std_*.i" { Join-Path $swigLib "std/$file" }
                            default { Join-Path $swigLib $file }
                        }

                        Write-Host "Copying to: $destPath"
                        Copy-Item -Path $location -Destination $destPath -Force
                        $found = $true
                        break
                    }
                }
                if (-not $found) {
                    Write-Warning "Could not find $file in any expected location"
                }
            }

            # Copy additional useful directories and their contents
            $usefulDirs = @("python", "std", "typemaps")
            foreach ($dir in $usefulDirs) {
                $srcPaths = @(
                    (Join-Path $libSourceDir $dir),
                    (Join-Path $srcDir "Lib/$dir")
                )

                foreach ($srcPath in $srcPaths) {
                    if (Test-Path $srcPath) {
                        Write-Host "Found $dir directory at: $srcPath"
                        $destDir = Join-Path $swigLib $dir
                        Write-Host "Copying directory $dir to: $destDir"
                        Copy-Item -Path "$srcPath\*" -Destination $destDir -Recurse -Force
                        break
                    }
                }
            }

            # Special handling for typemaps.i if not found
            if (-not (Test-Path (Join-Path $swigLib "typemaps/typemaps.i"))) {
                Write-Host "Looking for typemaps.i in alternative locations..."
                $typemapsFile = Get-ChildItem -Path $tempDir -Recurse -Filter "typemaps.i" | Select-Object -First 1
                if ($typemapsFile) {
                    Write-Host "Found typemaps.i at: $($typemapsFile.FullName)"
                    Copy-Item -Path $typemapsFile.FullName -Destination (Join-Path $swigLib "typemaps/typemaps.i") -Force
                }
            }

            Write-Host "Cleanup temporary files..."
            Remove-Item $tempFile -Force
            Remove-Item $tempDir -Recurse -Force

        } catch {
            Write-Error "Failed to download or extract SWIG files: $_"
            exit 1
        }
    }

    # Verify essential files
    Write-Host "`nVerifying essential SWIG files:"
    $missingFiles = @()
    foreach ($file in $essentialFiles) {
        # Determine the correct path based on file type
        $filePath = switch -Wildcard ($file) {
            "python.swg" { Join-Path $swigLib "python/$file" }
            "std_*.i" { Join-Path $swigLib "std/$file" }
            "typemaps.i" { Join-Path $swigLib "typemaps/$file" }
            default { Join-Path $swigLib $file }
        }
        $exists = Test-Path $filePath
        Write-Host "$file`: $exists (at $filePath)"
        if ($exists) {
            $fileItem = Get-Item $filePath
            Write-Host "  Size: $($fileItem.Length) bytes"
            Write-Host "  Last Write: $($fileItem.LastWriteTime)"
            Write-Host "  Parent Directory: $($fileItem.Directory.FullName)"
        }
        if (-not $exists) {
            $missingFiles += $file
        }
    }

    if ($missingFiles.Count -gt 0) {
        Write-Error "Missing essential SWIG files: $($missingFiles -join ', ')"
        exit 1
    }
}

# Check for local swigwin-4.2.1
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$swigPath = Join-Path $scriptDir "swigwin-4.2.1\swig.exe"
$swigPath = [System.IO.Path]::GetFullPath($swigPath)

Write-Host "Looking for SWIG at: $swigPath"
if (-not (Test-Path $swigPath)) {
    Write-Error "SWIG not found at: $swigPath. Please ensure swigwin-4.2.1 is extracted in the correct location."
    exit 1
}

Write-Host "Found SWIG executable, checking version..."
Write-Host "File exists: $(Test-Path $swigPath)"
Write-Host "File size: $((Get-Item $swigPath).Length) bytes"
Write-Host "File last write time: $((Get-Item $swigPath).LastWriteTime)"

$version = Get-SwigVersion $swigPath
if ($null -eq $version) {
    Write-Error "Failed to get SWIG version. Please ensure swigwin-4.2.1 is correctly installed."
    exit 1
}
if ($version -ne "4.2.1") {
    Write-Error "Incorrect SWIG version. Expected 4.2.1 but found: $version"
    exit 1
}

# Get conda environment info and set up paths
$condaInfo = conda info --json | ConvertFrom-Json
$condaPrefix = $condaInfo.active_prefix
if (-not $condaPrefix) { $condaPrefix = $condaInfo.root_prefix }

Write-Host "`nConda environment:"
Write-Host "Prefix: $condaPrefix"

# Set up SWIG paths for CMake
$swigRoot = Join-Path $scriptDir "swigwin-4.2.1"
$swigRoot = [System.IO.Path]::GetFullPath($swigRoot)
$swigLib = Join-Path $swigRoot "Lib"

# Copy or verify SWIG interface files
Copy-SwigFiles -CondaPrefix $condaPrefix -SwigRoot $swigRoot

Write-Host "`nFound SWIG 4.2.1:"
Write-Host "Path: $swigPath"
Write-Host "Version: $version"

Write-Host "`nSWIG paths for CMake:"
Write-Host "SWIG_EXECUTABLE: $swigPath"
Write-Host "SWIG_DIR: $swigLib"
Write-Host "SWIG_LIB: $swigLib"

Write-Host "`nVerifying paths exist:"
@($swigPath, $swigLib) | ForEach-Object {
    $item = Get-Item $_ -ErrorAction SilentlyContinue
    Write-Host "$_`: $(Test-Path $_) $(if($item){"($(if($item.PSIsContainer){'Directory'}else{'File'}))"} else {'(Not Found)'})"
}

# Export variables for use in the build script
$script:swigPath = $swigPath
$script:swigShare = $swigLib
