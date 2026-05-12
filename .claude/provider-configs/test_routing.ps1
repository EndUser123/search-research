. 'P:\.claude\provider-configs\cc-bifrost.ps1'
$model = 'N-Kimi-2.6'
$scriptPath = "$PSScriptRoot\scripts\routes_probe.py"
$tmp = [System.IO.Path]::GetTempFileName() + ".py"
$scriptContent = @"
import sqlite3, json
conn = sqlite3.connect(r'C:\Users\brsth\AppData\Roaming\bifrost\config.db')
c = conn.cursor()
c.execute('''
    SELECT r.id, r.cel_expression, rt.provider, rt.model
    FROM routing_rules r
    LEFT JOIN routing_targets rt ON rt.rule_id = r.id
    WHERE r.cel_expression IS NOT NULL AND r.cel_expression != ''
    ORDER BY r.priority
''')
routes = {}
for row in c.fetchall():
    cel = row[1]
    provider = row[2]
    model = row[3]
    import re
    m = re.search('model==\"([^\"]+)\"', cel.replace(' ', ''))
    if m and provider and model:
        modelName = m.group(1)
        routes[modelName] = {'display': f'{provider}/{model}', 'sonnet': modelName, 'opus': modelName, 'haiku': modelName}
print(json.dumps(routes))
conn.close()
"@
[System.IO.File]::WriteAllText($tmp, $scriptContent, [System.Text.Encoding]::UTF8)
$json = python3 $tmp 2>$null
Remove-Item $tmp -Force -ErrorAction SilentlyContinue
if ($json) {
    $data = ConvertFrom-Json $json
    $ht = @{}
    try {
        $data.psobject.properties | ForEach-Object { $ht[$_.Name] = $_.Value }
    } catch {
        foreach ($prop in $data.PSObject.Properties) {
            $ht[$prop.Name] = $prop.Value
        }
    }
    Write-Host "=== DB ROUTES ==="
    $ht.Keys | ForEach-Object {
        $k = $_
        $v = $ht[$k]
        Write-Host "$k -> display=$($v.display)"
    }
    Write-Host ""
    Write-Host "=== LOOKUP N-Kimi-2.6 ==="
    if ($ht.ContainsKey('N-Kimi-2.6')) {
        $route = $ht['N-Kimi-2.6']
        Write-Host "Found: display=$($route.display)"
    } else {
        Write-Host "NOT FOUND in routing table"
    }
} else {
    Write-Host "No JSON returned from DB query"
}
