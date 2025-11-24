# English Practice Bot - Mini App

Telegram Mini App for viewing analytics and progress tracking.

## Features

- 📊 **Analytics Dashboard** - View your learning statistics
- 💬 **Message Tracking** - Track voice and text messages
- ❌ **Error Analysis** - See breakdown of grammar errors
- 🔥 **Streak Counter** - Monitor your practice consistency
- 📈 **Charts** - Visualize your progress over time

## Tech Stack

- **Frontend:** React 18 + Vite
- **Charts:** Chart.js + react-chartjs-2
- **Telegram SDK:** @telegram-apps/sdk-react
- **Styling:** CSS with Telegram theme variables

## Development Setup

### Prerequisites

- Node.js 18+ and npm
- Running FastAPI backend (see `api/` folder)

### Installation

```bash
cd miniapp
npm install
```

### Configuration

Create a `.env` file:

```env
VITE_API_URL=http://localhost:8000
```

For production, set this to your deployed API URL.

### Run Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:3000`.

### Testing in Telegram

To test the Mini App in Telegram during development:

1. Use a tunneling service like [ngrok](https://ngrok.com/) to expose your local server:
   ```bash
   ngrok http 3000
   ```

2. Update the WebApp URL in `handlers/start.py` with the ngrok URL

3. Open your bot in Telegram and click the Mini App button

## Build for Production

```bash
npm run build
```

This creates an optimized build in the `dist/` folder.

## Deployment

### Deploy to Vercel

1. Push your code to GitHub

2. Go to [Vercel](https://vercel.com/) and import your repository

3. Configure build settings:
   - **Framework Preset:** Vite
   - **Root Directory:** `miniapp`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`

4. Add environment variable:
   - `VITE_API_URL` = `https://your-api-domain.com`

5. Deploy!

6. Update the WebApp URL in `handlers/start.py` with your Vercel URL:
   ```python
   web_app=WebAppInfo(url="https://your-app.vercel.app")
   ```

### Deploy to Netlify

Similar process:

1. Connect your GitHub repository to Netlify

2. Configure build:
   - **Base directory:** `miniapp`
   - **Build command:** `npm run build`
   - **Publish directory:** `miniapp/dist`

3. Add environment variable:
   - `VITE_API_URL` = `https://your-api-domain.com`

4. Deploy and update bot with new URL

## Project Structure

```
miniapp/
├── public/              # Static assets
├── src/
│   ├── components/      # React components
│   │   ├── Dashboard.jsx    # Main dashboard
│   │   ├── StatsCard.jsx    # Stats display card
│   │   └── Charts.jsx       # Chart components
│   ├── services/        # API client
│   │   └── api.js       # Backend communication
│   ├── App.jsx          # Root component
│   ├── App.css          # App styles
│   ├── main.jsx         # Entry point
│   └── index.css        # Global styles
├── index.html           # HTML template
├── package.json         # Dependencies
└── vite.config.js       # Vite configuration
```

## Telegram WebApp Integration

The app uses Telegram WebApp API to:

- Get user information (`window.Telegram.WebApp.initDataUnsafe.user`)
- Authenticate requests (`window.Telegram.WebApp.initData`)
- Match Telegram theme (`var(--tg-theme-bg-color)`)
- Show alerts (`window.Telegram.WebApp.showAlert()`)

## API Endpoints Used

- `GET /api/analytics/{user_id}` - Get user analytics
- `GET /api/charts/{user_id}?days=7` - Get chart data
- `POST /api/auth/validate` - Validate authentication

All requests include `X-Telegram-Init-Data` header for authentication.

## Troubleshooting

### "Could not get user data from Telegram"

This error appears when the app is not opened through Telegram. The Mini App must be accessed via the WebApp button in the bot.

### "Failed to load analytics"

Check that:
1. The API backend is running and accessible
2. `VITE_API_URL` is correctly configured
3. CORS is enabled in the API for your domain
4. The user has sent at least one message to the bot

### Blank screen in Telegram

Check the browser console (Telegram Desktop: Settings → Advanced → Enable debug) for errors.

## Future Features

- ⭐ Premium subscription UI
- ⚙️ Settings page
- 📤 Export analytics data
- 🎯 Goal setting and tracking
- 🏆 Achievements and badges

## License

Part of the English Practice Bot project.

