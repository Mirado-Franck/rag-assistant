# ===========================================================================
#  verifier_b1.ps1 - simple relais vers verifier_b1.bat
#  (le .bat evite tout probleme de politique d'execution PowerShell)
# ===========================================================================
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
& ".\verifier_b1.bat"
exit $LASTEXITCODE
