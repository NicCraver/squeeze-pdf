<script setup lang="ts">
import { useDark } from '@vueuse/core'
import { useCompressJob } from './composables/useCompressJob'
import SettingsPanel from './components/SettingsPanel.vue'
import DropZone from './components/DropZone.vue'
import FileList from './components/FileList.vue'
import ResultSummary from './components/ResultSummary.vue'

useDark({
  selector: 'html',
  attribute: 'class',
  valueDark: 'dark',
  valueLight: '',
})

const {
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
} = useCompressJob()
</script>

<template>
  <div class="min-h-screen bg-gray-50 text-gray-900 dark:bg-gray-950 dark:text-gray-100">
    <header class="border-b border-gray-200 bg-white/80 backdrop-blur dark:border-gray-800 dark:bg-gray-900/80">
      <div class="mx-auto flex max-w-6xl items-center gap-3 px-4 py-4 sm:px-6">
        <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-600 text-xs font-bold text-white shadow-sm">
          PDF
        </div>
        <div>
          <h1 class="text-lg font-semibold tracking-tight">
            squeeze-pdf
          </h1>
          <p class="text-xs text-gray-500 dark:text-gray-400">
            轻量 PDF 压缩工具
          </p>
        </div>
      </div>
    </header>

    <main class="mx-auto max-w-6xl px-4 py-6 sm:px-6">
      <div class="grid gap-6 lg:grid-cols-[18rem_1fr]">
        <SettingsPanel
          v-model:max-mb="maxMb"
          v-model:output-dir="outputDir"
          :can-start="canStart"
          :is-running="isRunning"
          @start="startJob"
        />

        <div class="flex min-w-0 flex-col gap-4">
          <DropZone
            :disabled="isRunning"
            @add-files="addFiles"
          />
          <FileList :files="files" />
          <ResultSummary
            v-if="jobDone || jobError"
            :summary="summary"
            :output-dir="outputDir"
            :job-error="jobError"
          />
        </div>
      </div>
    </main>
  </div>
</template>
