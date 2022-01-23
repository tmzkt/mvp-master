import Vue from 'vue';
import VueCarousel from 'vue-carousel';
import Reviews from './Reviews.vue';

Vue.use(VueCarousel);

new Vue({
    render: h => h(Reviews),
}).$mount('#reviews');
