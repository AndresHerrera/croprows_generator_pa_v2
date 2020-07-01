@echo off
echo ==============================================
echo ========== COMPILING RESOURCES ===============
echo on
call "C:\Program Files\QGIS 2.18\bin\pyrcc4.exe" -o resources.py resources.qrc
@echo off
echo ========== DONE COMPILATION ===============
echo on