# Recipe Manager Web App - Implementation Plan

## Project Overview

**Project Name:** Recipe Manager  
**Type:** Self-hosted Flask Web Application  
**Core Functionality:** A personal recipe management system with ingredient search, meal planning, shopping list generation, and nutrition tracking  
**Target Users:** Home cooks who want to organize recipes, plan meals, and generate shopping lists

---

## Technology Stack

### Backend
- **Framework:** Flask 3.x (Python 3.11+)
- **Database:** SQLite (self-hosted, file-based)
- **ORM:** SQLAlchemy 2.x with Flask-SQLAlchemy
- **Authentication:** Flask-Login with hashed passwords
- **API:** RESTful Flask endpoints with JSON responses
- **Migration:** Flask-Migrate (Alembic)

### Frontend
- **Template Engine:** Jinja2 (Flask default)
- **CSS Framework:** Tailwind CSS (via CDN for simplicity)
- **JavaScript:** Vanilla JS with Fetch API
- **Icons:** Heroicons or Phosphor Icons

### Key Dependencies (requirements.txt)
```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.5
Flask-Login==0.6.3
Werkzeug==3.0.1
SQLAlchemy==2.0.23
python-dotenv==1.0.0
requests==2.31.0
```

---

## File Structure

```
recipe-manager/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── config.py                # Configuration settings
│   ├── models.py                # SQLAlchemy models
│   ├── forms.py                 # WTForms (if needed)
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py              # Login/register/logout
│   │   ├── recipes.py            # Recipe CRUD
│   │   ├── search.py             # Ingredient search
│   │   ├── meal_plan.py         # Meal planning
│   │   ├── shopping.py           # Shopping list generation
│   │   ├── nutrition.py          # Nutrition tracking
│   │   └── api.py               # API routes (JSON)
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── nutrition_calculator.py
│   │   ├── shopping_list_generator.py
│   │   └── meal_planner.py
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── validators.py
│   │   └── helpers.py
│   │
│   └── templates/
│       ├── base.html
│       ├── auth/
│       │   ├── login.html
│       │   └── register.html
│       ├── recipes/
│       │   ├── list.html
│       │   ├── detail.html
│       │   ├── create.html
│       │   └── edit.html
│       ├── search.html
│       ├── meal_plan.html
│       ├── shopping_list.html
│       ├── nutrition.html
│       └── dashboard.html
│   │
│   └── static/
│       ├── css/
│       │   └── custom.css
│       └── js/
│           ├── main.js
│           ├── recipe_form.js
│           ├── search.js
│           └── meal_plan.js
│
├── migrations/                    # Alembic migrations
├── instance/                      # SQLite database
├── .env                          # Environment variables
├── requirements.txt
├── run.py                        # Application entry point
└── PLAN.md                       # This file
```

---

## Database Schema

### User
```python
class User(db.Model):
    id: Integer (PK)
    username: String(80) - UNIQUE, NOT NULL
    email: String(120) - UNIQUE, NOT NULL
    password_hash: String(256) - NOT NULL
    created_at: DateTime
    recipes: Relationship -> Recipe (backref)
    meal_plans: Relationship -> MealPlan
    shopping_lists: Relationship -> ShoppingList
```

### Recipe
```python
class Recipe(db.Model):
    id: Integer (PK)
    title: String(200) - NOT NULL
    description: Text
    instructions: Text - NOT NULL
    prep_time: Integer (minutes)
    cook_time: Integer (minutes)
    servings: Integer
    difficulty: String(20) - easy/medium/hard
    cuisine: String(50)
    image_url: String(500)
    created_at: DateTime
    updated_at: DateTime
    user_id: Integer (FK -> User)
    ingredients: Relationship -> RecipeIngredient
    meal_plans: Relationship -> MealPlan
```

### Ingredient
```python
class Ingredient(db.Model):
    id: Integer (PK)
    name: String(200) - UNIQUE, NOT NULL
    category: String(50) - produce/dairy/meat/pantry/etc
    default_unit: String(20)
    nutrition_per_100g: JSON - {calories, protein, carbs, fat, fiber}
```

### RecipeIngredient (M2M with quantity)
```python
class RecipeIngredient(db.Model):
    id: Integer (PK)
    recipe_id: Integer (FK -> Recipe)
    ingredient_id: Integer (FK -> Ingredient)
    quantity: Float - NOT NULL
    unit: String(20) - NOT NULL
    notes: String(100) - optional (e.g., "diced", "room temp")
```

