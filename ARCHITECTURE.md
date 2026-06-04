# RealEstate Project Architecture

## Structure
The project is built as a Multi-Page Application (MPA) with a separation of concern between global utilities and page-specific scripts.

```text
realestate/
├── backend/
│   ├── fastapi_backend/  # FastAPI implementation (future development)
│   └── frontend/
│       └── frontend/      # Current active frontend files
│           ├── home.html        # Main Landing & Search
│           ├── property-detail.html
│           ├── calculators.html
│           ├── script.js        # Global Logic & "Store" Object
│           └── style.css        # Global CSS system
└── CONTEXT.md
```

## Data Management (Store)
The application uses a centered data management system in `script.js` called **`Store`**.
- **Persistence**: All data is stored in `localStorage` as JSON.
- **Methods**: `Store.getProperties()`, `Store.addProperty()`, `Store.getFavorites()`, etc.
- **Bootstrapping**: On first load, `seedDemoProperties()` populates the `Store` with dummy data.

## Authentication & Security
- **Auth Simulation**: Users can login/signup with email/password.
- **Session Management**: Handled via the `re_user` key in `localStorage`.
- **RBAC**: A Role-Based Access Control system (`RBAC`) limits certain actions (e.g., Sellers can list properties, Buyers can't).

## Design System
- **Theme**: Premium dark-mode with a gold gradient accent (`#FFD700` to `#FFA500`).
- **Styles**: Defined globally in `style.css` using CSS variables for theme switching and consistency.
- **Components**: Reusable card UI templates (renderPropertyCard) and common navigational elements (topbar/sidebar).

## Rendering Logic
The UI renders dynamically using Vanilla JS DOM manipulation.
- **`renderPropertyCard`**: A central function to generate a property card.
- **`doSearch`**: A complex filtering algorithm that computes subsets of properties based on user inputs.
