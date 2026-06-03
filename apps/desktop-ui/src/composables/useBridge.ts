function pathFromFile(file: File): string {
  return (file as File & { path?: string }).path ?? file.name
}

function pickFilesViaInput(accept: string, multiple: boolean): Promise<string[]> {
  return new Promise((resolve) => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = accept
    input.multiple = multiple
    input.style.display = 'none'
    document.body.appendChild(input)

    input.addEventListener('change', () => {
      const paths = Array.from(input.files ?? []).map(pathFromFile)
      input.remove()
      resolve(paths)
    })

    input.addEventListener('cancel', () => {
      input.remove()
      resolve([])
    })

    input.click()
  })
}

export function useBridge() {
  async function pickFiles(): Promise<string[]> {
    if (window.pywebview?.api?.pick_files) {
      return window.pywebview.api.pick_files()
    }
    return pickFilesViaInput('.pdf,application/pdf', true)
  }

  async function pickOutputDir(): Promise<string | null> {
    if (window.pywebview?.api?.pick_output_dir) {
      return window.pywebview.api.pick_output_dir()
    }
    const dir = window.prompt('输出目录路径（浏览器开发模式）')
    return dir?.trim() || null
  }

  async function openFolder(path: string): Promise<void> {
    if (window.pywebview?.api?.open_folder) {
      await window.pywebview.api.open_folder(path)
      return
    }
    console.info('open_folder:', path)
  }

  function pathsFromDroppedFiles(files: FileList | File[]): string[] {
    return Array.from(files)
      .filter((file) => file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf'))
      .map(pathFromFile)
  }

  return {
    pickFiles,
    pickOutputDir,
    openFolder,
    pathsFromDroppedFiles,
  }
}
