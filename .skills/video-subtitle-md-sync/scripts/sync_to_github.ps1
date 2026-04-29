[CmdletBinding()]
param(
  [Parameter(Mandatory = $false)]
  [string]$RepoRoot = ".",

  [Parameter(Mandatory = $false)]
  [string]$Message,

  [Parameter(Mandatory = $false)]
  [string]$Branch
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-Branch([string]$RequestedBranch) {
  if (-not [string]::IsNullOrWhiteSpace($RequestedBranch)) {
    return $RequestedBranch.Trim()
  }

  $currentBranch = git branch --show-current
  if (-not [string]::IsNullOrWhiteSpace($currentBranch)) {
    return $currentBranch.Trim()
  }

  return "HEAD"
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

Push-Location $root
try {
  git add --all

  git diff --cached --quiet
  if ($LASTEXITCODE -eq 0) {
    Write-Host "No changes to sync."
    exit 0
  }

  $branchToPush = Resolve-Branch $Branch
  $commitMessage = $Message
  if ([string]::IsNullOrWhiteSpace($commitMessage)) {
    $commitMessage = "Sync transcript update"
  }

  git commit -m $commitMessage

  if ($branchToPush -eq "HEAD") {
    git push origin HEAD
  } else {
    git push origin $branchToPush
  }

  Write-Host "Synced to GitHub on branch '$branchToPush'."
} finally {
  Pop-Location
}
