import { computed, ref, shallowRef, watch } from 'vue'
import { useWebSocket } from '@vueuse/core'
import type { CreateJobResponse, FileItem, JobEvent, JobSummary } from '../types'
import { fileNameFromPath } from '../utils/format'

function wsBaseUrl(): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/api/ws`
}

export function useCompressJob() {
  const files = ref<FileItem[]>([])
  const maxMb = ref(1.0)
  const outputDir = ref('')
  const isRunning = ref(false)
  const jobDone = ref(false)
  const jobError = ref<string | null>(null)
  const activeJobId = shallowRef<string | null>(null)

  const wsUrl = computed(() =>
    activeJobId.value ? `${wsBaseUrl()}?job_id=${activeJobId.value}` : undefined,
  )

  const { open, close, data } = useWebSocket(wsUrl, {
    immediate: false,
    autoReconnect: false,
  })

  const summary = computed<JobSummary>(() => {
    let totalSaved = 0
    let succeeded = 0
    let failed = 0

    for (const file of files.value) {
      if (file.status === 'done' && file.srcSize != null && file.dstSize != null) {
        totalSaved += Math.max(0, file.srcSize - file.dstSize)
        succeeded++
      } else if (file.status === 'error') {
        failed++
      }
    }

    return { totalSaved, succeeded, failed }
  })

  const canStart = computed(
    () => files.value.length > 0 && outputDir.value.length > 0 && !isRunning.value,
  )

  function addFiles(paths: string[]) {
    for (const path of paths) {
      if (!path) continue
      const name = fileNameFromPath(path)
      if (files.value.some((item) => item.path === path)) continue
      files.value.push({ path, name, status: 'pending' })
    }
    jobDone.value = false
    jobError.value = null
  }

  function resetFiles() {
    for (const file of files.value) {
      file.status = 'pending'
      file.srcSize = undefined
      file.dstSize = undefined
      file.error = undefined
    }
    jobDone.value = false
    jobError.value = null
  }

  function findFileByName(name: string): FileItem | undefined {
    return files.value.find((item) => item.name === name)
  }

  function handleEvent(event: JobEvent) {
    switch (event.type) {
      case 'file_start': {
        const file = findFileByName(event.file)
        if (file) file.status = 'running'
        break
      }
      case 'file_done': {
        const file = findFileByName(event.file)
        if (!file) break
        file.srcSize = event.src_size
        file.dstSize = event.dst_size
        if (event.error) {
          file.status = 'error'
          file.error = event.error
        } else {
          file.status = 'done'
        }
        break
      }
      case 'job_done':
        isRunning.value = false
        jobDone.value = true
        close()
        break
      case 'job_failed':
        isRunning.value = false
        jobError.value = event.error
        close()
        break
    }
  }

  watch(data, (raw) => {
    if (!raw) return
    try {
      handleEvent(JSON.parse(raw) as JobEvent)
    } catch {
      // ignore malformed messages
    }
  })

  async function startJob() {
    if (!canStart.value) return

    close()
    resetFiles()
    isRunning.value = true
    jobError.value = null

    try {
      const response = await fetch('/api/jobs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          files: files.value.map((item) => item.path),
          max_mb: maxMb.value,
          output_dir: outputDir.value,
        }),
      })

      if (!response.ok) {
        const detail = await response.json().catch(() => ({}))
        throw new Error(detail.detail ?? `请求失败 (${response.status})`)
      }

      const job = (await response.json()) as CreateJobResponse
      activeJobId.value = job.id
      open()
    } catch (err) {
      isRunning.value = false
      jobError.value = err instanceof Error ? err.message : '启动任务失败'
    }
  }

  return {
    files,
    maxMb,
    outputDir,
    isRunning,
    jobDone,
    jobError,
    summary,
    canStart,
    addFiles,
    startJob,
  }
}
