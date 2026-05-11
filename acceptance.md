# Acceptance Criteria

## Tasks 1-4: Completed

## Task 5: Core shop resources (Shop) with metafield and event support

### Acceptance Criteria
- [ ] Shop resource extends ResourceBase with shop-specific functionality
- [ ] Shop.current() retrieves the current shop's information
- [ ] shop.metafields() returns list of Metafield resources for the shop
- [ ] shop.add_metafield(metafield) creates a new metafield for the shop
- [ ] shop.events() returns list of Event resources for the shop
- [ ] Metafield resource supports CRUD operations
- [ ] Metafield has namespace, key, value, and value_type attributes
- [ ] Event resource supports read operations
- [ ] Event has subject_type, subject_id, verb, and created_at attributes
