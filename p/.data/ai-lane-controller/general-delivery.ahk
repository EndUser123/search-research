
; general-delivery.ahk - AHK v2 delivery to any bound lane HWND
#SingleInstance Force
DetectHiddenWindows False
if A_Args.Length < 1 {
    FileAppend '{"stage":"startup","error":"missing expDir arg"}', A_Args[1] . "/delivery-result.json"
    ExitApp 1
}
expDir := A_Args[1]
authFile := expDir . "/delivery-authorization.json"
resultFile := expDir . "/delivery-result.json"
if !FileExist(authFile) {
    FileAppend '{"stage":"precondition","error":"auth file not found"}', resultFile
    ExitApp 2
}
authRaw := FileRead(authFile)
titleMatch := RegExMatch(authRaw, '"binding_title"[^:]*:\s*"([^"]+)"', &m)
expHwndMatch := RegExMatch(authRaw, '"bound_hwnd_dec"\s*:\s*(\d+)', &h)
ctrlHwndMatch := RegExMatch(authRaw, '"controller_hwnd_dec"\s*:\s*(\d+)', &c)
expiryMatch := RegExMatch(authRaw, '"expires_at"\s*:\s*"([^"]+)"', &e)
if !titleMatch { FileAppend '{"stage":"precondition","error":"no binding_title"}', resultFile; ExitApp 3 }
if !expHwndMatch { FileAppend '{"stage":"precondition","error":"no bound_hwnd_dec"}', resultFile; ExitApp 3 }
bindTitle := m[1]
expectedHwnd := Integer(h[1])
ctrlHwnd := ctrlHwndMatch ? Integer(c[1]) : 0
if expiryMatch {
    expireSec := DateDiff(e[1], A_NowUTC, "Seconds")
    if expireSec <= 0 { FileAppend '{"stage":"precondition","error":"auth expired"}', resultFile; ExitApp 4 }
}
foundHwnd := 0; foundCount := 0
WinGetList allHwnd
for hwndEntry in allHwnd {
    WinGetTitle t, "ahk_id " hwndEntry
    if (t = bindTitle) { foundCount++; foundHwnd := hwndEntry }
}
if (foundCount != 1) { FileAppend '{"stage":"precondition","error":"title count","count":' foundCount '}', resultFile; ExitApp 5 }
if (foundHwnd != expectedHwnd) { FileAppend '{"stage":"precondition","error":"hwnd changed"}', resultFile; ExitApp 6 }
if (ctrlHwnd > 0 && foundHwnd = ctrlHwnd) { FileAppend '{"stage":"precondition","error":"same window"}', resultFile; ExitApp 7 }
WinActivate "ahk_id " foundHwnd
if !WinWaitActive("ahk_id " foundHwnd,, 3) { FileAppend '{"stage":"activate","error":"timeout 3s"}', resultFile; ExitApp 8 }
if !WinActive("ahk_id " foundHwnd) { FileAppend '{"stage":"activate","error":"not active"}', resultFile; ExitApp 9 }
Sleep 200
SendInput "^v"
Sleep 200
if !WinActive("ahk_id " foundHwnd) {
    FileAppend '{"stage":"paste","error":"focus changed"}', resultFile
    ExitApp 10
}
Sleep 100
SendInput "{Enter}"
FileAppend '{"stage":"enter","status":"submitted","hwnd":' foundHwnd '}', resultFile
ExitApp 0
