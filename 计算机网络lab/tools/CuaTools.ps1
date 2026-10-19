# CuaTools.ps1 - reusable GUI observation helpers for DSH agent
# Loaded with:  . "C:\University Courses\计算机网络lab\tools\CuaTools.ps1"
# Requires: PowerShell 5.1 (Desktop), FullLanguage

Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms

# ---- Win32 interop ---------------------------------------------------------
if (-not ('CuaWin32' -as [type])) {
Add-Type -TypeDefinition @'
using System;
using System.Text;
using System.Runtime.InteropServices;

public class CuaWin32 {
    public delegate bool EnumProc(IntPtr h, IntPtr l);

    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr l);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
    [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetWindowTextW(IntPtr h, StringBuilder s, int n);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetClassNameW(IntPtr h, StringBuilder s, int n);
    [DllImport("user32.dll")] public static extern int GetWindowTextLengthW(IntPtr h);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
    [DllImport("user32.dll")] public static extern IntPtr GetDesktopWindow();
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll")] public static extern IntPtr WindowFromPoint(POINT p);
    [DllImport("user32.dll")] public static extern IntPtr GetDC(IntPtr h);
    [DllImport("gdi32.dll")] public static extern int GetDeviceCaps(IntPtr dc, int i);
    [DllImport("user32.dll")] public static extern int ReleaseDC(IntPtr h, IntPtr dc);

    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
    [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X, Y; }
}
'@
}

function Enable-CuaDpiAware {
    <# Makes this process DPI-aware so GetWindowRect/GetSystemMetrics report
       PHYSICAL pixels, matching screenshot pixel space. #>
    [void][CuaWin32]::SetProcessDPIAware()
    $r = New-Object CuaWin32+RECT
    return $true
}

function Get-CuaWindows {
    <# Returns visible top-level windows with title, class, pid, process, rect. #>
    $fg = [CuaWin32]::GetForegroundWindow()
    $script:__cuaRows = New-Object System.Collections.ArrayList
    $cb = [CuaWin32+EnumProc] {
        param($h, $l)
        if ([CuaWin32]::IsWindowVisible($h)) {
            $len = [CuaWin32]::GetWindowTextLengthW($h)
            if ($len -gt 0) {
                $sb = New-Object System.Text.StringBuilder 512
                [void][CuaWin32]::GetWindowTextW($h, $sb, 512)
                $cn = New-Object System.Text.StringBuilder 256
                [void][CuaWin32]::GetClassNameW($h, $cn, 256)
                $procId = [uint32]0
                [void][CuaWin32]::GetWindowThreadProcessId($h, [ref]$procId)
                $r = New-Object CuaWin32+RECT
                [void][CuaWin32]::GetWindowRect($h, [ref]$r)
                $pn = ''
                try { $pn = (Get-Process -Id $procId -ErrorAction Stop).ProcessName } catch { }
                [void]$script:__cuaRows.Add([pscustomobject]@{
                    Handle     = $h
                    PID        = $procId
                    Proc       = $pn
                    Title      = $sb.ToString()
                    Class      = $cn.ToString()
                    Left       = $r.Left
                    Top        = $r.Top
                    Right      = $r.Right
                    Bottom     = $r.Bottom
                    Width      = ($r.Right - $r.Left)
                    Height     = ($r.Bottom - $r.Top)
                    Minimized  = [CuaWin32]::IsIconic($h)
                    Foreground = ($h -eq $fg)
                })
            }
        }
        return $true
    }
    [void][CuaWin32]::EnumWindows($cb, [IntPtr]::Zero)
    return $script:__cuaRows
}

function Get-CuaScreen { param([string]$Path, [switch]$Quiet)
    <# Grabs the full virtual desktop to a PNG file (physical pixels). #>
    $f = [System.Windows.Forms.SystemInformation]::VirtualScreen
    $bmp = New-Object System.Drawing.Bitmap($f.Width, $f.Height)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($f.Left, $f.Top, 0, 0, $bmp.Size)
    $g.Dispose()
    if (-not $Path) { $Path = Join-Path $env:TEMP ("cua-shot-" + (Get-Date -Format 'HHmmss-fff') + ".png") }
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $bmp.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    $bmp.Dispose()
    if (-not $Quiet) {
        "SCREENSHOT $Path  size=$($f.Width)x$($f.Height)  bytes=$((Get-Item $Path).Length)"
    }
    return $Path
}

function Get-CuaWindowShot { param([IntPtr]$Handle, [string]$Path)
    <# Grabs a single window by handle to a PNG (physical pixels). #>
    $r = New-Object CuaWin32+RECT
    [void][CuaWin32]::GetWindowRect($Handle, [ref]$r)
    $w = $r.Right - $r.Left; $h = $r.Bottom - $r.Top
    if ($w -le 0 -or $h -le 0) { throw "window has no area (minimized?)" }
    $bmp = New-Object System.Drawing.Bitmap($w, $h)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($r.Left, $r.Top, 0, 0, (New-Object System.Drawing.Size($w, $h)))
    $g.Dispose()
    if (-not $Path) { $Path = Join-Path $env:TEMP ("cua-win-" + (Get-Date -Format 'HHmmss-fff') + ".png") }
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $bmp.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    $bmp.Dispose()
    "WINDOWSHOT $Path  rect=$($r.Left),$($r.Top),$($r.Right),$($r.Bottom) size=${w}x${h}"
    return $Path
}

