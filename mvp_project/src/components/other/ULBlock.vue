<template>
  <ul class="ulblock">
    <div class="ulblock__title">
      <slot />
      <div class="h5 m-0">{{ title }}</div>
    </div>
    <li v-for="item in list" :key="item" v-html="item"></li>
  </ul>
</template>

<script>
export default {
  name: 'ULBlock',
  props: {
    title: String,
    list: Object,
  }
};
</script>
<style lang="scss">
@import '../../scss/constants';

.ulblock {
  li {
    margin-left: 32px;
  }

  &__title {
    display: flex;
    align-items: center;
    margin-bottom: 10px;
  }

  &__icon {
    $-size: 30px;

    display: block;
    margin-right: 16px;
    min-width: $-size;
    width: $-size;
    height: $-size;

    path {
      fill: $color-dark;
    }
  }
}
</style>