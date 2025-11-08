# Aidem AI Frontend

Modern, clean React frontend for Aidem AI built with Vite, TypeScript, and Tailwind CSS.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm/yarn
- Backend API running on `http://localhost:5002`

### Setup

1. **Install dependencies:**
```bash
npm install
# or
yarn install
```

2. **(Optional) Set up environment variables:**
```bash
cp .env.example .env
```

By default, the Vite dev server proxies `/api/*` to the backend on `http://localhost:5002`, so you can skip configuring an API URL for local development. Add values only when pointing at a different backend or hosted Supabase project:
```env
# Only required if you are NOT using the built-in dev proxy
VITE_API_BASE=https://your-api-host.example.com

VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

3. **Start development server:**
```bash
npm run dev
# or
yarn dev
```

The app will be available at `http://localhost:3000` and forwards `/api/*` calls to `http://localhost:5002`.

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/              # Reusable UI components
│   │   ├── CopilotChat.tsx  # Main chat interface
│   │   └── TermSheetViewer.tsx  # Term sheet display
│   ├── lib/
│   │   ├── apiClient.ts     # API client with auth
│   │   └── supabase.ts      # Supabase client
│   ├── pages/
│   │   └── Home.tsx         # Main app page
│   ├── types/
│   │   └── index.ts         # TypeScript types
│   ├── App.tsx              # Root component
│   ├── main.tsx             # Entry point
│   └── index.css            # Global styles
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

## 🏗️ What Was Ported

From the old `frontend-cra-old/`, we ported:

- ✅ **API Client** - Clean axios wrapper with Supabase auth
- ✅ **Supabase Integration** - Authentication setup
- ✅ **CopilotChat** - Core chat functionality (simplified)
- ✅ **Term Sheet Viewer** - Markdown-based term sheet display
- ✅ **Basic UI Components** - Button, Textarea, Badge
- ✅ **Type Definitions** - TypeScript types for API responses

## 🗑️ What Was Removed

We intentionally removed legacy code:

- ❌ Multiple overlapping chat managers
- ❌ Complex chip-based information architecture
- ❌ Unused persona intake forms
- ❌ Legacy session management
- ❌ Overly complex state management
- ❌ Heavy UI component dependencies

## 🎨 Tech Stack

- **Vite** - Fast build tool and dev server
- **React 19** - UI framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first styling
- **React Markdown** - Markdown rendering
- **Axios** - HTTP client
- **Lucide React** - Icon library

## 📦 Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## 🔌 Backend Integration

The frontend expects these backend endpoints:

- `POST /api/copilot/chat` - General chat
- `POST /api/copilot/intent` - Intent-specific requests
- `POST /api/copilot/generate-term-sheet` - Generate term sheets

## 🎯 Next Steps

1. Add more UI components as needed
2. Implement advanced features (live markdown editing, redlines)
3. Add authentication UI
4. Integrate term sheet generation flow
5. Add document export functionality

## 📝 Notes

- This is a **fresh start** - no legacy baggage
- TypeScript everywhere for type safety
- Minimal dependencies
- Easy to extend and maintain

