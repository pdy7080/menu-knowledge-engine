# Menu Guide Korea - Frontend

B2C Mobile Web Interface for Menu Knowledge Engine

## 📱 Features

- **Text Search**: Enter Korean menu names and get instant translations
- **Multi-menu Search**: Search multiple menus separated by comma or newline
- **Popular Dishes**: Quick access to common Korean dishes
- **Mobile-First Design**: Optimized for mobile (480px), works on desktop too
- **Real-time API Integration**: Connects to FastAPI backend

## 🚀 Quick Start

### 1. Start Backend Server

```bash
cd C:\project\menu\app\backend
uvicorn main:app --reload --port 8000
```

Backend will run on: http://localhost:8000

### 2. Serve Frontend

**Option A: Python HTTP Server**
```bash
cd C:\project\menu\app\frontend
python -m http.server 8080
```

**Option B: VS Code Live Server**
1. Install "Live Server" extension
2. Right-click on `index.html`
3. Select "Open with Live Server"

Frontend will run on: http://localhost:8080 or http://localhost:5500

### 3. Open in Browser

Navigate to: http://localhost:8080 (or your Live Server port)

## 🧪 Test Cases

1. **Basic Search**
   - Enter: `김치찌개`
   - Expected: Match with description and allergens

2. **Modifier Decomposition**
   - Enter: `왕얼큰순두부찌개`
   - Expected: Show modifiers (왕=Extra Large, 얼큰=Spicy)

3. **AI Discovery**
   - Enter: `스테이크` (not in Korean menu database)
   - Expected: "Analyzing..." message

4. **Multiple Menus**
   - Enter: `비빔밥, 김치찌개, 떡볶이`
   - Expected: 3 result cards

5. **Popular Dishes**
   - Click: `냉면` tag
   - Expected: Instant search for 냉면

## 📁 File Structure

```
frontend/
├── index.html          # Main HTML file
├── css/
│   └── style.css      # Styles (mobile-first)
├── js/
│   └── app.js         # Application logic & API calls
└── assets/            # Future: images, icons
```

## 🎨 Design System

### Colors
- Base: `#FFF8F0` (warm cream)
- Accent: `#E85D3A` (Korean red)
- Card: `#FFFFFF`

### Fonts
- Korean: Noto Sans KR
- English: Inter

### Breakpoints
- Mobile: 0-480px (primary)
- Tablet: 481-768px
- Desktop: 769px+

## 🔧 API Integration

### Endpoint Used
```
POST /api/v1/menu/identify
{
  "menu_name_ko": "김치찌개"
}
```

### Response Handling
- `exact`: Direct match found
- `modifier_decomposition`: Menu with modifiers
- `similarity`: Typo correction match
- `ai_discovery_needed`: Not in database (AI needed)

## 🚧 Coming Soon (v0.2+)

- [ ] Photo upload & OCR
- [ ] Multi-language support (日本語, 中文)
- [ ] Offline favorites
- [ ] Share results

## 📝 Version

**v0.1** - Sprint 2 MVP
Mobile-first text search with real-time API integration
