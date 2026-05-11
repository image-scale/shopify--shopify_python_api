# Todo

## Plan
Build the library starting with the core session and authentication features, then add API versioning and the resource base class, followed by concrete resources, GraphQL support, pagination, and utility features. Each task delivers complete functionality that can be tested end-to-end.

## Tasks
- [x] Task 1: Implement session management with OAuth authentication, including session setup, OAuth URL generation, HMAC validation, and token exchange for accessing Shopify stores
- [x] Task 2: Implement API version management for handling different Shopify API versions (stable releases like "2024-07" and unstable) with version coercion and validation
- [x] Task 3: Implement API access scope management for validating and comparing OAuth permission scopes with read/write implications
- [>] Task 4: Implement the resource base class with thread-local session state, HTTP connection handling, and ActiveResource-style find/save/destroy operations
- [ ] Task 5: Implement core shop resources (Shop) with metafield and event support, demonstrating the resource pattern
- [ ] Task 6: Implement product resources (Product, Variant, Image) with price range calculation, collection associations, and metafield support
- [ ] Task 7: Implement customer resources (Customer) with search functionality, invitation sending, and order associations
- [ ] Task 8: Implement order resources (Order, Transaction, Fulfillment) with order lifecycle operations (close, open, cancel, capture)
- [ ] Task 9: Implement GraphQL client for executing queries with variables and operation names against the Shopify GraphQL API
- [ ] Task 10: Implement paginated collections with cursor-based pagination, next/previous page navigation, and memory-efficient iteration
- [ ] Task 11: Implement API call limit tracking to monitor and report Shopify API usage limits from response headers
- [ ] Task 12: Implement session token validation for embedded apps using JWT decoding and issuer verification
