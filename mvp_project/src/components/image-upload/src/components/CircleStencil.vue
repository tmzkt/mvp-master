<template>
  <div class="circle-stencil" :style="style">
    <DraggableElement class="circle-stencil__handler" @drag="onHandlerMove">
      <img src="/static/components/image-upload/img/handler.svg" alt />
    </DraggableElement>
    <DraggableArea @move="onMove">
      <PreviewResult
        class="circle-stencil__preview"
        :img="img"
        :stencilCoordinates="stencilCoordinates"
        :resultCoordinates="resultCoordinates"
      />
    </DraggableArea>
  </div>
</template>

<script>
import {
  DraggableElement,
  DraggableArea,
  PreviewResult,
  ResizeEvent
} from 'vue-advanced-cropper'

export default {
  name: 'CircleStencil',
  components: {
    PreviewResult,
    DraggableArea,
    DraggableElement
  },
  props: {
    img: {
      type: Object
    },
    resultCoordinates: {
      type: Object
    },
    stencilCoordinates: {
      type: Object
    }
  },
  computed: {
    style() {
      const { height, width, left, top } = this.stencilCoordinates
      return {
        width: `${width}px`,
        height: `${height}px`,
        left: `${left}px`,
        top: `${top}px`
      }
    }
  },
  methods: {
    onMove(moveEvent) {
      this.$emit('move', moveEvent)
    },
    onHandlerMove(dragEvent) {
      const shift = dragEvent.shift()

      const widthResize = shift.left
      const heightResize = -shift.top

      this.$emit(
        'resize',
        new ResizeEvent(dragEvent.nativeEvent, {
          left: widthResize,
          right: widthResize,
          top: heightResize,
          bottom: heightResize
        })
      )
    },
    aspectRatios() {
      return {
        minimum: 1,
        maximum: 1
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.circle-stencil {
  border-radius: 50%;
  cursor: move;
  position: absolute;
  border: dashed 2px white;
  box-sizing: border-box;
}

.circle-stencil__handler {
  position: absolute;
  right: 15%;
  top: 14%;
  z-index: 1;
  cursor: ne-resize;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  transform: translate(50%, -50%);
}

.circle-stencil__preview {
  border-radius: 50%;
  overflow: hidden;
}
</style>
