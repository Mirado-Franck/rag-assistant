param(
    [string]$Path = ".",
    [string]$OutputFile = "structure.txt",
    [string[]]$IgnoreFolders = @(
        "__pycache__",
        "migrations",
        "venv",
        "env",
        ".venv",
        "node_modules",
        "build",
        "dist",
        ".vite",
        ".git",
        ".hg",
        ".svn",
        ".idea",
        ".vscode",
        ".cache",
        ".pytest_cache",
        ".mypy_cache",
        "staticfiles",
        "media",
        "coverage",
        "htmlcov"
    )
)

if (Test-Path $OutputFile) { Remove-Item $OutputFile }

function Show-Tree ($directory, $prefix = "") {

    $Tee   = [char]0x251C  # ├
    $Elbow = [char]0x2514  # └
    $Horiz = [char]0x2500  # ─
    $Vert  = [char]0x2502  # │

    $items = Get-ChildItem -LiteralPath $directory -Force | Sort-Object Name

    for ($i = 0; $i -lt $items.Count; $i++) {
        $item = $items[$i]
        $isLast = ($i -eq $items.Count - 1)

        $connector = if ($isLast) { "$Elbow$Horiz$Horiz " } else { "$Tee$Horiz$Horiz " }
        $suffix = if ($item.PSIsContainer) { "/" } else { "" }

        $line = "$prefix$connector$($item.Name)$suffix"
        Write-Output $line
        Add-Content -Path $OutputFile -Value $line -Encoding utf8

        if ($item.PSIsContainer) {
            if ($IgnoreFolders -contains $item.Name) { continue }

            $newPrefix = $prefix + $(if ($isLast) { "    " } else { "$Vert   " })
            Show-Tree -directory $item.FullName -prefix $newPrefix
        }
    }
}

Show-Tree -directory $Path
Write-Output "`n✅ La structure a été sauvegardée dans $OutputFile"