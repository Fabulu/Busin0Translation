# init-run.ps1 — Initialize a new Claude Code run directory
#
# Usage: .\init-run.ps1 <slug>
# Example: .\init-run.ps1 fix-auth-bug
#   Creates: RUN-YYYYMMDD-HHMM-fix-auth-bug/ with TASK_LOG.md and SPEC_v1.md
#
# Templates sourced from: docs/coding_agents/claude_run_templates/

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$Slug
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path "$ScriptDir\..\..").Path
$TemplateDir = Join-Path $RepoRoot "docs\coding_agents\claude_run_templates"

$RunId = Get-Date -Format "yyyyMMdd-HHmm"
$Timestamp = "$(Get-Date -Format 'yyyy-MM-dd HH:mm') EST"
$Description = "[Describe objective here]"

$RunDir = Join-Path $ScriptDir "RUN-$RunId-$Slug"

if (Test-Path $RunDir) {
    Write-Error "ERROR: Directory already exists: $RunDir"
    exit 1
}

New-Item -ItemType Directory -Path $RunDir | Out-Null

# Generate TASK_LOG.md from template
$TaskLogTemplate = Join-Path $TemplateDir "TASK_LOG\TASK_LOG.md"
if (Test-Path $TaskLogTemplate) {
    (Get-Content $TaskLogTemplate -Raw) `
        -replace '\{\{RUN_ID\}\}', $RunId `
        -replace '\{\{SLUG\}\}', $Slug `
        -replace '\{\{TIMESTAMP\}\}', $Timestamp `
        -replace '\{\{DESCRIPTION\}\}', $Description |
        Set-Content (Join-Path $RunDir "TASK_LOG.md") -NoNewline
} else {
    Write-Warning "TASK_LOG template not found at $TaskLogTemplate"
}

# Generate SPEC_v1.md from template
$SpecTemplate = Join-Path $TemplateDir "SPEC\SPEC_v1.md"
if (Test-Path $SpecTemplate) {
    (Get-Content $SpecTemplate -Raw) `
        -replace '\{\{RUN_ID\}\}', $RunId `
        -replace '\{\{SLUG\}\}', $Slug `
        -replace '\{\{TIMESTAMP\}\}', $Timestamp `
        -replace '\{\{DESCRIPTION\}\}', $Description |
        Set-Content (Join-Path $RunDir "SPEC_v1.md") -NoNewline
} else {
    Write-Warning "SPEC template not found at $SpecTemplate"
}

Write-Host "Created: $RunDir"
Write-Host "   TASK_LOG.md"
Write-Host "   SPEC_v1.md"
Write-Host ""
Write-Host "Run ID: RUN-$RunId"
