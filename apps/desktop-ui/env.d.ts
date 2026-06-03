/// <reference types="vite/client" />

interface PyWebViewApi {
  pick_files(): Promise<string[]>
  pick_output_dir(): Promise<string | null>
  open_folder(path: string): Promise<void>
}

interface PyWebView {
  api?: PyWebViewApi
}

declare global {
  interface Window {
    pywebview?: PyWebView
  }
}

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<object, object, unknown>
  export default component
}

export {}
