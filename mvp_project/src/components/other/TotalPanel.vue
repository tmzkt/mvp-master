<i18n>
{
  "en": {
    "title": "Global statistics",
    "newConfirmed": "New confirmed",
    "totalDeaths": "Total deaths",
    "totalRecovered": "Total recovered",
    "totalConfirmed": "Total confirmed"
  },
  "ru": {
    "title": "Общая статистика",
    "newConfirmed": "Новые случаи",
    "totalDeaths": "Всего смертей",
    "totalRecovered": "Всего выздоровело",
    "totalConfirmed": "Всего заразившихся"
  }
}
</i18n>
<template>
  <div class="total">
    <div class="total__title">{{ $t('title') }}</div>
    <div class="total__wrap">
      <div class="total__item">
        {{ $t('newConfirmed') }}:
        <b class="total__item-val pl-1">{{ data.NewConfirmed }}</b>
      </div>
      <div class="total__item">
        {{ $t('totalDeaths') }}:
        <b class="total__item-val pl-1">{{ data.TotalDeaths }}</b>
      </div>
      <div class="total__item">
        {{ $t('totalRecovered') }}:
        <b class="total__item-val pl-1">{{ data.TotalRecovered }}</b>
      </div>
      <div class="total__item">
        {{ $t('totalConfirmed') }}:
        <b class="total__item-val pl-1">{{ data.TotalConfirmed }}</b>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "TotalPanel",
  props: {
    data: Object
  }
};
</script>
<style lang="scss">
@import "../../scss/constants";

.total {
  width: 100%;

  &__title {
    margin-bottom: 0.2em;
    font-size: 0.95em;
  }

  &__wrap {
    display: inline-flex;
    justify-content: center;
    flex-wrap: wrap;
    margin: 0 auto 56px;
    padding: 16px 18px;
    width: 100%;
    border: 2px solid $color-dark;
    border-radius: 4px;

    @media (--max-phone) {
      flex-direction: column;
    }
  }

  &__item {
    display: flex;
    justify-content: space-between;
    margin: 0 14px 0 0;

    &:last-child {
      margin-right: 0;
    }

    @media (--max-laptop) {
      flex-basis: 45%;
      margin: 0;
      padding: 0 10px;
    }

    @media (--max-middle) {
      flex-basis: 100%;
    }
  }

  &__item-val {
    font-size: 1.15em;
    line-height: 1.4;
    letter-spacing: 0.05em;
  }
}
</style>
