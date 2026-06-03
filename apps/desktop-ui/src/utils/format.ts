export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

export function compressionRatio(src: number, dst: number): string {
  if (src <= 0) return '0%'
  const ratio = ((1 - dst / src) * 100)
  return `${ratio.toFixed(1)}%`
}

export function fileNameFromPath(path: string): string {
  return path.split(/[/\\]/).pop() ?? path
}
