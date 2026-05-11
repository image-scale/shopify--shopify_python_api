# Acceptance Criteria

## Task 1: Session management with OAuth authentication
- [x] Session.setup(api_key="key", secret="secret") stores credentials for all sessions
- [x] Session(shop_url, version, token) creates a valid session with proper site URL
- [x] Session normalizes shop URLs: "testshop" becomes "testshop.myshopify.com"
- [x] Session strips protocols from URLs: "https://testshop.myshopify.com" extracts subdomain correctly
- [x] Session.valid returns True only when both url and token are present
- [x] Session.site returns the full admin API URL like "https://testshop.myshopify.com/admin/api/2024-07"
- [x] create_permission_url(redirect_uri) returns OAuth authorization URL with client_id
- [x] create_permission_url with scope parameter adds comma-joined scopes to URL
- [x] create_permission_url with state parameter includes state for CSRF protection
- [x] validate_hmac(params) returns True for valid HMAC signature, False otherwise
- [x] validate_params(params) checks both HMAC and timestamp (rejects if > 1 day old)
- [x] calculate_hmac(params) generates correct HMAC-SHA256 signature excluding hmac param
- [x] HMAC calculation handles special characters (& and =) by percent-encoding them
- [x] request_token(params) validates HMAC, exchanges code for access token via HTTP
- [x] request_token raises ValidationException for invalid HMAC or expired timestamp
- [x] Session.temp context manager temporarily activates a session and restores original on exit

## Task 2: API version management

### Acceptance Criteria
- [ ] Version objects can be created for stable releases like "2024-07"
- [ ] Version objects validate format: must be YYYY-MM pattern
- [ ] Version with invalid format (e.g., "invalid-version") raises an error
- [ ] UnstableVersion represents the "unstable" API version
- [ ] Version.name returns the version string ("2024-07" or "unstable")
- [ ] Version.numeric_version returns integer for comparison (e.g., 202407 for "2024-07")
- [ ] Version.api_path(base_url) returns full API path like "https://shop.com/admin/api/2024-07"
- [ ] Version.stable returns True for release versions, False for unstable
- [ ] VersionRegistry stores known versions and allows lookup by name
- [ ] coerce_to_version(string) returns existing version or creates new Release dynamically
- [ ] coerce_to_version raises error for invalid version format
- [ ] Common API versions (2023-01, 2024-01, 2024-07, etc.) are pre-registered
