param(
    [string]$BaseUrl  = "http://localhost:8000",
    [string]$Email    = "test@test.com",
    [string]$Password = "Test1234!",
    [string]$Username = "testuser"
)

$ErrorActionPreference = "Continue"
$passed = 0
$failed = 0

function Pass { param($msg) Write-Host "  [PASS] $msg" -ForegroundColor Green;  $script:passed++ }
function Fail { param($msg) Write-Host "  [FAIL] $msg" -ForegroundColor Red;    $script:failed++ }
function Step { param($msg) Write-Host "`n>> $msg" -ForegroundColor Cyan }

$tmpFile = "$env:TEMP\syllabus_test.txt"
@"
Lecture 1: Python basics. Variables, data types, functions, scope.
Lecture 2: OOP. Classes, inheritance, polymorphism, encapsulation.
Lecture 3: Async Python. asyncio, coroutines, event loop, tasks.
Lecture 4: Testing. unittest, pytest, mocking, fixtures.
Exam: 2026-07-01 covers all lectures.
"@ | Set-Content -Encoding UTF8 $tmpFile

Write-Host "`n== Learnable AI Module Tests ==" -ForegroundColor Yellow
Write-Host "Target: $BaseUrl" -ForegroundColor Yellow

# 1. Health
Step "1. Health"
try {
    $r = Invoke-RestMethod -Uri "$BaseUrl/health"
    if ($r.status -eq "ok") { Pass "server is up" } else { Fail "unexpected: $($r.status)" }
} catch {
    Fail "unreachable: $($_.Exception.Message)"
}

# 2. Register
Step "2. Register"
try {
    Invoke-RestMethod -Method POST -Uri "$BaseUrl/api/v1/auth/register" -ContentType "application/json" -Body "{`"email`":`"$Email`",`"password`":`"$Password`",`"username`":`"$Username`"}" | Out-Null
    Pass "registered $Email"
} catch {
    $msg = $_.ToString()
    if ($msg -match "REGISTER_USER_ALREADY_EXISTS" -or $msg -match "REGISTER_USERNAME_ALREADY_EXISTS") {
        Pass "user already exists"
    } else {
        Fail "register error: $msg"
    }
}

# 3. Login
Step "3. Login"
$TOKEN = $null
try {
    $r = Invoke-RestMethod -Method POST -Uri "$BaseUrl/api/v1/auth/jwt/login" -ContentType "application/x-www-form-urlencoded" -Body "username=$Email&password=$Password"
    $TOKEN = $r.access_token
    Pass "token received"
} catch {
    Fail "login failed: $($_.Exception.Message)"
    exit 1
}

$H = @{Authorization = "Bearer $TOKEN"}

# 4. Stats
Step "4. AI Stats"
try {
    $r = Invoke-RestMethod -Uri "$BaseUrl/api/v1/ai/stats" -Headers $H
    Pass "model=$($r.model) vision=$($r.vision_model)"
} catch {
    Fail "$($_.Exception.Message)"
}

# 5. Create graph
Step "5. Create graph"
$GRAPH_ID = $null
try {
    $r = Invoke-RestMethod -Method POST -Uri "$BaseUrl/api/v1/graphs" -Headers $H -ContentType "application/json" -Body '{"name":"AI Test Graph"}'
    $GRAPH_ID = $r.id
    Pass "graph_id=$GRAPH_ID"
} catch {
    Fail "failed: $($_.Exception.Message)"
    exit 1
}

# 6. Generate graph from file
Step "6. Generate graph from file (LLM call, may take 30s)"
try {
    $raw = curl.exe -s -X POST "$BaseUrl/api/v1/ai/graphs/$GRAPH_ID/generate" -H "Authorization: Bearer $TOKEN" -F "file=@$tmpFile"
    $r = $raw | ConvertFrom-Json
    if ($r.nodes_created -gt 0) {
        Pass "nodes=$($r.nodes_created) deadlines=$($r.deadlines_created)"
    } else {
        Fail "zero nodes: $raw"
    }
} catch {
    Fail "$($_.Exception.Message)"
}

