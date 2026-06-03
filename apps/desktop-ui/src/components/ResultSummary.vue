<script setup lang="ts">
import type { JobSummary } from '../types'
import { formatBytes } from '../utils/format'
import { useBridge } from '../composables/useBridge'

const props = defineProps<{
  summary: JobSummary
  outputDir: string
  jobError: string | null
}>()

const { openFolder } = useBridge()

function onOpenFolder() {
  if (props.outputDir) openFolder(props.outputDir)
}
</script>

<template>
  <section class="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-gray-900">
    <div class="border-b border-gray-100 px-5 py-3 dark:border-gray-800">
      <h2 class="text-sm font-semibold text-gray-900 dark:text-gray-100">
        压缩结果
      </h2>
    </div>

    <div
      v-if="jobError"
      class="mx-5 mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300"
    >
      {{ jobError }}
    </div>

    <div class="grid grid-cols-3 gap-4 p-5">
      <div class="rounded-lg bg-gray-50 px-3 py-3 dark:bg-gray-800/60">
        <p class="text-xs text-gray-500 dark:text-gray-400">
          节省空间
        </p>
        <p class="mt-1 text-lg font-semibold tabular-nums text-teal-600 dark:text-teal-400">
          {{ formatBytes(summary.totalSaved) }}
        </p>
      </div>
      <div class="rounded-lg bg-gray-50 px-3 py-3 dark:bg-gray-800/60">
        <p class="text-xs text-gray-500 dark:text-gray-400">
          成功
        </p>
        <p class="mt-1 text-lg font-semibold tabular-nums text-green-600 dark:text-green-400">
          {{ summary.succeeded }}
        </p>
      </div>
      <div class="rounded-lg bg-gray-50 px-3 py-3 dark:bg-gray-800/60">
        <p class="text-xs text-gray-500 dark:text-gray-400">
          失败
        </p>
        <p class="mt-1 text-lg font-semibold tabular-nums text-red-500 dark:text-red-400">
          {{ summary.failed }}
        </p>
      </div>
    </div>

    <div class="border-t border-gray-100 px-5 py-4 dark:border-gray-800">
      <button
        type="button"
        class="inline-flex items-center rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm text-gray-700 transition-colors hover:border-teal-300 hover:text-teal-700 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200 dark:hover:border-teal-600 dark:hover:text-teal-300"
        :disabled="!outputDir"
        @click="onOpenFolder"
      >
        打开输出文件夹
      </button>
    </div>
  </section>
</template>
