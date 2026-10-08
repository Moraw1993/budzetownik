param(
    [string]$Network = "myhomebudget_default",
    [string]$CaddyImage = "caddy:2.10.0-alpine",
    [string]$BackendImage = "myhomebudget-backend:local",
    [string]$FrontendImage = "myhomebudget-frontend:latest",
    [ValidateRange(1, 20)][int]$Repetitions = 2,
    [string]$ConfigPath
)

$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$productionPath = Join-Path $repositoryRoot "infra/Caddyfile"
if ($ConfigPath) { $productionPath = [System.IO.Path]::GetFullPath($ConfigPath) }
$probePath = Join-Path $PSScriptRoot "probes/attachment_proxy_probe.py"
$h2ProbePath = Join-Path $PSScriptRoot "probes/attachment_proxy_h2.mjs"
$tempParent = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$testDirectory = Join-Path $tempParent ("mhh-attachment-proxy-" + [guid]::NewGuid())
$suffix = [guid]::NewGuid().ToString("N").Substring(0, 8)
$upstreamName = "mhh-attachment-up-$suffix"
$proxyName = "mhh-attachment-proxy-$suffix"
$appProxyName = "mhh-attachment-app-$suffix"
$evidenceDirectory = Join-Path $repositoryRoot ".runtime/attachment-proxy-$suffix"

