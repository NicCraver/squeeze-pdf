<script setup lang="ts">
import { useBridge } from '../composables/useBridge'

const maxMb = defineModel<number>('maxMb', { required: true })
const outputDir = defineModel<string>('outputDir', { required: true })

defineProps<{
  canStart: boolean
  isRunning: boolean
}>()

const emit = defineEmits<{
  start: []
}>()

const { pickOutputDir } = useBridge()

async function onPickOutputDir() {
  const dir = await pickOutputDir()
  if (dir) outputDir.value = dir
}
</script>

<template>
  <aside class="flex flex-col gap-6 rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-gray-900">
    <div>
      <h2 class="text-sm font-semibold text-gray-900 dark:text-gray-100">
        压缩设置
      </h2>
      <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
        调整目标大小与输出位置
      </p>
    </div>

    <div class="space-y-3">
      <div class="flex items-center justify-between">
        <label class="text-sm text-gray-700 dark:text-gray-300">目标大小</label>
        <span class="rounded-md bg-teal-50 px-2 py-0.5 text-sm font-medium text-teal-700 dark:bg-teal-950 dark:text-teal-300">
          {{ maxMb.toFixed(1) }} MB
        </span>
      </div>
      <input
        v-model.number="maxMb"
        type="range"
        min="0.1"
        max="10"
        step="0.1"
        :disabled="isRunning"
        class="h-2 w-full cursor-pointer appearance-none rounded-full bg-gray-200 accent-teal-600 disabled:opacity-50 dark:bg-gray-700"
      >
      <div class="flex justify-between text-xs text-gray-400">
        <span>0.1 MB</span>
        <span>10 MB</span>
      </div>
    </div>

    <div class="space-y-2">
      <label class="text-sm text-gray-700 dark:text-gray-300">输出目录</label>
      <div
        class="min-h-10 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-xs break-all text-gray-600 dark:border-gray-700 dark:bg-gray-800/50 dark:text-gray-300"
        :title="outputDir || '未选择'"
      >
        {{ outputDir || '未选择输出目录' }}
      </div>
      <button
        type="button"
        class="inline-flex w-full items-center justify-center rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm text-gray-700 transition-colors hover:border-teal-300 hover:text-teal-700 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200 dark:hover:border-teal-600 dark:hover:text-teal-300"
        :disabled="isRunning"
        @click="onPickOutputDir"
      >
        选择目录
      </button>
    </div>

    <button
      type="button"
      class="mt-auto inline-flex w-full items-center justify-center rounded-lg bg-teal-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-teal-700 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-teal-500 dark:hover:bg-teal-600"
      :disabled="!canStart"
      @click="emit('start')"
    >
      {{ isRunning ? '压缩中…' : '开始压缩' }}
    </button>
  </aside>
</template>
