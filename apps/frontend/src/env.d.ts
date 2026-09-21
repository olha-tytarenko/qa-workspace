interface ImportMetaEnv {
  /** Base URL of the backend API, without the `/api` prefix. See `.env.example`. */
  readonly VITE_API_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
