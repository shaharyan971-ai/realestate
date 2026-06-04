# Refactor Property Listing Logic

The goal of this refactor is to consolidate duplicate property card rendering logic and centralize the filtering and searching functionality within the `Store` object in `script.js`. This will make the codebase more maintainable and reduce the weight of page-specific scripts.

## User Review Required

> [!IMPORTANT]
> This refactor will change how properties are filtered and rendered on the `home.html` page. While the final UI will look the same, the internal logic will move from embedded `<script>` tags in `home.html` to the shared `script.js`.

## Proposed Changes

### [Store & Components] [script.js](file:///c:/Users/ancus/Downloads/realestate%20%283%29/realestate/backend/frontend/frontend/script.js)

#### [MODIFY] [script.js](file:///c:/Users/ancus/Downloads/realestate%20%283%29/realestate/backend/frontend/frontend/script.js)
- Enhance the `Store` object with a `search(params)` method to centralize filtering logic.
- Standardize `renderPropertyCard` to include all features (Deal Score, Badges, etc.) so it can replace the local `makeCard` in `home.html`.
- Add a `formatCurrency` utility to `script.js` to ensure consistent price formatting across the app.

### [Home Page] [home.html](file:///c:/Users/ancus/Downloads/realestate%20%283%29/realestate/backend/frontend/frontend/home.html)

#### [MODIFY] [home.html](file:///c:/Users/ancus/Downloads/realestate%20%283%29/realestate/backend/frontend/frontend/home.html)
- Remove the local `makeCard` function.
- Remove the local `fmtPrice` function.
- Simplify `doSearch` by delegating the filtering work to `Store.search()`.
- Use the shared `renderPropertyCard` from `script.js`.

## Open Questions

- Should we also move the "Results Bar" and "Empty State" UI generation to `script.js` as well? 
    - *Proposed*: Keep the UI generation in `script.js` as a utility function (`renderEmptyState`) to allow other pages (like `favorites.html` or `properties.html`) to use it.

## Verification Plan

### Automated Tests
- No automated testing framework is currently set up. Manual verification is required.

### Manual Verification
- Open `home.html` and verify that initial property loading still works.
- Test all filters (Price, Type, BHK, Deal Score) and ensure results update correctly.
- Test sorting (Price High/Low, Newest, Area) and ensure the order is correct.
- Verify that "View Details" and "Favorite" buttons still function.
