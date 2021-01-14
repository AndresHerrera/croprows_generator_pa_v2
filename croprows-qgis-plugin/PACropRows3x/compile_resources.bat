@echo off
echo ==============================================
echo ========== COMPILING RESOURCES ===============
call "C:\OSGeo4W64\bin\o4w_env.bat"
call "C:\OSGeo4W64\bin\qt5_env.bat"
call "C:\OSGeo4W64\bin\py3_env.bat"
@echo on
call "C:\OSGeo4W64\apps\Python37\Scripts\pyrcc5.bat" -o resources.py resources.qrc
echo ========== DONE COMPILATION ===============