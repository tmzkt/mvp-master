<i18n>
    {
        "en": {
            "Country": "Country",
            "Confirmed": "Confirmed"
        },
        "ru": {
            "Country": "Страна",
            "Confirmed": "Всего случаев"
        }
    }
</i18n>
<template>
  <div
    :class="loaded ?
      'stats text-secondary mx-lg-5 px-lg-5 mt-5'
      : 'spinner-grow mx-auto d-flex'"
  >
    <div class="stats__inner" v-if="loaded">
      <Info />

      <TotalPanel :data="total" />

      <div class="d-flex align-items-start flex-wrap">
        <div class="col-12 d-md-none mb-4">
          <select id="country" class="custom-select" @change="onSelectCountry">
            <option
              v-for="country in countries"
              :key="country.slug"
              :value="country.slug"
              :selected="country.slug === currentCountry"
              class="d-flex justify-between"
            >
              <span>{{ country.name }}</span>
              <span>({{ separateNumber(country.total) }})</span>
            </option>
          </select>
        </div>

        <div class="stats__holder">
          <div class="stats__left d-none d-md-flex mt-4">
            <b-table
              id="country-table"
              ref="country-table"
              striped
              hover
              :items="countries"
              :fields="fields"
              :per-page="perPage"
              :current-page="currentPage"
              @row-selected="onRowSelected"
              selectMode="single"
              selectable
              selected-variant="primary"
            ></b-table>

            <b-pagination
              class="mb-0"
              v-model="currentPage"
              :total-rows="countries.length"
              :per-page="perPage"
              aria-controls="country-table"
              align="center"
            ></b-pagination>
          </div>

          <div class="stats__right">
            <div
              :class="{ 'spinner-border mx-auto d-flex mt-5': fetched }"
            >
              <DataCharts v-if="!fetched" class="mb-5" :collection="datacollection" />

              <div class="stats__table" v-if="!fetched">
                <Table :length="tableCollection.length" :collection="tableCollection" />
              </div>
            </div>
          </div>
        </div>

        <div class="stats__holder">
          <iframe
            src="https://ourworldindata.org/grapher/total-cases-covid-19?tab=map"
            style="width: 100%; height: 600px; border: 0px none;"
          ></iframe>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import firebase from "firebase/app";
import "firebase/database";
const config = require("./firebaseConfig");

firebase.initializeApp(config);

const rootKey = "antivirus";
const database = firebase.database();
const antivirusRef = database.ref(rootKey);
const getSnapshotChild = (snapshot) => (key) => snapshot.child(key).val();

import { BPagination } from "bootstrap-vue";

import DataCharts from "../../components/charts/Chart.vue";
import Table from "../../components/table/Table.vue";
import TotalPanel from "../../components/other/TotalPanel.vue";
import Info from "./Info.vue";

