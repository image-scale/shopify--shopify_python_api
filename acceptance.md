# Acceptance Criteria

## Task 1-3: Completed

## Task 4: Resource base class with ActiveResource-style operations

### Acceptance Criteria
- [ ] Resource.activate_session(session) sets the active session for API requests
- [ ] Resource.clear_session() clears the active session
- [ ] Resource.site returns the current API site URL
- [ ] Resource.headers returns headers including X-Shopify-Access-Token
- [ ] Resource.find(id) retrieves a single resource by ID via HTTP GET
- [ ] Resource.find() without ID retrieves a collection of resources
- [ ] Resource.find() with query params adds them to the request
- [ ] resource.save() creates new resource via POST when no ID present
- [ ] resource.save() updates existing resource via PUT when ID present
- [ ] resource.destroy() deletes the resource via HTTP DELETE
- [ ] Resources decode JSON responses into attribute dictionaries
- [ ] Resources support prefix options for nested resources (e.g., /orders/123/fulfillments)
- [ ] Thread-local state prevents session leakage between threads
