<script setup lang="ts">
import type { FileItem } from '../types'
import { compressionRatio, formatBytes } from '../utils/format'

defineProps<{
  files: FileItem[]
}>()

const statusLabel: Record<FileItem['status'], string> = {
  pending: '等待',
  running: '压缩中',
  done: '完成',
  error: '失败',
}

const statusClass: Record<FileItem['status'], string> = {
  pending: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300',
  running: 'bg-teal-50 text-teal-700 dark:bg-teal-950 dark:text-teal-300',
  done: 'bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300',
  error: 'bg-red-50 text-red-600 dark:bg-red-950 dark:text-red-400',
}
</script>

<template>
  <section
    v-if="files.length"
    class="rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-gray-900"
  >
    <div class="flex items-center justify-between border-b border-gray-100 px-5 py-3 dark:border-gray-800">
      <h2 class="text-sm font-semibold text-gray-900 dark:text-gray-100">
        文件列表
      </h2>
      <span class="text-xs text-gray-500 dark:text-gray-400">{{ files.length }} 个文件</span>
    </div>

    <ul class="divide-y divide-gray-100 dark:divide-gray-800">
      <li
        v-for="file in files"
        :key="file.path"
        class="flex items-start gap-4 px-5 py-3.5"
      >
        <div class="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-red-50 dark:bg-red-950/40">
          <span class="text-xs font-bold text-red-500">PDF</span>
        </div>

        <div class="min-w-0 flex-1">
          <div class="flex flex-wrap items-center gap-2">
            <p
              class="truncate text-sm font-medium text-gray-900 dark:text-gray-100"
              :title="file.name"
            >
              {{ file.name }}
            </p>
            <span
              class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
              :class="statusClass[file.status]"
            >
              {{ statusLabel[file.status] }}
            </span>
          </div>

          <p
            v-if="file.status === 'done' && file.srcSize != null && file.dstSize != null"
            class="mt-1 text-xs text-gray-500 dark:text-gray-400"
          >
            {{ formatBytes(file.srcSize) }} → {{ formatBytes(file.dstSize) }}
            <span class="ml-1 text-teal-600 dark:text-teal-400">
              节省 {{ compressionRatio(file.srcSize, file.dstSize) }}
            </span>
          </p>

          <p
            v-else-if="file.status === 'error'"
            class="mt-1 text-xs text-red-500"
          >
            {{ file.error || '压缩失败' }}
          </p>

          <p
            v-else
            class="mt-1 truncate text-xs text-gray-400"
            :title="file.path"
          >
            {{ file.path }}
          </p>

          <div
            v-if="file.status === 'running'"
            class="mt-2 h-1.5 overflow-hidden rounded-full bg-gray-100 dark:bg-gray-800"
          >
            <div class="progress-bar h-full rounded-full bg-teal-500" />
          </div>
        </div>
      </li>
    </ul>
  </section>

  <section
    v-else
    class="flex items-center justify-center rounded-xl border border-gray-200 bg-white px-5 py-10 text-sm text-gray-400 shadow-sm dark:border-gray-800 dark:bg-gray-900 dark:text-gray-500"
  >
    尚未添加文件
  </section>
</template>

<style scoped>
.progress-bar {
  width: 40%;
  animation: progress 1.2s ease-in-out infinite;
}

@keyframes progress {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(350%);
  }
}
</style>
