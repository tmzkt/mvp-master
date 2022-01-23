<template>
  <div class="review can-animate">
    <div class="review__title">Наши клиенты о нас </div>
    <div class="review__wrap">
      <Carousel
        :perPage="1"
        paginationActiveColor="#ffffff"
        paginationColor="#0f639b"
        :paginationPadding="10"
        :paginationSize="12"
      >
        <Slide>
          <Review
            authorName="Иван Иванов, создатель «‎Хеленг Инк»"
            authorUrl="https://i.pravatar.cc/160?img=11"
            text="Longevity InTime обещает создать в ближайшее время сервис для отслеживания параметров здоровья, который сможет фиксировать заболевание на самой ранней стадии"
          />
        </Slide>
        <Slide>
          <Review
            authorName="Александр Нечаев, основатель «Нового времени»"
            authorUrl="https://i.pravatar.cc/160?img=14"
            text="Отличный сервис. Решил свои проблемы, стал сильнее и энергичнее"
          />
        </Slide>
        <Slide>
          <Review
            authorName="Максим Сотников, директор центра современной диагностики «Наша загадочная жизнь»"
            authorUrl="https://i.pravatar.cc/160?img=18"
            text="Longevity InTime обещает создать в ближайшее время сервис для отслеживания параметров здоровья, который сможет фиксировать заболевание на самой ранней стадии"
          />
        </Slide>
      </Carousel>
    </div>
  </div>
</template>
<script>
import Review from "./Review.vue";
import { Carousel, Slide } from "vue-carousel";
export default {
  components: {
    Review,
    Carousel,
    Slide
  }
};
</script>
<style src="./review.scss" lang="scss"></style>
