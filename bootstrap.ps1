param(
  [string]$Branch = "main",
  [string]$Target = (Get-Location).Path,
  [switch]$Force
)
$ErrorActionPreference = "Stop"
$repo = "thewild001/loop-maker"
$temp = Join-Path ([System.IO.Path]::GetTempPath()) ("loop-maker-" + [guid]::NewGuid())
$archive = Join-Path $temp "source.zip"
try {
  New-Item -ItemType Directory -Path $temp -Force | Out-Null
  Invoke-WebRequest -Uri "https://codeload.github.com/$repo/zip/refs/heads/$Branch" -OutFile $archive
  Expand-Archive -Path $archive -DestinationPath $temp -Force
  $root = Get-ChildItem -Path $temp -Directory | Select-Object -First 1
  if (-not $root -or -not (Test-Path (Join-Path $root.FullName "skills"))) {
    throw "El archivo descargado no contiene una distribución válida de Loop Maker."
  }
  function Copy-LoopMakerFile([string]$Source, [string]$Destination) {
    New-Item -ItemType Directory -Path (Split-Path -Parent $Destination) -Force | Out-Null
    if ((Test-Path $Destination) -and -not $Force) { Write-Host "Preserved: $Destination"; return }
    Copy-Item -LiteralPath $Source -Destination $Destination -Force
    Write-Host "Installed: $Destination"
  }
  foreach ($relativeTarget in @(".agents/skills", ".claude/skills", ".opencode/skills")) {
    $sourceRoot = Join-Path $root.FullName "skills"
    Get-ChildItem -Path $sourceRoot -File -Recurse | ForEach-Object {
      $relative = $_.FullName.Substring($sourceRoot.Length).TrimStart([char[]]@(92, 47))
      Copy-LoopMakerFile $_.FullName (Join-Path (Join-Path $Target $relativeTarget) $relative)
    }
  }
  foreach ($entry in @(
    @("agents/loop-maker-orchestrator.md", ".opencode/agents/loop-maker-orchestrator.md"),
    @("integrations/cursor/loop-maker.mdc", ".cursor/rules/loop-maker.mdc"),
    @("integrations/copilot/loop-maker.instructions.md", ".github/instructions/loop-maker.instructions.md")
  )) {
    Copy-LoopMakerFile (Join-Path $root.FullName $entry[0]) (Join-Path $Target $entry[1])
  }
  Write-Host "Loop Maker skills installed in $Target"
  Write-Host "Open the project in your agent and invoke /loop-maker."
  Write-Host "MCP is optional; see integrations/mcp/README.md."
} finally {
  if (Test-Path $temp) { Remove-Item -LiteralPath $temp -Recurse -Force }
}
