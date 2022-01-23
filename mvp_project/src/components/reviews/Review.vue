<template>
  <div class="review__item">
    <div class="review__ava">
      <img :src="authorUrl" :alt="authorName" class="review__ava-img">
    </div>
    <div class="review__item-content">
      <div class="review__item-text">{{ text }}</div>
      <div class="review__item-author">{{ authorName }}</div>
    </div>
  </div>
</template>
<script>
export default {
  name: 'Review',
  props: {
    text: String,
    authorName: String,
    authorUrl: String,
  }
}
</script>
