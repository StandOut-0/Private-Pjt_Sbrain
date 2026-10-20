# React Frontend

React + TypeScript UI, Django remains responsible for session authentication, access control, API responses, and file permissions.

## Build and run

```powershell
cd front/react
npm install
npm run build
cd ../
.\.venv\Scripts\python.exe manage.py runserver
```

All primary application routes load the Vite production bundle from `front/static/react/` through `manifest.json`. The Django views continue to enforce session and role permissions and provide page data as JSON; React renders the shared authenticated shell and all page content. Rebuild after changing React source.

To run Vite's standalone development preview, use `npm run dev` and open `http://127.0.0.1:5173/`. The preview uses local example data; the Django integrated Dashboard uses the production build.

## Libraries

- React + TypeScript: UI and typed contracts
- React Router: page routing
- TanStack Query: server data cache and request state
- Zustand: UI-only global state
- React Hook Form + Zod: form state and validation
- Tailwind CSS + shadcn/ui patterns + Radix UI: shared UI primitives
- lucide-react: icons

Dashboard, Projects, management, Coming Soon, FAQ, user guide, and login/authentication views now render through React. Django continues handling authentication, role checks, form submissions, file operations, and the project chat stub. Current page data comes from `apps/mockdata.py` or the Coming Soon Markdown files; this UI conversion does not imply database-backed live Agent functionality. The authenticated React shell implements navigation, theme settings, notification and invitation dialogs; the existing screen-tour script is retained for its guided-tour behavior.