export default {
  components: {
    TotalPanel,
    DataCharts,
    Table,
    Info,
    BPagination,
  },
  data() {
    return {
      perPage: 21,
      currentPage: 1,
      fields: [
        {
          key: "name",
          label: this.$t("Country"),
        },
        {
          key: "total",
          label: this.$t("Confirmed"),
        },
      ],
      datacollection: null,
      loaded: false,
      fetched: false,
      prepared: false,
      countries: "",
      countryCodes: {},
      currentCountry: null,
      userCountryCode: 'US',
      total: null,
      tableCollection: null,
      symptoms: null,
      advices: null,
      selected: null,
    }
  },
  // watch: {
  //   loaded: function (newVal) {
  //     if (newVal) {
  //       this.$nextTick(() => {
  //         const currentCountry = this.countries.find(
  //           (country) => country.countryCode === this.userCountryCode
  //         );

  //         const currentRow = this.countries.indexOf(currentCountry);
  //         this.$refs["country-table"].selectRow(currentRow);
  //       });
  //     }
  //   },
  // },
  methods: {
    detectCurrentCountry() {
      return axios
        .get(
          "http://api.ipstack.com/check?access_key=10590c59bafa7b75944a71ce589cd36d"
        )
        .then((res) => res.data)
        .then((data) => {
          this.userCountryCode = data.country_code
        })
        .catch(e => {})
    },
    onRowSelected(items) {
      this.selected = items;
      this.currentCountry = items[0].slug;
      this.fetchDataByCountry(this.currentCountry);
    },
    onSelectCountry(e) {
      this.currentCountry = e.target.value;
      this.fetchDataByCountry(this.currentCountry);
    },
    fetchContent() {
      const api = "https://us-central1-message-dev.cloudfunctions.net/api/v1";
      const requestSymptoms = axios.get(`${api}/symptoms`);
      const requestAdvices = axios.get(`${api}/advices`);

      axios
        .all([requestSymptoms, requestAdvices])
        .then(
          axios.spread((...responses) => {
            const responseSymptoms = responses[0];
            const responseAdvices = responses[1];
            this.symptoms = responseSymptoms.data.ru;
            this.advices = responseAdvices.data.ru;
            this.prepared = true;
          })
        )
        .catch((errors) => {
          console.error(errors);
        });
    },
    fetchInitData() {
      antivirusRef.once("value").then((snapshot) => {
        const snapshotByKey = getSnapshotChild(snapshot);
        const topSlugs = snapshotByKey(`topSlugs`);
        const lastModified = snapshotByKey(`lastModified`);
        const total = snapshotByKey(`summary`).Global;
        const countries = snapshotByKey(`summary`).Countries;

        for (const country of countries) {
          this.countryCodes[country.Slug] = country.CountryCode;
        }

        for (const key in total) {
          if (total.hasOwnProperty(key)) {
            total[key] = this.separateNumber(total[key]);
          }
        }

        this.total = total;

        const currentCountry = countries.find(
          (country) => country.CountryCode === this.userCountryCode
        );

        this.currentCountry = currentCountry.Slug;

        this.countries = countries
          .sort((a, b) => b.TotalConfirmed - a.TotalConfirmed)
          .map((country) => ({
            name: country.Country,
            slug: country.Slug,
            total: this.separateNumber(country.TotalConfirmed),
            countryCode: country.CountryCode,
          }));

        this.fetchDataByCountry(this.currentCountry)
          .then(data => {
            if (!data) {
              this.currentCountry = 'united-states'
              this.fetchDataByCountry(this.currentCountry);
            }

            this.fetchContent();
          });

        const obj = {
          loaded: this.loaded,
        };
        console.info(
          "%c%s",
          "color: orange; font-weight: bold;",
          "Last update",
          lastModified
        );
      });
    },
    formatDate(date) {
      const modifiedDate = new Date(date);
      const dd = modifiedDate.getDate();
      const mm = modifiedDate.getMonth() + 1;
      const yyyy = modifiedDate.getFullYear();

      return `${dd}/${mm}/${yyyy}`;
    },
    setDatacollection(data) {
      const dates = data.map((item) => item.Date).map(this.formatDate);
      const cases = data.map((item) => item.Cases);
      const tableCollection = data.reverse().map((item) => ({
        date: this.formatDate(item.Date),
        cases: this.separateNumber(item.Cases),
      }));

      this.tableCollection = tableCollection;
      this.datacollection = {
        labels: dates,
        datasets: [
          {
            label: data[0].Country,
            backgroundColor: "#007bff",
            data: cases,
          },
        ],
      };

      this.loaded = true;
    },
    fetchDataByCountry(geo) {
      this.fetched = true;
      return antivirusRef.once("value")
        .then((snapshot) => {
          const snapshotByKey = getSnapshotChild(snapshot);
          const data = snapshotByKey(`total/country/${geo}/status/confirmed`);
          this.setDatacollection(data);
          this.fetched = false;

          return data
        })
        .catch(error => {
          console.warn(error)
          return false
        })
    },
    separateNumber(value) {
      return value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
    },
  },

  mounted() {
    // this.detectCurrentCountry()
    //   .then(() => this.fetchInitData())
    //   .catch((e) => console.warn(e.message));

    this.fetchInitData()
  }
}
</script>

<style lang="scss">
@import "../../scss/constants.scss";
@import "../../scss/mixins.scss";

.stats {
  $-color: #007bff;

  margin: 0 auto;

  @media (--max-phone) {
    padding: 10px;
  }

  &__holder {
    display: flex;
    width: 100%;
    margin-bottom: 44px;
    position: relative;
  }

  &__left {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    margin-right: 32px;
    min-width: 50%;

    @media (--max-middle) {
      min-width: auto;
    }
  }

  &__right {
    width: 100%;
  }
}
</style>
