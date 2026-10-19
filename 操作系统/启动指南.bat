@echo off
chcp 65001 >nul
title 操作系统学习指南
cd /d "%~dp0"
start "" python serve_guide.py