# 7. List nodes
Step "7. List graph nodes"
$NODE_ID = $null
try {
    $nodes = Invoke-RestMethod -Uri "$BaseUrl/api/v1/graphs/$GRAPH_ID/nodes" -Headers $H
    if ($nodes.Count -gt 0) {
        $NODE_ID = $nodes[0].id
        Pass "$($nodes.Count) node(s), using id=$NODE_ID"
    } else {
        Fail "no nodes returned"
        $NODE_ID = "00000000-0000-0000-0000-000000000000"
    }
} catch {
    Fail "$($_.Exception.Message)"
    $NODE_ID = "00000000-0000-0000-0000-000000000000"
}

# 8. Record error
Step "8. Record error"
try {
    $raw = curl.exe -s -X POST "$BaseUrl/api/v1/ai/nodes/$NODE_ID/errors" -H "Authorization: Bearer $TOKEN" -F "description=Confusing async def with regular def" -F "source=chat"
    $r = $raw | ConvertFrom-Json
    if ($r.error_id) {
        Pass "error_id=$($r.error_id)"
    } else {
        Fail "no error_id: $raw"
    }
} catch {
    Fail "$($_.Exception.Message)"
}

# 9. Chat SSE (create session first, then stream)
Step "9a. Create chat session"
$THREAD_ID = $null
try {
    $r = Invoke-RestMethod -Method POST -Uri "$BaseUrl/api/v1/chats?node_id=$NODE_ID" -Headers $H
    $THREAD_ID = $r.id
    Pass "thread_id=$THREAD_ID"
} catch {
    Fail "failed to create chat: $($_.Exception.Message)"
}

Step "9b. Chat SSE (LLM call, may take 30s)"
if ($THREAD_ID) {
    try {
        $chatJson = '{"message":"What is asyncio and why is it useful?","chat_type":"theory","thread_id":"' + $THREAD_ID + '"}'
        $chatJson | Set-Content -Encoding UTF8 "$env:TEMP\chat_body.json"
        $raw = curl.exe -s -m 60 -N -X POST "$BaseUrl/api/v1/ai/nodes/$NODE_ID/chat" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "@$env:TEMP\chat_body.json"
        $text = ($raw -join "") -replace "data: ", ""
        if ($text.Length -gt 20) {
            Pass "got $($text.Length) chars: $($text.Substring(0, [Math]::Min(100,$text.Length)))..."
        } else {
            Fail "too short: $text"
        }
    } catch {
        Fail "$($_.Exception.Message)"
    }
} else {
    Fail "skipped — no thread_id"
}

# 10. Materials
Step "10. Materials from file (LLM call, may take 60s)"
try {
    $raw = curl.exe -s -m 120 -X POST "$BaseUrl/api/v1/ai/nodes/$NODE_ID/materials/generate-from-file" -H "Authorization: Bearer $TOKEN" -F "file=@$tmpFile" -F "material_type=both"
    $r = $raw | ConvertFrom-Json
    if ($r.cards.Count -gt 0 -or $r.notes.Length -gt 0) {
        Pass "cards=$($r.cards.Count) notes=$($r.notes.Length) chars"
    } else {
        Fail "empty response: $raw"
    }
} catch {
    Fail "$($_.Exception.Message)"
}

# 11. Planning SSE
Step "11. Planning agent SSE (LLM call, may take 30s)"
try {
    '{"message":"Add a node about decorators after the functions node"}' | Set-Content -Encoding UTF8 "$env:TEMP\plan_body.json"
    $raw = curl.exe -s -m 60 -N -X POST "$BaseUrl/api/v1/ai/graphs/$GRAPH_ID/plan" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "@$env:TEMP\plan_body.json"
    $text = ($raw -join "") -replace "data: ", ""
    if ($text.Length -gt 10) {
        Pass "got $($text.Length) chars: $($text.Substring(0, [Math]::Min(100,$text.Length)))..."
    } else {
        Fail "too short: $text"
    }
} catch {
    Fail "$($_.Exception.Message)"
}

# Summary
$color = if ($failed -eq 0) { "Green" } else { "Red" }
Write-Host "`n== Results: $passed passed, $failed failed ==`n" -ForegroundColor $color

Remove-Item $tmpFile -ErrorAction SilentlyContinue
Remove-Item "$env:TEMP\chat_body.json" -ErrorAction SilentlyContinue
Remove-Item "$env:TEMP\plan_body.json" -ErrorAction SilentlyContinue
