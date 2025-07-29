# Test para generar preview desde Laravel usando ruta debug
curl.exe -X POST "http://localhost:8088/debug-preview/60" `
    -H "Content-Type: application/json" `
    -H "Accept: application/json" `
    -d '{"render_type": "2d"}' `
    --verbose
