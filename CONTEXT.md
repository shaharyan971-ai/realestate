# RealEstate Project Context

## Overview
**RealEstate** is a modern, feature-rich property discovery and management platform. It allows users to search for properties, filter listings based on complex criteria (BHK, Price, Deal Score), compare properties, and manage their own listings.

## Technical Stack
- **Frontend**: 
    - **Language**: HTML5, Vanilla JavaScript (ES6+).
    - **Styling**: Vanilla CSS3 with a focus on dark-mode aesthetics and responsive design.
- **Backend (Potential)**: 
    - A FastAPI (Python) backend exists in the `fastapi_backend` directory, though the current frontend implementation is primarily decoupled and uses `localStorage` for data persistence.
- **Persistence**: 
    - `localStorage` manages session data, user profiles, property listings, favorites, and messages.

## Core Features
1. **Property Discovery**: Advanced search and multi-criteria filtering (location, rent/sale, price range, property type, BHK, and "Deal Score").
2. **AI Price Prediction**: A rule-based engine that predicts property rates based on city, area, and BHK, providing a "Deal Score" (Great Deal, Fair Price, Overpriced).
3. **User Management**: Authentication simulation with SHA-256 hashing, OTP generation (simulated), and Role-Based Access Control (RBAC) (Buyer, Seller, Agent, Admin).
4. **Calculators**: EMI and other financial calculators for property planning.
5. **Messaging System**: Internal messaging for communication between buyers and sellers.
6. **Property Comparison**: Side-by-side comparison of property specifications.

## Current Project Status
The project is in a highly functional prototype stage where the frontend is fully integrated with a `localStorage` state management system (`Store`). The UI is polished with a premium dark-mode design.
