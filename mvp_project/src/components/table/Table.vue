<i18n>
{
  "en": {
    "date": "Date",
    "confirmed": "Confirmed"
  },
  "ru": {
    "date": "Дата",
    "confirmed": "Всего случаев"
  }
}
</i18n>
<template>
  <div>
    <b-table
      id="total-table"
      striped
      :items="collection"
      :fields="fields"
      :per-page="perPage"
      :current-page="currentPage"
    ></b-table>
    <b-pagination
      class="mb-0"
      v-model="currentPage"
      :total-rows="length"
      :per-page="perPage"
      aria-controls="total-table"
      align="center"
    ></b-pagination>
  </div>
</template>

<script>
import { BPagination } from "bootstrap-vue";
export default {
  components: {
    BPagination
  },
  props: {
    collection: Array,
    length: Number
  },
  data() {
    return {
      perPage: 12,
      currentPage: 1,
      fields: [
        {
          key: "date",
          label: this.$t("date"),
          thStyle: "width: 50%;",
          tdStyle: "width: 50%;"
        },
        {
          key: "cases",
          label: this.$t("confirmed"),
          thClass: "text-left",
          tdClass: "text-left"
        }
      ]
    };
  }
};
</script>
<style lang="scss">
.table {
  margin-bottom: 10px;
}
</style>
