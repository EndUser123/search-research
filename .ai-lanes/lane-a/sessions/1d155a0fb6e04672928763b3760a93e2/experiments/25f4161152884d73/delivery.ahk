; AHK v2 - lane delivery experiment
#SingleInstance Force
DetectHiddenWindows False

; Target HWND in decimal
targetHwnd := 0xa90738

; Activate the window
if WinExist("ahk_id " targetHwnd) {
    WinActivate
    Sleep 300
    WinWaitActive("ahk_id " targetHwnd,, 2)
    if WinActive("ahk_id " targetHwnd) {
        ; Paste
        SendInput "^v"
        Sleep 200
        ; Press Enter
        SendInput "{Enter}"
    }
}