function Get-CuaScreenInfo {
    <# Reports the coordinate truth: logical vs physical desktop size and DPI. #>
    $dc = [CuaWin32]::GetDC([IntPtr]::Zero)
    $physW = [CuaWin32]::GetDeviceCaps($dc, 118)
    $physH = [CuaWin32]::GetDeviceCaps($dc, 117)
    $dpiX = [CuaWin32]::GetDeviceCaps($dc, 88)
    [void][CuaWin32]::ReleaseDC([IntPtr]::Zero, $dc)
    $vs = [System.Windows.Forms.SystemInformation]::VirtualScreen
    $smW = [System.Windows.Forms.SystemInformation]::VirtualScreen.Width
    [pscustomobject]@{
        WinFormsVirtualScreen = "$($vs.Left),$($vs.Top) $($vs.Width)x$($vs.Height)"
        PhysicalPanel         = "${physW}x${physH}"
        LogicalDPI            = $dpiX
        ScaleFactor           = [math]::Round($physW / [double]$vs.Width, 3)
        ProcessDpiAware       = $script:__cuaDpiAware
    }
}

function Set-CuaForeground { param([IntPtr]$Handle)
    <# Brings a window to the foreground. Returns $true/$false. #>
    if ([CuaWin32]::IsIconic($Handle)) { [void][CuaWin32]::ShowWindow($Handle, 9) }  # SW_RESTORE
    $ok = [CuaWin32]::SetForegroundWindow($Handle)
    Start-Sleep -Milliseconds 250
    $fg = [CuaWin32]::GetForegroundWindow()
    [pscustomobject]@{ Requested = $ok; IsForegroundNow = ($fg -eq $Handle); ForegroundHandle = $fg; TargetHandle = $Handle }
}

function Find-CuaWindow { param([string]$TitlePattern, [string]$ProcPattern)
    <# Finds window(s) by title regex and/or process-name regex. #>
    $wins = Get-CuaWindows
    if ($TitlePattern) { $wins = $wins | Where-Object { $_.Title -match $TitlePattern } }
    if ($ProcPattern) { $wins = $wins | Where-Object { $_.Proc -match $ProcPattern } }
    return $wins
}

function Send-CuaText { param([string]$Text, [int]$DelayMs = 60)
    <# Types text into the focused control using SendKeys (works for Notepad-class apps). #>
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.SendKeys]::SendWait($Text)
    Start-Sleep -Milliseconds $DelayMs
}

function Get-CuaUiaWindows {
    <# Lists top-level windows as seen by UI Automation (Accessibility tree). #>
    Add-Type -AssemblyName UIAutomationClient
    Add-Type -AssemblyName UIAutomationTypes
    $root = [System.Windows.Automation.AutomationElement]::RootElement
    $cond = New-Object System.Windows.Automation.PropertyCondition(
        [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
        [System.Windows.Automation.ControlType]::Window)
    $wins = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $cond)
    $out = @()
    foreach ($w in $wins) {
        $out += [pscustomobject]@{
            Name      = $w.Current.Name
            Class     = $w.Current.ClassName
            PID       = $w.Current.ProcessId
            Handle    = $w.Current.NativeWindowHandle
            Enabled   = $w.Current.IsEnabled
            Offscreen = $w.Current.IsOffscreen
        }
    }
    return $out
}

function Get-CuaUiaTree { param([IntPtr]$Handle, [int]$MaxDepth = 3, [int]$MaxNodes = 80)
    <# Dumps a shallow UI Automation subtree for a top-level window handle. #>
    Add-Type -AssemblyName UIAutomationClient
    Add-Type -AssemblyName UIAutomationTypes
    $root = [System.Windows.Automation.AutomationElement]::RootElement
    $cond = New-Object System.Windows.Automation.PropertyCondition(
        [System.Windows.Automation.AutomationElement]::NativeWindowHandleProperty, [int]$Handle)
    $top = $root.FindFirst([System.Windows.Automation.TreeScope]::Children, $cond)
    if (-not $top) { return @() }
    $rows = New-Object System.Collections.ArrayList
    $walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker
    function Walk($el, $depth) {
        if ($rows.Count -ge $MaxNodes) { return }
        $r = $el.Current.BoundingRectangle
        $ctype = ($el.Current.ControlType.ProgrammaticName) -replace 'ControlType\.', ''
        [void]$rows.Add([pscustomobject]@{
            Depth        = $depth
            ControlType  = $ctype
            Name         = $el.Current.Name
            AutomationId = $el.Current.AutomationId
            Class        = $el.Current.ClassName
            Rect         = "$([int]$r.X),$([int]$r.Y) $([int]$r.Width)x$([int]$r.Height)"
            Enabled      = $el.Current.IsEnabled
        })
        if ($depth -ge $MaxDepth) { return }
        $child = $walker.GetFirstChild($el)
        while ($child -ne $null -and $rows.Count -lt $MaxNodes) {
            Walk $child ($depth + 1)
            $child = $walker.GetNextSibling($child)
        }
    }
    Walk $top 0
    return $rows
}

# Initialise DPI awareness on load so all coordinates are physical pixels.
if (-not $script:__cuaDpiAware) {
    [void][CuaWin32]::SetProcessDPIAware()
    $script:__cuaDpiAware = $true
}
