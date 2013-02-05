Name "Aston"
Icon "logo.ico"
LicenseData "..\..\COPYING.txt"
OutFile "aston.exe"
InstallDir $PROGRAMFILES\Aston
RequestExecutionLevel user

Page license
Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

Section "Aston (required)"
  SectionIn RO
  SetOutPath "$INSTDIR"
  File /r "..\..\dist"
  WriteUninstaller "uninstall.exe"
SectionEnd

Section "Start Menu Shortcuts"
  SetOutPath "$INSTDIR\dist"
  CreateDirectory "$SMPrograms\Aston"
  CreateShortcut "$SMPROGRAMS\Aston\Uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0
  CreateShortcut "$SMPROGRAMS\Aston\Aston.lnk" "$INSTDIR\dist\astonx.exe" "" "$INSTDIR\dist\aston\ui\icons\logo.ico" 0
SectionEnd

Section "Uninstall"
  Delete $INSTDIR\uninstall.exe
  RMDir /r "$INSTDIR"

  Delete "$SMPROGRAMS\Aston\*.*"
  RMDir "$SMPROGRAMS\Aston"
SectionEnd