### MealPlan
```python
class MealPlan(db.Model):
    id: Integer (PK)
    user_id: Integer (FK -> User)
    date: Date - NOT NULL
    meal_type: String(20) - breakfast/lunch/dinner/snack
    recipe_id: Integer (FK -> Recipe)
    servings: Integer
```

### ShoppingList
```python
class ShoppingList(db.Model):
    id: Integer (PK)
    user_id: Integer (FK -> User)
    name: String(200)
    created_at: DateTime
    items: Relationship -> ShoppingListItem

class ShoppingListItem(db.Model):
    id: Integer (PK)
    shopping_list_id: Integer (FK -> ShoppingList)
    ingredient_id: Integer (FK -> Ingredient)
    quantity: Float
    unit: String(20)
    checked: Boolean (default False)
```

---

## API Design

### Authentication Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create new user |
| POST | `/auth/login` | User login |
| POST | `/auth/logout` | User logout |
| GET | `/auth/profile` | Get current user |

### Recipe Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/recipes` | List all user recipes |
| GET | `/recipes/<id>` | Get recipe detail |
| POST | `/recipes` | Create recipe |
| PUT | `/recipes/<id>` | Update recipe |
| DELETE | `/recipes/<id>` | Delete recipe |
| GET | `/recipes/<id>/nutrition` | Get recipe nutrition |

### Search Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/search` | Search recipes by name |
| GET | `/search/ingredients` | Search by ingredient |
| GET | `/api/ingredients` | Autocomplete ingredients |

### Meal Plan Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/meal-plan` | Get meal plan (date range) |
| POST | `/meal-plan` | Add meal to plan |
| PUT | `/meal-plan/<id>` | Update meal entry |
| DELETE | `/meal-plan/<id>` | Remove meal from plan |
| GET | `/meal-plan/week` | Get current week plan |

### Shopping List Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/shopping-lists` | List all shopping lists |
| POST | `/shopping-lists` | Create from meal plan |
| PUT | `/shopping-lists/<id>/items/<item_id>` | Toggle item checked |
| DELETE | `/shopping-lists/<id>` | Delete shopping list |

### Nutrition Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/nutrition/dashboard` | Nutrition overview |
| GET | `/nutrition/recipe/<id>` | Recipe nutrition breakdown |
| GET | `/nutrition/meal-plan` | Weekly nutrition summary |

---

## UI/UX Design

### Color Palette (Dark Theme)
| Element | Color |
|---------|-------|
| Background Primary | `#0f172a` (slate-900) |
| Background Secondary | `#1e293b` (slate-800) |
| Background Card | `#334155` (slate-700) |
| Text Primary | `#f1f5f9` (slate-100) |
| Text Secondary | `#94a3b8` (slate-400) |
| Accent Primary | `#f59e0b` (amber-500) |
| Accent Hover | `#d97706` (amber-600) |
| Success | `#22c55e` (green-500) |
| Error | `#ef4444` (red-500) |
| Border | `#475569` (slate-600) |

### Typography
- **Headings:** Inter or system-ui, font-weight 600-700
- **Body:** Inter or system-ui, font-weight 400
- **Monospace:** For measurements/numbers

### Layout Structure
```
┌─────────────────────────────────────────────────────┐
│ HEADER: Logo | Nav Links | User Menu               │
├─────────────────────────────────────────────────────┤
│                                                     │
│  MAIN CONTENT AREA                                  │
│  (varies by page)                                  │
│                                                     │
├─────────────────────────────────────────────────────┤
│ FOOTER: Copyright | Links                          │
└─────────────────────────────────────────────────────┘
```

### Responsive Breakpoints
- Mobile: < 640px
- Tablet: 640px - 1024px
- Desktop: > 1024px

---

## Core Features Implementation

### 1. Recipe Management
- **Create:** Form with title, description, ingredients (dynamic add/remove), instructions, metadata
- **Read:** Card grid view, detail view with ingredients and steps
- **Update:** Pre-filled form with existing data
- **Delete:** Confirmation modal before deletion
- **Image:** URL field (no file upload for v1)

### 2. Ingredient Search
- Real-time autocomplete as user types
- Search by ingredient name
- Filter recipes containing specific ingredients
- "What can I make with..." feature (ingredient intersection)

### 3. Meal Planning
- Weekly calendar view (Mon-Sun)
- Drag-and-drop recipes onto days (optional v2)
- Meal types: Breakfast, Lunch, Dinner, Snack
- Multiple servings support
- Copy week to next week

