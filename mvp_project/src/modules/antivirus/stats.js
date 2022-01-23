import Vue from 'vue';
import Antivirus from './Antivirus.vue';
import { TablePlugin } from 'bootstrap-vue';
Vue.use(TablePlugin);

import VueI18n from 'vue-i18n';
Vue.use(VueI18n);

new Vue({
    i18n: new VueI18n({
        locale: document.documentElement.lang
    }),
    render: h => h(Antivirus),
}).$mount('#antivirus');
