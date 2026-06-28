<#
.SYNOPSIS
    init-run.ps1 — Initialize a new Claude Code run directory (Windows/PowerShell port of init-run.sh)

.DESCRIPTION
    Creates runs/CLAUDE-RUNS/RUN-YYYYMMDD-HHMM-<slug>/ with TASK_LOG.md and SPEC_v1.md,
    substituting {{RUN_ID}}, {{SLUG}}, {{TIMESTAMP}}, {{DESCRIPTION}} from the templates in
    docs/coding_agents/claude_run_templates/.

.EXAMPLE
    .\init-run.ps1 fix-auth-bug
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0, HelpMessage = "Short slug for the run, e.g. fix-auth-bug")]
    [string]$Slug
)

$ErrorActionPreference = 'Stop'

$ScriptDir   = $PSScriptRoot
$RepoRoot    = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path
$TemplateDir = Join-Path $RepoRoot "docs\coding_agents\claude_run_templates"

$RunId       = Get-Date -Format 'yyyyMMdd-HHmm'
$Timestamp   = (Get-Date -Format 'yyyy-MM-dd HH:mm') + ' EST'
$Description = '[Describe objective here]'

$RunDir = Join-Path $ScriptDir "RUN-$RunId-$Slug"

if (Test-Path $RunDir) {
    Write-Error "Directory already exists: $RunDir"
    exit 1
}

New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

function Expand-Template {
    param([string]$Source, [string]$Destination)

    if (-not (Test-Path $Source)) {
        Write-Warning "Template not found at $Source"
        return
    }
    $content = Get-Content -Raw -Path $Source
    $content = $content.Replace('{{RUN_ID}}',     $RunId)
    $content = $content.Replace('{{SLUG}}',        $Slug)
    $content = $content.Replace('{{TIMESTAMP}}',   $Timestamp)
    $content = $content.Replace('{{DESCRIPTION}}', $Description)
    # Write UTF-8 without BOM so downstream tools read it cleanly
    [System.IO.File]::WriteAllText($Destination, $content, (New-Object System.Text.UTF8Encoding($false)))
}

Expand-Template -Source (Join-Path $TemplateDir "TASK_LOG\TASK_LOG.md") -Destination (Join-Path $RunDir "TASK_LOG.md")
Expand-Template -Source (Join-Path $TemplateDir "SPEC\SPEC_v1.md")       -Destination (Join-Path $RunDir "SPEC_v1.md")

Write-Output "Created: $RunDir"
Write-Output "   TASK_LOG.md"
Write-Output "   SPEC_v1.md"
Write-Output ""
Write-Output "Run ID: RUN-$RunId"
