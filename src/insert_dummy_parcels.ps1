# Send N random parcel inserts to the API, picking a random LCN each time.
$Url = "http://127.0.0.1:5000/insert"
$providers = @("PostNord", "DAO", "UPS", "GLS", "Bring", "FedEx")
$N = 50
Start-Sleep -Milliseconds 200

for ($i = 1; $i -le $N; $i++) {
    # 4-digit string with leading zeros
    $digits = '{0:D4}' -f (Get-Random -Minimum 0 -Maximum 10000)

    # 12-digit barcode (digits only)
    $barcode = -join (1..12 | ForEach-Object { (Get-Random -Maximum 10).ToString() })

    # 2-letter LC
    $lc = -join (1..2 | ForEach-Object { [char](Get-Random -Minimum 65 -Maximum 90) })

    # pick a random provider (LCN)
    $provider = $providers | Get-Random

    # optional: if Provider is DAO, include a random 5-digit kode
    $bodyHash = @{
        provider = $provider
        digits   = $digits
        barcode  = $barcode
        lc       = $lc
    }

    if ($provider -eq "DAO") {
        $kode = '{0:D5}' -f (Get-Random -Minimum 0 -Maximum 100000)
        $bodyHash.kode = $kode
    }

    $body = $bodyHash | ConvertTo-Json

    try {
        Invoke-RestMethod -Uri $Url -Method Post -ContentType "application/json" -Body $body -TimeoutSec 10
        Write-Host "Posted #$i -> provider=$provider digits=$digits barcode=$barcode lc=$lc" -ForegroundColor Green
        if ($provider -eq "DAO") { Write-Host "  (kode=$kode)" -ForegroundColor Yellow }
    } catch {
        Write-Warning "Failed #$i -> $_"
    }

    # small delay so server isn't overwhelmed
    Start-Sleep -Milliseconds (Get-Random -Minimum 100 -Maximum 500)
}