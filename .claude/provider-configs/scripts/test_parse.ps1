function Test {
    $tmp = [System.IO.Path]::GetTempFileName() + '.py'
    $scriptContent = @"""test"""@
    [System.IO.File]::WriteAllText($tmp, $scriptContent, [System.Text.Encoding]::UTF8)
    Get-Content $tmp
}
Test
