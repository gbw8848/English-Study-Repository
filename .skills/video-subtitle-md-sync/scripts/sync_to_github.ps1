[CmdletBinding()]
param(
  [Parameter(Mandatory = $false)]
  [string]$RepoRoot = ".",

  [Parameter(Mandatory = $false)]
  [string]$Message,

  [Parameter(Mandatory = $false)]
  [string]$Branch,

  [Parameter(Mandatory = $false)]
  [switch]$SkipEncodingCheck
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

function Ensure-GitRepository {
  param(
    [Parameter(Mandatory = $true)]
    [string]$RootPath
  )

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

function Ensure-EncodingOk {
  param(
    [Parameter(Mandatory = $true)]
    [string]$RootPath,

    [Parameter(Mandatory = $false)]
    [switch]$SkipEncodingCheck
  )

  if ($SkipEncodingCheck) {
    return
  }

  $checkScript = Join-Path $PSScriptRoot "check_review_encoding.py"
  if (-not (Test-Path -LiteralPath $checkScript)) {
    throw "Missing encoding check script: $checkScript"
  }

  py $checkScript --repo-root $RootPath
  if ($LASTEXITCODE -ne 0) {
    throw "Encoding check failed. Fix garbled Chinese before syncing to GitHub."
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

  Ensure-EncodingOk -RootPath $root -SkipEncodingCheck:$SkipEncodingCheck

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
