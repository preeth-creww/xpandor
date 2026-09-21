# xpandor.net

Website for [xpandor.net](https://xpandor.net), built with Astro and deployed on Cloudflare Pages.

## 🚀 Local Development

```bash
npm install
npm run dev
```

Open `http://localhost:4321` in your browser.

## 📦 Build

```bash
npm run build
```

The output will be generated in `./dist`.

## ☁️ Deployment

Deployments are automated through **Cloudflare Pages**:
- **Framework Preset:** Astro
- **Build Command:** `npm run build`
- **Output Directory:** `dist`
- Any push to `main` triggers a live deployment.