### 4. Shopping List Generation
- Auto-generate from meal plan date range
- Combine duplicate ingredients (sum quantities)
- Group by ingredient category
- Checkbox to mark items purchased
- Manual add/remove items

### 5. Nutrition Tracking
- Per-recipe nutrition calculation
- Daily/weekly nutrition summaries
- Visual charts (simple CSS bars or library)
- Categories: Calories, Protein, Carbs, Fat

---

## Error Handling

### HTTP Error Codes
| Code | Meaning | Handling |
|------|---------|----------|
| 400 | Bad Request | Show form validation errors |
| 401 | Unauthorized | Redirect to login |
| 403 | Forbidden | Show "Access Denied" page |
| 404 | Not Found | Show "Not Found" page |
| 422 | Unprocessable | Form validation failed |
| 500 | Internal Error | Show error page, log details |

### Form Validation
- Server-side validation on ALL inputs
- Required field checks
- Length limits (title: 200, description: 2000, etc.)
- Email format validation
- Password strength requirements (min 8 chars)

### Database Errors
- Catch SQLAlchemy IntegrityError for duplicate entries
- Rollback on failed transactions
- Log database errors with context

### API Error Response Format
```json
{
  "error": true,
  "message": "Human readable error",
  "code": "ERROR_CODE",
  "details": {}
}
```

---

## Edge Cases

### Recipe Management
- Empty recipe list: Show "Add your first recipe" CTA
- Missing ingredients: Allow recipes without ingredients
- Long instructions: Handle with proper text formatting
- Special characters in names: Sanitize input

### Search
- No results: Show "No recipes found" with suggestions
- Very long search query: Truncate at 100 chars
- Special characters: Escape SQL LIKE wildcards

### Meal Planning
- Past dates: Allow editing (not just future)
- Same recipe multiple times: Allow duplicates
- Empty day: Show "No meals planned"

### Shopping List
- Zero ingredients: Warn user before creating
- Unit conversion: Default to ingredient's default_unit
- Ingredient not in database: Allow manual entry

### Nutrition
- Missing nutrition data: Show "Unknown" or estimate
- Zero servings: Prevent (minimum 1)
- Very large quantities: Cap display at reasonable max

### Authentication
- Duplicate username/email: Show specific error
- Session expiry: Redirect to login with message
- Password reset: Not in v1 scope

---

## Security Considerations

1. **Password Hashing:** Use Werkzeug generate_password_hash with pbkdf2:sha256
2. **CSRF Protection:** Flask-WTF (or manual CSRF tokens)
3. **SQL Injection:** SQLAlchemy ORM prevents this
4. **XSS Prevention:** Jinja2 auto-escapes
5. **Rate Limiting:** Optional (Flask-Limiter)
6. **Input Sanitization:** Strip whitespace, limit lengths

---

## Development Phases

### Phase 1: Foundation (Day 1)
- [ ] Project setup with Flask
- [ ] Database models and migrations
- [ ] Authentication (login/register)
- [ ] Base template with dark theme

### Phase 2: Recipe Core (Day 2)
- [ ] Recipe CRUD operations
- [ ] Ingredient management
- [ ] Recipe list and detail views

### Phase 3: Search & Discovery (Day 3)
- [ ] Ingredient search functionality
- [ ] Autocomplete for ingredients
- [ ] Recipe filtering

### Phase 4: Meal Planning (Day 4)
- [ ] Weekly meal plan view
- [ ] Add/remove meals from plan
- [ ] Date navigation

### Phase 5: Shopping & Nutrition (Day 5)
- [ ] Shopping list generation
- [ ] Shopping list management
- [ ] Basic nutrition calculations

### Phase 6: Polish (Day 6)
- [ ] Error pages
- [ ] Responsive design check
- [ ] Edge case handling
- [ ] Testing

---

## Acceptance Criteria

1. ✓ User can register and login
2. ✓ User can create, view, edit, delete recipes
3. ✓ User can search recipes by ingredient
4. ✓ User can plan meals for the week
5. ✓ User can generate shopping list from meal plan
6. ✓ User can view nutrition information
7. ✓ Dark theme is applied consistently
8. ✓ All forms have proper validation
9. ✓ Error states are handled gracefully
10. ✓ Application is responsive on mobile

---

## Future Enhancements (Post-v1)

- Recipe image upload
- Meal plan drag-and-drop
- Grocery delivery integration
- Recipe sharing
- Shopping list export (PDF)
- Recipe categories/tags
- Cooking timer
- Kitchen inventory
- Import from URL (recipe scraping)
- Multiple users/households
