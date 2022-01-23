<i18n>
{
  "en": {
    "symptoms": {
      "list": [
        "fever",
        "tiredness",
        "dry cough",
        "shortness of breath",
        "aches and pains",
        "sore throat",
        "very few people will report diarrhoea, nausea or a runny nose"
      ],
      "title": "WHO COVID-19 symptoms"
    },
    "advices": {
      "list": [
        "Wash your hands frequently",
        "Maintain social distancing",
        "Avoid touching eyes, nose and mouth",
        "Practice respiratory hygiene",
        "If you have fever, cough and difficulty breathing, seek medical care early",
        "Stay informed and follow advice given by your healthcare provider"
      ],
      "title": "WHO COVID-19 advices"
    }
  },
  "ru": {
    "symptoms": {
      "list": [
        "высокая температура",
        "усталость",
        "сухой кашель",
        "одышка",
        "ломота и боль",
        "больное горло",
        "очень немногие сообщают о диарее, тошноте или насморке"
      ],
      "title": "Общие симптомы"
    },
    "advices": {
      "list": [
        "Мойте руки как можно чаще при помощи мыла и воды (продолжительность &gt; 40 сек) или спиртосодержащих средств (содержание спирта &gt; 60%)",
        "Соблюдайте социальную дистанцию 1,5 метра и больше",
        "Избегайте прикасаться к глазам, носу и рту",
        "Если у Вас повышенная температура, кашель и признаки затрудненного дыхания, обращайтесь за медицинской помощью как можно скорее",
        "Следуйте правилам респираторной гигиены (закрывайте рот и нос во время чихания или кашля салфетками или тканью, после чего сразу избавляйтесь от них)",
        "Продолжайте получать информацию и следовать указаниям медицинских служб."
      ],
      "title": "Советы ВОЗ по COVID-19"
    }
  }
}
</i18n>
<template>
  <div class="mb-5 d-flex justify-content-start flex-wrap flex-md-nowrap">
    <ULBlock
      class="mb-5 p-0 mx-2"
      style="flex-basis: 670px;"
      :list="$t('symptoms.list')"
      :title="$t('symptoms.title')"
    >
      <SVGMask class="ulblock__icon" />
    </ULBlock>
    <ULBlock :list="$t('advices.list')" :title="$t('advices.title')" class="p-0 mx-2">
      <SVGAdvice class="ulblock__icon" />
    </ULBlock>
  </div>
</template>

<script>
import ULBlock from "../../components/other/ULBlock.vue";
import SVGAdvice from "../../components/icons/SVGAdvice.vue";
import SVGMask from "../../components/icons/SVGMask.vue";

export default {
  components: {
    ULBlock,
    SVGAdvice,
    SVGMask
  },
  name: "Info"
};
</script>
