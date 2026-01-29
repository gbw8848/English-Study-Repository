[CmdletBinding(SupportsShouldProcess = $true)]
param(
  [Parameter(Mandatory = $false)]
  [string]$Date,

  [Parameter(Mandatory = $false)]
  [string]$Summary,

  [Parameter(Mandatory = $false)]
  [switch]$Force,

  [Parameter(Mandatory = $false)]
  [switch]$Commit,

  [Parameter(Mandatory = $false)]
  [switch]$Push,

  [Parameter(Mandatory = $false)]
  [string]$Branch = "main"
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

function Get-Newline([string]$Text) {
  if ($Text -match "\r\n") { return "`r`n" }
  return "`n"
}

function Write-Utf8NoBom([string]$Path, [string]$Content) {
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Content, $utf8NoBom)
}

function Get-ReviewPlanContent([string]$RepoRoot, [string]$IsoDate) {
  $templatePath = Join-Path $RepoRoot "templates/Review_Plan_TEMPLATE.md"

  if (Test-Path $templatePath) {
    $template = Get-Content -Path $templatePath -Raw -Encoding UTF8
    return $template.Replace("{{DATE}}", $IsoDate)
  }

  @(
    "# English Review Plan - $IsoDate"
    ""
    "## Core Vocabulary"
    ""
    "## Grammar Review"
    ""
    "## Useful Phrases"
    ""
    "## Pronunciation Tips"
    ""
  ) -join "`n"
}

function Update-ReadmeToc(
  [string]$RepoRoot,
  [string]$IsoDate,
  [string]$PlanFileName,
  [string]$SummaryText
) {
  $readmePath = Join-Path $RepoRoot "README.md"
  if (-not (Test-Path $readmePath)) {
    Write-Verbose "README.md not found, skipping README update."
    return $false
  }

  $readme = Get-Content -Path $readmePath -Raw -Encoding UTF8
  if ($readme.Contains("($PlanFileName)")) {
    Write-Verbose "README already contains link to $PlanFileName, skipping."
    return $false
  }

  $summary = $SummaryText
  if ([string]::IsNullOrWhiteSpace($summary)) {
    $summary = "(TBD)"
  }
  $summary = ($summary -replace "\r\n|\n|\r", " ").Trim()

  $mu = [char]0x76EE
  $lu = [char]0x5F55
  $tocHeaderLine = "## " + $mu + $lu

  $newline = Get-Newline $readme
  $lines = $readme -split "\r\n|\n|\r"

  $fu = [char]0x590D
  $xi = [char]0x4E60
  $ji = [char]0x8BA1
  $hua = [char]0x5212
  $reviewPlanLabel = "" + $fu + $xi + $ji + $hua

  $outLines = New-Object System.Collections.Generic.List[string]
  $inserted = $false
  for ($i = 0; $i -lt $lines.Length; $i++) {
    $line = $lines[$i]
    $outLines.Add($line)
    if (-not $inserted -and $line.Trim() -eq $tocHeaderLine) {
      $outLines.Add("- [$IsoDate $reviewPlanLabel]($PlanFileName): $summary")
      $inserted = $true
    }
  }

  if (-not $inserted) {
    throw "Could not find TOC header line '$tocHeaderLine' in README.md."
  }

  $updated = ($outLines -join $newline)
  if ($updated -eq $readme) { return $false }

  Write-Utf8NoBom -Path $readmePath -Content $updated
  return $true
}

function Invoke-GitCommitAndPush(
  [string]$RepoRoot,
  [string]$IsoDate,
  [string]$PlanFileName,
  [string]$BranchName,
  [switch]$DoPush
) {
  Push-Location $RepoRoot
  try {
    git add -- $PlanFileName README.md | Out-Null

    git diff --cached --quiet
    if ($LASTEXITCODE -eq 0) {
      Write-Verbose "No changes staged; skipping commit/push."
      return
    }

    git commit -m "Add review plan $IsoDate" | Out-Null
    if ($DoPush) {
      git push origin $BranchName | Out-Null
    }
  } finally {
    Pop-Location
  }
}

$isoDate = Resolve-IsoDate $Date
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$planFileName = "Review_Plan_$isoDate.md"
$planPath = Join-Path $repoRoot $planFileName

$planCreatedOrOverwritten = $false
if ((Test-Path $planPath) -and (-not $Force)) {
  Write-Host "Exists: $planFileName (use -Force to overwrite)"
} else {
  $content = Get-ReviewPlanContent -RepoRoot $repoRoot -IsoDate $isoDate
  if ($PSCmdlet.ShouldProcess($planPath, "Write review plan")) {
    Write-Utf8NoBom -Path $planPath -Content $content
    $planCreatedOrOverwritten = $true
  }
}

$readmeChanged = $false
if ($PSCmdlet.ShouldProcess((Join-Path $repoRoot "README.md"), "Update README table of contents")) {
  $readmeChanged = Update-ReadmeToc -RepoRoot $repoRoot -IsoDate $isoDate -PlanFileName $planFileName -SummaryText $Summary
}

if ($Push) { $Commit = $true }
if ($Commit) {
  Invoke-GitCommitAndPush -RepoRoot $repoRoot -IsoDate $isoDate -PlanFileName $planFileName -BranchName $Branch -DoPush:$Push
}

if (-not ($planCreatedOrOverwritten -or $readmeChanged)) {
  Write-Host "No changes."
}
