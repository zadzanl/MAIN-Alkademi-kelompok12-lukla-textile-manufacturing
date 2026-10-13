# Naming Conventions - Lukla Operations Engine

Panduan naming untuk consistency saat Vibe Coding.

## File Naming

### React Components
```
PascalCase.jsx
Contoh: UserDashboard.jsx, OrderCard.jsx, StatusBadge.jsx
```

### Utility/Helper Functions
```
camelCase.js
Contoh: calculateShippingCost.js, validateEmail.js, formatDate.js
```

### Database Related
```
camelCase.js (queries)
Schema files: camelCaseSchema.js
Contoh: getUserOrders.js, userSchema.js
```

### Hooks
```
useNameInCamelCase.js
Contoh: useAuth.js, useFetchData.js, useLocalStorage.js
```

## Code Naming

### Components
```javascript
// PascalCase
const UserProfile = () => { ... }
const DashboardCard = () => { ... }
```

### Functions
```javascript
// camelCase, verb at start
const fetchUserData = () => { ... }
const calculateTotal = () => { ... }
const handleSubmit = () => { ... }
```

### Variables
```javascript
// camelCase
const userData = { ... }
const isLoading = false
const orderCount = 0
```

### Constants
```javascript
// UPPER_SNAKE_CASE
const API_BASE_URL = 'https://api.example.com'
const MAX_RETRY_COUNT = 3
const DEFAULT_TIMEOUT = 5000
```

### Event Handlers
```javascript
// handleEventName
const handleClick = () => { ... }
const handleFormSubmit = (e) => { ... }
const handleUserLogout = () => { ... }
```

## Database Naming

### Tables
```
snake_case (plural)
users, orders, products, order_items
```

### Columns
```
snake_case
user_id, first_name, email, created_at
```

### Relationships
```
foreign_key: singular_table_id
user_id, product_id, order_id
```

## API Endpoints

```
/api/v1/resource
/api/v1/users
/api/v1/users/:id
/api/v1/orders/:id/items
```

### Methods
```
GET    /users          (list)
GET    /users/:id      (detail)
POST   /users          (create)
PUT    /users/:id      (update)
DELETE /users/:id      (delete)
```
