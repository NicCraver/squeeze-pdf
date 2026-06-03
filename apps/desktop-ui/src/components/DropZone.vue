<script setup lang="ts">
import { ref } from 'vue'
import { useBridge } from '../composables/useBridge'

const emit = defineEmits<{
  addFiles: [paths: string[]]
}>()

defineProps<{
  disabled?: boolean
}>()

const { pickFiles, pathsFromDroppedFiles } = useBridge()
const isDragging = ref(false)

async function onClick() {
  const paths = await pickFiles()
  if (paths.length) emit('addFiles', paths)
}

function onDragOver(event: DragEvent) {
  event.preventDefault()
  isDragging.value = true
}

function onDragLeave() {
  isDragging.value = false
}

function onDrop(event: DragEvent) {
  event.preventDefault()
  isDragging.value = false
  if (!event.dataTransfer?.files.length) return
  const paths = pathsFromDroppedFiles(event.dataTransfer.files)
  if (paths.length) emit('addFiles', paths)
}
</script>

<template>
  <div
    class="cursor-pointer rounded-xl border-2 border-dashed border-gray-300 bg-white/60 transition-all hover:border-teal-400 hover:bg-teal-50/40 dark:border-gray-700 dark:bg-gray-900/40 dark:hover:border-teal-500 dark:hover:bg-teal-950/30"
    :class="{
      'scale-[1.01] border-teal-500 bg-teal-50/60 dark:border-teal-400 dark:bg-teal-950/40': isDragging,
      'cursor-not-allowed opacity-50 hover:border-gray-300 hover:bg-white/60 dark:hover:border-gray-700 dark:hover:bg-gray-900/40': disabled,
    }"
    @click="!disabled && onClick()"
    @dragover="onDragOver"
    @dragleave="onDragLeave"
    @drop="onDrop"
  >
    <div class="pointer-events-none flex flex-col items-center gap-3 py-8">
      <div class="flex h-14 w-14 items-center justify-center rounded-full bg-teal-50 dark:bg-teal-950/60">
        <svg class="h-7 w-7 text-teal-600 dark:text-teal-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
      </div>
      <div class="text-center">
        <p class="text-sm font-medium text-gray-800 dark:text-gray-100">
          拖拽 PDF 到此处，或点击选择文件
        </p>
        <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
          支持多文件批量压缩
        </p>
      </div>
    </div>
  </div>
</template>