function Invoke-ProbeDocker {
    param([string[]]$Arguments)
    $output = & docker @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Docker failed ($LASTEXITCODE): $($Arguments -join ' ')`n$($output -join [Environment]::NewLine)"
    }
    return $output
}

function Start-ProbeProxy {
    param([string]$Name, [string]$Config)
    Invoke-ProbeDocker @(
        "run", "--detach", "--name", $Name, "--network", $Network,
        "--network-alias", $Name,
        "--mount", "type=bind,source=$Config,target=/etc/caddy/Caddyfile,readonly",
        $CaddyImage, "caddy", "run", "--config", "/etc/caddy/Caddyfile"
    ) | Out-Null
}

try {
    Invoke-ProbeDocker @("network", "inspect", $Network) | Out-Null
    New-Item -ItemType Directory -Path $testDirectory, $evidenceDirectory | Out-Null
    Invoke-ProbeDocker @("image", "inspect", "--format", "{{json .RepoDigests}}", $CaddyImage) |
        Set-Content -LiteralPath (Join-Path $evidenceDirectory "image-digest.txt")
    Invoke-ProbeDocker @("run", "--rm", $CaddyImage, "caddy", "version") |
        Set-Content -LiteralPath (Join-Path $evidenceDirectory "version.txt")
    Invoke-ProbeDocker @("run", "--rm", $CaddyImage, "caddy", "build-info") |
        Set-Content -LiteralPath (Join-Path $evidenceDirectory "build-info.txt")
    Invoke-ProbeDocker @(
        "run", "--rm", "--mount", "type=bind,source=$productionPath,target=/etc/caddy/Caddyfile,readonly",
        $CaddyImage, "caddy", "validate", "--config", "/etc/caddy/Caddyfile"
    ) | Set-Content -LiteralPath (Join-Path $evidenceDirectory "production-validate.txt")

    $production = [System.IO.File]::ReadAllText($productionPath)
    $responseBudget = if ($production.Contains("write_timeout 10m")) { "1" } else { "0" }
    if (-not $production.Contains("read_timeout 10m")) { throw "Production upload timeout was not found." }
    $probeConfig = $production.Replace("read_timeout 10m", "read_timeout 2s")
    $probeConfig = $probeConfig.Replace("write_timeout 10m", "write_timeout 2s")
    $probeConfig = $probeConfig.Replace("backend:8000", "${upstreamName}:8001").Replace("frontend:3000", "${upstreamName}:8001")
    $logConfig = "tls internal`n`tlog {`n`t`toutput stdout`n`t`tformat json`n`t}"
    $probeConfig = $probeConfig.Replace("tls internal", $logConfig)
    $siteStart = $probeConfig.IndexOf("https://localhost:8443 {")
    if ($siteStart -lt 0) { throw "Production TLS listener was not found." }
    $controlSite = $probeConfig.Substring($siteStart).Replace("8443", "8444").Replace("read_timeout 2s", "read_timeout 6s").Replace("write_timeout 2s", "write_timeout 6s")
    $lateWriteControlSite = $probeConfig.Substring($siteStart).Replace("8443", "8445").Replace("write_timeout 2s", "write_timeout 6s")
    $probeConfig += [Environment]::NewLine + $controlSite
    if ($responseBudget -eq "1") { $probeConfig += [Environment]::NewLine + $lateWriteControlSite }
    $configPath = Join-Path $testDirectory "probe.Caddyfile"
    [System.IO.File]::WriteAllText($configPath, $probeConfig)
    Copy-Item -LiteralPath $configPath -Destination (Join-Path $evidenceDirectory "probe.Caddyfile")
    [ordered]@{
        repetitions = $Repetitions
        protocols = @("http/1.1", "h2")
        response_budget = ($responseBudget -eq "1")
        configuration_sha256 = (Get-FileHash -LiteralPath $configPath -Algorithm SHA256).Hash.ToLowerInvariant()
        source_configuration_sha256 = (Get-FileHash -LiteralPath $productionPath -Algorithm SHA256).Hash.ToLowerInvariant()
        caddy_image = $CaddyImage
    } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $evidenceDirectory "manifest.json")
    $adaptOutput = & docker run --rm --mount "type=bind,source=$configPath,target=/etc/caddy/Caddyfile,readonly" `
        $CaddyImage caddy adapt --config /etc/caddy/Caddyfile --pretty `
        2>(Join-Path $evidenceDirectory "adapt-stderr.txt")
    if ($LASTEXITCODE -ne 0) { throw "Caddy adapter failed." }
    $adaptOutput | Set-Content -LiteralPath (Join-Path $evidenceDirectory "adapt.json")

    Invoke-ProbeDocker @(
        "run", "--detach", "--name", $upstreamName, "--network", $Network,
        "--network-alias", $upstreamName,
        "--mount", "type=bind,source=$probePath,target=/tmp/probe.py,readonly",
        $BackendImage, "python", "-u", "/tmp/probe.py", "server"
    ) | Out-Null
    Start-ProbeProxy -Name $proxyName -Config $configPath
    Start-ProbeProxy -Name $appProxyName -Config $productionPath
    Start-Sleep -Seconds 2
    $clientOutput = & docker run --rm --network $Network -e "PROXY_HOST=$proxyName" -e "REQUIRE_RESPONSE_BUDGET=$responseBudget" `
        --mount "type=bind,source=$probePath,target=/tmp/probe.py,readonly" `
        $BackendImage python -u /tmp/probe.py client --repetitions $Repetitions 2>&1
    $clientExitCode = $LASTEXITCODE
    $clientOutput | Set-Content -LiteralPath (Join-Path $evidenceDirectory "client.jsonl")
    $clientOutput | ForEach-Object { Write-Output $_ }
    $h2Output = & docker run --rm --network $Network -e "PROXY_HOST=$proxyName" `
        -e "PROBE_REPETITIONS=$Repetitions" -e "REQUIRE_RESPONSE_BUDGET=$responseBudget" `
        --mount "type=bind,source=$h2ProbePath,target=/tmp/h2.mjs,readonly" `
        --entrypoint node $FrontendImage /tmp/h2.mjs 2>&1
    $h2ExitCode = $LASTEXITCODE
    $h2Output | Set-Content -LiteralPath (Join-Path $evidenceDirectory "client-h2.jsonl")
    $h2Output | ForEach-Object { Write-Output $_ }

    $nodeClient = @'
const assert = require("node:assert/strict");
const https = require("node:https");
const http2 = require("node:http2");
const hostname = process.env.APP_PROXY_HOST;
const path = "/api/households/";
async function http1() {
  return new Promise((resolve, reject) => {
    const request = https.get({
      hostname,
      port: 8443,
      path,
      servername: "localhost",
      rejectUnauthorized: false,
      headers: { Host: "localhost:8443" },
    }, (response) => {
      let body = "";
      response.on("data", (chunk) => {
        body += chunk;
      });
      response.on("end", () => resolve({
        status: response.statusCode,
        version: response.httpVersion,
        body,
      }));
    });
    request.on("error", reject);
  });
}
async function http2Request() {
  return new Promise((resolve, reject) => {
    const session = http2.connect(`https://${hostname}:8443`, {
      servername: "localhost",
      rejectUnauthorized: false,
    });
    session.on("error", reject);
    const request = session.request({ ":path": path, ":authority": "localhost:8443" });
    let status;
    let body = "";
    request.on("response", (headers) => {
      status = headers[":status"];
    });
    request.on("data", (chunk) => {
      body += chunk;
    });
    request.on("end", () => {
      session.close();
      resolve({ status, body });
    });
    request.on("error", reject);
    request.end();
  });
}
(async () => {
  const h1 = await http1();
  assert.equal(h1.status, 403);
  assert.equal(h1.version, "1.1");
  assert.match(h1.body, /uwierzyteln|auth/i);
  const h2 = await http2Request();
  assert.equal(h2.status, 403);
  assert.match(h2.body, /uwierzyteln|auth/i);
  console.log("Real backend through production TLS config: HTTP/1.1 and HTTP/2 authentication responses passed.");
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
'@
    $nodePath = Join-Path $testDirectory "app-client.js"
    [System.IO.File]::WriteAllText($nodePath, $nodeClient)
    Invoke-ProbeDocker @(
        "run", "--rm", "--network", $Network, "-e", "APP_PROXY_HOST=$appProxyName",
        "--mount", "type=bind,source=$nodePath,target=/tmp/app-client.js,readonly",
        "--entrypoint", "node", $FrontendImage, "/tmp/app-client.js"
    ) | Tee-Object -FilePath (Join-Path $evidenceDirectory "app-protocols.txt")
    & docker logs $proxyName 2>&1 | Set-Content -LiteralPath (Join-Path $evidenceDirectory "proxy.jsonl")
    & docker logs $upstreamName 2>&1 | Set-Content -LiteralPath (Join-Path $evidenceDirectory "upstream.jsonl")
    $assessment = & docker run --rm --mount "type=bind,source=$probePath,target=/tmp/probe.py,readonly" `
        --mount "type=bind,source=$evidenceDirectory,target=/evidence" `
        $BackendImage python /tmp/probe.py assess --evidence-directory /evidence 2>&1
    $assessmentExitCode = $LASTEXITCODE
    $assessment | Tee-Object -FilePath (Join-Path $evidenceDirectory "assessment.txt")
    if ($clientExitCode -ne 0 -or $h2ExitCode -ne 0 -or $assessmentExitCode -ne 0) { throw "Proxy probe failed. Evidence: $evidenceDirectory" }
    Write-Output "Proxy probe passed. Evidence: $evidenceDirectory"
}
finally {
    foreach ($name in @($proxyName, $appProxyName, $upstreamName)) {
        $exists = & docker ps -a --format "{{.Names}}" 2>$null | Where-Object { $_ -eq $name }
        if ($exists) {
            & docker logs $name 2>&1 | Set-Content -LiteralPath (Join-Path $evidenceDirectory "$name.jsonl")
            & docker rm -f $name | Out-Null
        }
    }
    $resolvedDirectory = [System.IO.Path]::GetFullPath($testDirectory)
    if ($resolvedDirectory.StartsWith($tempParent, [System.StringComparison]::OrdinalIgnoreCase) -and (Test-Path -LiteralPath $resolvedDirectory)) {
        Remove-Item -LiteralPath $resolvedDirectory -Recurse -Force
    }
}
