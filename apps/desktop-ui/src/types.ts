export type FileStatus = 'pending' | 'running' | 'done' | 'error'

export interface FileItem {
  path: string
  name: string
  status: FileStatus
  srcSize?: number
  dstSize?: number
  error?: string
}

export interface JobSummary {
  totalSaved: number
  succeeded: number
  failed: number
}

export type JobEvent =
  | { type: 'file_start'; file: string }
  | {
      type: 'file_done'
      file: string
      src_size: number
      dst_size: number
      zoom?: number
      quality?: number
      exceeded_target?: boolean
      error?: string | null
    }
  | { type: 'job_done'; job_id: string }
  | { type: 'job_failed'; error: string }

export interface CreateJobResponse {
  id: string
  status: string
  files: string[]
  max_mb: number
  output_dir: string
}
