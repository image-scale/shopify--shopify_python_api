# Acceptance Criteria

## Task 1: Session management with OAuth authentication

### Acceptance Criteria
- [ ] Session.setup(api_key="key", secret="secret") stores credentials for all sessions
- [ ] Session(shop_url, version, token) creates a valid session with proper site URL
- [ ] Session normalizes shop URLs: "testshop" becomes "testshop.myshopify.com"
- [ ] Session strips protocols from URLs: "https://testshop.myshopify.com" extracts subdomain correctly
- [ ] Session.valid returns True only when both url and token are present
- [ ] Session.site returns the full admin API URL like "https://testshop.myshopify.com/admin/api/2024-07"
- [ ] create_permission_url(redirect_uri) returns OAuth authorization URL with client_id
- [ ] create_permission_url with scope parameter adds comma-joined scopes to URL
- [ ] create_permission_url with state parameter includes state for CSRF protection
- [ ] validate_hmac(params) returns True for valid HMAC signature, False otherwise
- [ ] validate_params(params) checks both HMAC and timestamp (rejects if > 1 day old)
- [ ] calculate_hmac(params) generates correct HMAC-SHA256 signature excluding hmac param
- [ ] HMAC calculation handles special characters (& and =) by percent-encoding them
- [ ] request_token(params) validates HMAC, exchanges code for access token via HTTP
- [ ] request_token raises ValidationException for invalid HMAC or expired timestamp
- [ ] Session.temp context manager temporarily activates a session and restores original on exit
