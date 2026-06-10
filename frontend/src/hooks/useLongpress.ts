import { onMounted, onUnmounted, ref } from 'vue'

export function useLongpress(options: { handler: () => void; delay?: number }) {
  const delay = options.delay || 500
  let timer: ReturnType<typeof setTimeout> | null = null
  let triggered = false

  function start(e: TouchEvent | MouseEvent) {
    triggered = false
    timer = setTimeout(() => {
      triggered = true
      options.handler()
    }, delay)
  }

  function cancel() {
    if (timer) clearTimeout(timer)
    timer = null
  }

  return {
    onTouchstart: start,
    onTouchend: cancel,
    onTouchmove: cancel,
    onMousedown: start,
    onMouseup: cancel,
    onMouseleave: cancel,
  }
}
