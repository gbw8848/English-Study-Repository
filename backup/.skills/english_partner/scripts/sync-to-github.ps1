[CmdletBinding()]
param(
  [Parameter(Mandatory = $false)]
  [string]$Date,

  [Parameter(Mandatory = $false)]
  [string]$Message,

  [Parameter(Mandatory = $false)]
  [string]$Branch = "main",

  [Parameter(Mandatory = $false)]
  [string]$RepoRoot = "."
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-IsoDate([string]$InputDate) {
  if ([string]::IsNullOrWhiteSpace($InputDate)) {
    return (Get-Date).ToString("yyyy-MM-dd")
  }

  try {
    $parsed = [DateTime]::ParseExact($InputDate.Trim(), "yyyy-MM-dd", $null)
    return $parsed.ToString("yyyy-MM-dd")
  } catch {
    throw "Invalid -Date '$InputDate'. Expected format yyyy-MM-dd."
  }
}

function Ensure-GitRepository([string]$RootPath) {
  Push-Location $RootPath
  try {
    git rev-parse --is-inside-work-tree 1>$null
    if ($LASTEXITCODE -ne 0) {
      throw "Current directory is not a git repository: $RootPath"
    }
  } finally {
    Pop-Location
  }
}

$root = (Resolve-Path $RepoRoot).Path
Ensure-GitRepository -RootPath $root

$isoDate = Resolve-IsoDate $Date
$commitMessage = $Message
if ([string]::IsNullOrWhiteSpace($commitMessage)) {
  $commitMessage = "Auto-summary: English study session analysis for $isoDate"
}

Push-Location $root
try {
  git add .

  git diff --cached --quiet
  if ($LASTEXITCODE -eq 0) {
    Write-Host "No changes to sync."
    exit 0
  }

  git commit -m $commitMessage
  git push origin $Branch
  Write-Host "Synced to GitHub on branch '$Branch'."
} finally {
  Pop-Location
}
