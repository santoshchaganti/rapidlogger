::: RapidLogger Launcher
:: This script launches RapidLogger silently in the background
:: Any errors or status messages will be written to rapidlogger.log
:: start /min cmd /c "python rapidlogger.py & pause"
@echo off
start /b pythonw rapidlogger.py